"""AI economy layer: retrieval-first answering, caches, usage tracking.

Decision hierarchy (cheapest first, LLM last):
  LEVEL 0 — structured MongoDB lookup (no AI at all)
  LEVEL 1 — cached/local semantic retrieval (embeddings + Qdrant, keyword fallback)
  LEVEL 2 — cheap LLM (classification/extraction only)
  LEVEL 3 — strong LLM (reasoning/synthesis/generation)

Reuses agent_tools getters, rag_query retrieval, and the audit log.
No parallel chat/lead/RAG/email systems are created here.
"""
import hashlib
import logging
import re
import time

log = logging.getLogger("rajiblabs")

# USD per 1M tokens (input, output). Documented estimates for the models we
# actually configure; unknown models fall back to DEFAULT_RATE.
PRICE_PER_1M = {
    "gpt-5-nano": (0.05, 0.40),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4o": (2.50, 10.00),
    "deepseek-chat": (0.14, 0.28),
    "text-embedding-3-small": (0.02, 0.0),
}
DEFAULT_RATE = (0.10, 0.40)


def estimate_tokens(text: str) -> int:
    """Chars/4 heuristic, documented as estimate (real usage preferred)."""
    return max(1, len(text or "") // 4)


def text_hash(text: str) -> str:
    return hashlib.sha256((text or "").encode()).hexdigest()


def normalize_question(q: str) -> str:
    q = (q or "").strip().lower()
    q = re.sub(r"\s+", " ", q)
    return q[:500]


def question_hash(q: str, extra: str = "") -> str:
    return text_hash(normalize_question(q) + "|" + (extra or ""))


async def record_usage(db, *, provider: str, model: str, tag: str,
                       reason: str, in_text: str = "", out_text: str = "",
                       latency_ms: int = 0, usage_obj: dict | None = None,
                       cache_hit: bool = False,
                       retrieval_hit: bool | None = None,
                       fallback_reason: str | None = None,
                       response_type: str | None = None) -> None:
    """Measurable every LLM/embedding call. Never raises, never logs secrets.
    response_type: RAG_ONLY | STRUCTURED_LOOKUP | CACHE | LLM_FALLBACK | LLM_SYNTHESIS"""
    try:
        usage_obj = usage_obj or {}
        in_tok = int(usage_obj.get("prompt_tokens") or 0) or estimate_tokens(in_text)
        out_tok = int(usage_obj.get("completion_tokens") or 0) or estimate_tokens(out_text)
        rate_in, rate_out = PRICE_PER_1M.get(model, DEFAULT_RATE)
        cost = in_tok / 1_000_000 * rate_in + out_tok / 1_000_000 * rate_out
        from app.database import utcnow
        await db["ai_usage"].insert_one({
            "provider": provider, "model": model, "tag": tag, "reason": reason,
            "in_tokens": in_tok, "out_tokens": out_tok,
            "est_cost_usd": round(cost, 6), "latency_ms": int(latency_ms),
            "cache_hit": bool(cache_hit),
            "retrieval_hit": retrieval_hit, "fallback_reason": fallback_reason,
            "estimated": not bool(usage_obj),
            "response_type": response_type,
            "created_at": utcnow()})
    except Exception as e:
        log.warning("usage record failed: %s", e)


# ── LEVEL 0: structured answers (no AI) ──────────────────────────────
def _bullets(title: str, items: list[str], max_items: int = 8) -> str:
    lines = [f"{title}:"]
    for it in items[:max_items]:
        lines.append(f"- {it}")
    if len(items) > max_items:
        lines.append(f"- …and {len(items) - max_items} more (see the site).")
    return "\n".join(lines)


_STRUCT_PATTERNS: list[tuple[str, list[str]]] = [
    ("products", [r"\bproducts?\b", r"\bpestflow\b", r"\blexvault\b", r"\bdocu",
                  r"\baria\b", r"\bpricing\b", r"\bdemo\b"]),
    ("projects", [r"\bprojects?\b", r"\bportfolio\b", r"\bcase stud", r"\bbuilt\b"]),
    ("skills", [r"\bskills?\b", r"\btech stack\b", r"\btechnolog\w*\b.*\b(us|know|have|experience)\b"]),
    ("domains", [r"\bdomains?\b", r"\bindustr\w+\b", r"\bsectors?\b"]),
    ("resume", [r"\bresume\b", r"\bcv\b", r"\brésumé\b"]),
    ("contact", [r"\bcontact\b", r"\bemail\b", r"\bphone\b", r"\bwhatsapp\b",
                 r"\breach\b", r"\bcall\b.*\brajib\b"]),
    ("live", [r"\blive\b", r"\bonline\b", r"\bwebsite\b.*\b(live|link|url)\b",
               r"\bdemo link\b", r"\bdeployed\b"]),
    ("social_links", [r"\bsocial\b", r"\blinkedin\b", r"\bgithub\b.*\b(profile|link|url)\b",
                      r"\btwitter\b", r"\bsocial media\b"]),
    ("experience", [r"\bexperience\b", r"\bcareer\b", r"\bwork history\b",
                    r"\bemployment\b", r"\bworked at\b", r"\bprevious jobs?\b"]),
    ("certifications", [r"\bcertifi", r"\bcredential", r"\blicense\b"]),
    ("tech_stack", [r"\bwhat tech\b", r"\bwhat technolog", r"\bwhat (is|does).*use",
                    r"\bstack\b", r"\bbuilt with\b", r"\bmade with\b"]),
    ("portfolio_live", [r"\bportfolio.*live\b", r"\blive.*portfolio\b",
                        r"\bportfolio.*site\b", r"\bsites?\b.*\blive\b"]),
]


async def structured_answer(question: str, db) -> dict | None:
    """LEVEL 0: answer list/fact questions straight from MongoDB.

    Returns {answer, sources, confidence, level} or None to fall through.
    Only answers when data is non-empty — never fabricates.
    """
    from app.services import agent_tools as tools
    q = normalize_question(question)
    kind = None
    for name, patterns in _STRUCT_PATTERNS:
        if any(re.search(p, q) for p in patterns):
            kind = name
            break
    if not kind:
        return None
    try:
        if kind == "products":
            items = await tools.get_products(db)
            if not items:
                return None
            lines = [f"{p.get('name')}: {(p.get('description') or '')[:140]}"
                     + (f" ({p.get('live_url')})" if p.get("live_url") else "")
                     for p in items]
            src = [{"title": p.get("name", ""), "url": p.get("live_url"),
                    "source_type": "tool:get_products"} for p in items]
            return {"answer": _bullets(f"RajibLabs products ({len(items)})", lines),
                    "sources": src, "confidence": 0.95, "level": 0, "intent": "PRODUCTS"}
        if kind == "projects":
            items = await tools.get_projects(db)
            if not items:
                return None
            lines = [f"{p.get('name')}: {(p.get('description') or '')[:140]}"
                     for p in items[:10]]
            src = [{"title": p.get("name", ""),
                    "url": p.get("live_url") or p.get("github_url"),
                    "source_type": "tool:get_projects"} for p in items[:10]]
            return {"answer": _bullets(f"Projects by Rajib ({len(items)})", lines, 10),
                    "sources": src, "confidence": 0.95, "level": 0,
                    "intent": "PROJECT_INFORMATION"}
        if kind == "skills":
            cur = db["skills"].find({"status": "published"}).sort("display_order", 1)
            names = [d.get("name", "") async for d in cur if d.get("name")]
            if not names:
                prof = await db["profiles"].find_one() or {}
                names = [s for s in (prof.get("skills") or []) if s]
            if not names:
                return None
            src = [{"title": "Rajib — Technical Skills",
                    "url": "https://rajiblabs.com/#about", "source_type": "profile"}]
            return {"answer": "Rajib's skills:\n- " + "\n- ".join(names[:30]),
                    "sources": src, "confidence": 0.95, "level": 0,
                    "intent": "TECHNICAL_EXPERIENCE"}
        if kind == "domains":
            cur = db["professional_domains"].find(
                {"status": "active"}).sort("confidence_score", -1)
            names = [d.get("name", "") async for d in cur if d.get("name")]
            if not names:
                return None
            src = [{"title": n, "url": None, "source_type": "domain"} for n in names]
            return {"answer": "Domains Rajib has worked in:\n- " + "\n- ".join(names),
                    "sources": src, "confidence": 0.9, "level": 0,
                    "intent": "ABOUT_RAJIB"}
        if kind == "resume":
            d = await db["resumes"].find_one({"active": True}, sort=[("version", -1)])
            if not d:
                return None
            src = [{"title": "Rajib Mahata — Resume (public)",
                    "url": "https://rajiblabs.com/#about", "source_type": "resume"}]
            return {"answer": ("The current published resume is version "
                               f"{d.get('version', 1)} "
                               f"({d.get('filename') or d.get('file_name') or 'PDF'}). "
                               "Download it from the About section."),
                    "sources": src, "confidence": 0.95, "level": 0,
                    "intent": "CAREER_INFORMATION"}
        if kind == "contact":
            c = await tools.get_contact_information(db)
            bits = [x for x in [
                f"Email: {', '.join(c.get('emails', []))}" if c.get("emails") else "",
                f"Phone: {c.get('primary_phone')}" if c.get("primary_phone") else "",
                f"WhatsApp: {c.get('whatsapp')}" if c.get("whatsapp") else "",
            ] if x]
            if not bits:
                return None
            return {"answer": "Reach RajibLabs:\n" + "\n".join(bits),
                    "sources": [], "confidence": 0.95, "level": 0,
                    "intent": "CONTACT"}
        if kind == "live":
            items = await tools.get_projects(db)
            live = [p for p in items if p.get("live_url")]
            if not live:
                return None
            lines = [f"{p.get('name')}: {p.get('live_url')}" for p in live]
            src = [{"title": p.get("name", ""), "url": p.get("live_url"),
                    "source_type": "tool:get_projects"} for p in live]
            return {"answer": _bullets("Live sites", lines),
                    "sources": src, "confidence": 0.95, "level": 0,
                    "intent": "PROJECT_INFORMATION"}
        if kind == "social_links":
            prof = await db["profiles"].find_one() or {}
            links = prof.get("social_links") or {}
            bits = [f"GitHub: {links['github']}" if links.get("github") else "",
                    f"LinkedIn: {links['linkedin']}" if links.get("linkedin") else "",
                    f"Twitter: {links['twitter']}" if links.get("twitter") else ""]
            bits = [b for b in bits if b]
            if not bits:
                return None
            src = [{"title": "Rajib — Social Links", "url": None, "source_type": "profile"}]
            return {"answer": "Rajib's social profiles:\n" + "\n".join(bits),
                    "sources": src, "confidence": 0.95, "level": 0,
                    "intent": "ABOUT_RAJIB"}
        if kind == "experience":
            prof = await db["profiles"].find_one() or {}
            career = prof.get("career") or []
            if not career:
                return None
            lines = [f"{c.get('role','')} at {c.get('company','')} ({c.get('period','')})"
                     for c in career[:5]]
            src = [{"title": "Rajib — Career Experience", "url": None, "source_type": "profile"}]
            return {"answer": "Rajib's experience:\n- " + "\n- ".join(lines),
                    "sources": src, "confidence": 0.95, "level": 0,
                    "intent": "CAREER_INFORMATION"}
        if kind == "certifications":
            cur = db["skills"].find({"status": "published", "category": "Certifications"})
            names = [d.get("name", "") async for d in cur if d.get("name")]
            if not names:
                return None
            src = [{"title": "Rajib — Certifications", "url": None, "source_type": "skills"}]
            return {"answer": "Certifications:\n- " + "\n- ".join(names),
                    "sources": src, "confidence": 0.9, "level": 0,
                    "intent": "TECHNICAL_EXPERIENCE"}
        if kind == "portfolio_live":
            cur = db["portfolio"].find({"status": "published", "live_url": {"$exists": True, "$ne": ""}})
            items = []
            async for p in cur:
                if p.get("live_url"):
                    items.append(p)
            if not items:
                return None
            lines = [f"{p.get('title','')}: {p.get('live_url')}" for p in items[:8]]
            src = [{"title": p.get("title", ""), "url": p.get("live_url"),
                    "source_type": "portfolio"} for p in items[:8]]
            return {"answer": _bullets("Live portfolio sites", lines),
                    "sources": src, "confidence": 0.95, "level": 0,
                    "intent": "PROJECT_INFORMATION"}
    except Exception as e:
        log.warning("structured answer failed: %s", e)
        return None
    return None


# ── LEVEL 1 caches ───────────────────────────────────────────────────
async def embedding_cache_get(db, text: str, provider: str, model: str):
    try:
        from datetime import datetime, timezone
        from app.config import get_settings
        doc = await db["embedding_cache"].find_one(
            {"text_hash": text_hash(text), "provider": provider, "model": model})
        if not doc:
            return None
        ttl = int(get_settings().rag_cache_ttl_seconds or 3600)
        age = (datetime.now(timezone.utc) - doc.get("created_at",
               datetime.now(timezone.utc))).total_seconds()
        if age > ttl:
            return None
        return doc.get("vector")
    except Exception:
        return None


async def embedding_cache_set(db, text: str, provider: str, model: str,
                              vector: list[float]) -> None:
    try:
        from app.database import utcnow
        await db["embedding_cache"].update_one(
            {"text_hash": text_hash(text), "provider": provider, "model": model},
            {"$set": {"vector": vector, "created_at": utcnow(),
                      "dim": len(vector or [])}},
            upsert=True)
    except Exception as e:
        log.warning("embedding cache set failed: %s", e)


async def cached_embed(text: str, db=None):
    """LEVEL 1 embedding with content-hash cache. Returns (vector, cache_hit)."""
    from app.services.rag_embeddings import EmbeddingError, EmbeddingService
    svc = EmbeddingService()
    if db is not None:
        hit = await embedding_cache_get(db, text, svc.provider, svc.model)
        if hit:
            return hit, True
    vec = await svc.generate_embedding(text)
    if db is not None:
        await embedding_cache_set(db, text, svc.provider, svc.model, vec)
    return vec, False


_KB_VERSION_CACHE: tuple[str, float] = ("0", 0.0)  # (version, monotonic_ts)
_KB_VERSION_TTL = 10.0  # seconds — avoid 2 DB roundtrips per cache check


async def kb_version(db) -> str:
    """Single cheap version stamp for the whole knowledge base.

    In-process cache (10s TTL) eliminates redundant DB roundtrips
    when response_cache_get and response_cache_set both need the version."""
    global _KB_VERSION_CACHE
    import time as _t
    now = _t.monotonic()
    cached_ver, cached_ts = _KB_VERSION_CACHE
    if now - cached_ts < _KB_VERSION_TTL:
        return cached_ver
    try:
        d = await db["site_settings"].find_one({"key": "kb_version"})
        ver = str((d or {}).get("value", {}).get("v", "0"))
        _KB_VERSION_CACHE = (ver, now)
        return ver
    except Exception:
        return cached_ver


async def bump_kb_version(db) -> str:
    """Incremented on every knowledge write; response cache keys off it."""
    try:
        from app.database import utcnow
        d = await db["site_settings"].find_one({"key": "kb_version"})
        v = int(((d or {}).get("value", {}) or {}).get("v", 0)) + 1
        await db["site_settings"].update_one(
            {"key": "kb_version"},
            {"$set": {"value": {"v": v}, "updated_at": utcnow()}}, upsert=True)
        return str(v)
    except Exception:
        return "0"


async def response_cache_get(db, question: str, extra: str = ""):
    try:
        from app.config import get_settings
        import time as _t
        doc = await db["response_cache"].find_one(
            {"q_hash": question_hash(question, extra)})
        if not doc:
            return None
        ttl = 3600
        try:
            ttl = int(get_settings().response_cache_ttl_seconds or 3600)
        except Exception:
            pass
        if _t.time() - float(doc.get("created_ts", 0)) > ttl:
            return None
        if str(doc.get("kb_version", "0")) != await kb_version(db):
            return None  # knowledge changed → stale
        return doc
    except Exception:
        return None


async def response_cache_set(db, question: str, answer: dict, extra: str = "") -> None:
    try:
        import time as _t
        await db["response_cache"].update_one(
            {"q_hash": question_hash(question, extra)},
            {"$set": {"answer": answer.get("answer", ""),
                      "sources": answer.get("sources", [])[:10],
                      "intent": answer.get("intent", "GENERAL"),
                      "grounded": bool(answer.get("grounded", True)),
                      "kb_version": await kb_version(db),
                      "created_ts": _t.time()}},
            upsert=True)
    except Exception as e:
        log.warning("response cache set failed: %s", e)


async def keyword_search(question: str, db, top_k: int = 5,
                         consumer: str = "public") -> list[dict]:
    """LEVEL 1 fallback when vectors are unavailable: Mongo regex search
    over knowledge chunks (implements retrieve()'s documented promise).

    Enforces the central KB guardrails server-side (same contract as the
    vector path): orphan chunks dropped, disallowed consumers filtered,
    title/url hydrated from the parent document. Fail-closed on error."""
    words = [w for w in re.findall(r"[a-z]{3,}", (question or "").lower())]
    words = [w for w in words if w not in
             ("what", "who", "how", "why", "the", "and", "for", "with", "does")]
    if not words:
        return []
    try:
        ors = [{"content": {"$regex": re.escape(w), "$options": "i"}} for w in words[:6]]
        out = []
        async for c in db["knowledge_chunks"].find({"$or": ors}).limit(top_k * 4):
            text = c.get("content", "") or ""
            low = text.lower()
            score = round(sum(1 for w in words if w in low) / max(1, len(words)), 4)
            if score <= 0:
                continue
            out.append({"chunk_id": str(c.get("_id")),
                        "document_id": str(c.get("document_id", "")),
                        "score": score, "source_type": (c.get("metadata") or {}).get(
                            "source_type", ""),
                        "title": "", "url": None, "content": text[:1500]})
        out.sort(key=lambda h: h["score"], reverse=True)
        out = out[:top_k * 4]
        # Central KB guardrail gate (same as vector path): hydrate parents,
        # enrich title/url, drop orphans + disallowed consumers. Never
        # prompt-gated.
        try:
            from app.services import kb_policy as _kb
            doc_ids: set[str] = {h.get("document_id", "") for h in out if h.get("document_id")}
            docs_by_id: dict = {}
            if doc_ids:
                from bson import ObjectId as _Oid
                oids = []
                for did in doc_ids:
                    try:
                        oids.append(_Oid(did))
                    except Exception:
                        pass
                if oids:
                    async for d in db["knowledge_documents"].find({"_id": {"$in": oids}}):
                        docs_by_id[str(d["_id"])] = d
            # Enrich display fields from the parent document (source of truth
            # for title/url/source_type); chunk metadata is only a fallback.
            for h in out:
                d = docs_by_id.get(h.get("document_id", ""))
                if d:
                    if not h.get("title"):
                        h["title"] = d.get("title", "")
                    if h.get("url") is None:
                        h["url"] = d.get("url")
                    if not h.get("source_type"):
                        h["source_type"] = d.get("source_type", "")
                    if not h.get("repository"):
                        h["repository"] = d.get("repository")
                    if not h.get("language"):
                        h["language"] = d.get("language")
            out = _kb.filter_hits(out, docs_by_id, consumer)
        except Exception as e:
            log.warning("keyword guardrail filter failed (fail-closed): %s", e)
            return []
        out.sort(key=lambda h: h["score"], reverse=True)
        return out[:top_k]
    except Exception as e:
        log.warning("keyword search failed: %s", e)
        return []
