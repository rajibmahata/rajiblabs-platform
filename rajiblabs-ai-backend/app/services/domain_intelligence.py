"""Professional Domain Intelligence — Profile Manager Agent extension.

Implements the spec's pipeline deterministically first, LLM only for
semantic synthesis. No parallel profile/content systems.
"""
import hashlib
import logging
import re
import uuid
from datetime import datetime, timezone
from urllib.parse import urlparse

from app.database import get_db, utcnow
from app.services.notify import audit, log_error

log = logging.getLogger("rajiblabs")

# Known domain hints — ONLY hints, never auto-published without evidence.
# Names exactly as spec examples; slugs derived via _slug().
DOMAIN_HINTS: dict[str, list[str]] = {
    "Agriculture / AgriTech": ["agriculture", "agritech", "agritech", "farm", "crop", "pest management", "pestflow", "field operations", "technician workflow", "agri"],
    "Pest Management / PestFlow": ["pest", "pestflow", "pest control", "technician", "quotation", "assignment", "apcs"],
    "Healthcare / Healthcare Technology": ["healthcare", "health care", "pharmacy", "pharmaceutical", "prescription", "patient", "hospital", "clinic"],
    "Enterprise Software": ["enterprise", "b2b", "business operations", "crm", "erp"],
    "SaaS": ["saas", "multi-tenant", "subscription", "tenancy"],
    "AI / Generative AI": ["ai", "generative", "llm", "gpt", "openai", "rag", "vector", "embedding"],
    "Agentic AI / AI Automation": ["agent", "agentic", "automation", "workflow automation", "multi-agent", "orchestrat"],
    "Cloud Platforms": ["azure", "aws", "cloud", "serverless", "paas"],
    "Financial / Business Systems": ["finance", "financial", "accounting", "billing", "payment", "stripe"],
    "E-commerce": ["ecommerce", "e-commerce", "shop", "cart", "storefront"],
    "Logistics": ["logistics", "fleet", "truck", "delivery", "supply chain"],
    "CRM / Business Operations": ["crm", "business operations", "operations platform"],
    "Workforce / Field Operations": ["workforce", "field operations", "field workforce", "mobile pwa"],
    "Property / Real Estate": ["property", "real estate", "proptech"],
    "Education": ["education", "learning", "course", "edtech", "lms"],
    "Government / Public Sector": ["government", "public sector", "govtech", "civic"],
    "Manufacturing": ["manufacturing", "factory", "production line", "mes"],
}

WEIGHTS = {
    "experience": 30,
    "project": 25,
    "product": 25,
    "portfolio": 20,
    "github_repo": 12,
    "github_readme": 8,
    "website_content": 6,
    "knowledge": 6,
    "linkedin": 10,
    "resume": 15,
    "profile": 10,
}

CONF_LABEL = [
    (90, "Strongly established"), (75, "Established"), (50, "Emerging"),
    (25, "Weak evidence"), (0, "Do not publish"),
]

def _slug(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return re.sub(r"-{2,}", "-", s)[:80] or uuid.uuid4().hex[:8]

def _hash(*parts: str) -> str:
    return hashlib.sha256("|".join(p or "" for p in parts).encode()).hexdigest()[:16]

def _sanitize(text: str) -> str:
    for pat in [r"sk-[A-Za-z0-9]{10,}", r"ghp_[A-Za-z0-9]{10,}", r"Bearer\s+\S+"]:
        text = re.sub(pat, "***", text, flags=re.I)
    return text[:8000]

def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())

async def _collect_sources(db) -> list[dict]:
    """Collect normalized text blobs with provenance. No secrets."""
    out = []
    # profile
    prof = await db["profiles"].find_one() or {}
    if prof.get("full_name"):
        out.append({"type": "profile", "id": str(prof.get("_id")), "text": f"{prof.get('full_name')} {prof.get('title','')} {prof.get('bio','')} {' '.join(prof.get('skills',[]))}", "meta": prof})
    for c in prof.get("career", []) or []:
        txt = f"{c.get('company','')} {c.get('role','')} {c.get('period','')} {' '.join(c.get('achievements',[]))} {' '.join(c.get('tech_stack',[]))}"
        out.append({"type": "experience", "id": c.get("company",""), "text": txt, "meta": c})
    # resume
    cur = db["resumes"].find({"active": True}).sort("version", -1).limit(1)
    docs = [d async for d in cur]
    if docs and docs[0].get("extracted_text"):
        out.append({"type": "resume", "id": str(docs[0]["_id"]), "text": docs[0]["extracted_text"][:6000], "meta": docs[0]})
    # projects (verified)
    async for p in db["projects"].find({"published": True}):
        txt = f"{p.get('name','')} {p.get('short_description','')} {p.get('full_description','')} {' '.join(p.get('technologies',[]))}"
        out.append({"type": "project", "id": str(p["_id"]), "text": txt, "meta": p, "slug": p.get("slug")})
    # portfolio
    async for p in db["portfolio"].find({"status": "published"}):
        txt = f"{p.get('title','')} {p.get('short_description','')} {p.get('description','')} {' '.join(p.get('tech_stack',[]))} {p.get('purpose','')} {p.get('problem','')}"
        out.append({"type": "portfolio", "id": str(p["_id"]), "text": txt, "meta": p, "slug": p.get("slug"), "url": p.get("live_url") or p.get("github_url")})
    # products
    async for p in db["products"].find({"status": {"$in": ["published","featured"]}}):
        txt = f"{p.get('name','')} {p.get('description','')} {' '.join(p.get('tech_stack',[]))}"
        out.append({"type": "product", "id": str(p["_id"]), "text": txt, "meta": p, "slug": p.get("slug")})
    # github repos
    async for r in db["github_repositories"].find({"is_private": {"$ne": True}}):
        txt = f"{r.get('name','')} {r.get('description','')} {' '.join(r.get('topics',[]))} {r.get('language','')} {r.get('readme','')[:2000]}"
        out.append({"type": "github_repo", "id": r.get("full_name",""), "text": txt, "meta": r})
    # website content
    async for w in db["homepage_content"].find({}):
        txt = f"{w.get('title','')} {w.get('subtitle','')} {str(w.get('body',{}))[:1000]}"
        out.append({"type": "website_content", "id": w.get("section_key",""), "text": txt, "meta": w})
    async for w in db["website_contents"].find({}):
        out.append({"type": "website_content", "id": w.get("key",""), "text": str(w.get("body_json",""))[:1000], "meta": w})
    # knowledge docs (active)
    async for k in db["knowledge_documents"].find({"status": "active"}).limit(50):
        out.append({"type": "knowledge", "id": str(k["_id"]), "text": k.get("content","")[:800], "meta": k})
    # linkedin source (if configured and enabled)
    src = await db["professional_sources"].find_one({"type": "linkedin", "enabled": True})
    if src and src.get("public_source"):
        # stored manual import field: linkedin_text (admin-approved)
        if src.get("linkedin_text"):
            out.append({"type": "linkedin", "id": "linkedin", "text": src["linkedin_text"][:6000], "meta": src})
    # fallback: if no linkedin_text but URL present, do not scrape — keep placeholder for future integration
    return [s for s in out if s["text"].strip()]

def _discover_domains(sources: list[dict]) -> dict[str, list[dict]]:
    """Keyword clustering: domain -> evidence sources."""
    buckets: dict[str, list[dict]] = {}
    for src in sources:
        norm = _normalize(src["text"])
        for domain, keywords in DOMAIN_HINTS.items():
            hits = sum(1 for kw in keywords if kw.lower() in norm)
            if hits:
                buckets.setdefault(domain, []).append({**src, "hits": hits})
    # Also capture unmapped strong signals as generic? Spec says don't invent without evidence — skip.
    return buckets

def _confidence(evidence: list[dict]) -> tuple[int, list[str]]:
    """Weighted sum, capped 100, with evidence breakdown."""
    score = 0
    by_type: dict[str, int] = {}
    for e in evidence:
        w = WEIGHTS.get(e["type"], 5)
        by_type[e["type"]] = by_type.get(e["type"], 0) + 1
        # hits multiplier for keyword density, capped
        mult = min(1 + (e.get("hits",1)-1)*0.3, 2.0)
        score += int(w * mult)
    score = min(100, score)
    reasons = [f"{k}:{v}" for k,v in by_type.items()]
    return score, reasons

def _label(score: int) -> str:
    for thr, label in CONF_LABEL:
        if score >= thr:
            return label
    return "Do not publish"

async def _validate_and_generate(domain: str, evidence: list[dict], existing: dict | None) -> dict | None:
    """Deterministic description generation; LLM only for prose, never for facts."""
    # Collect project/portfolio/github links for this domain
    projects = [e["slug"] for e in evidence if e["type"] in ("project","portfolio") and e.get("slug")]
    products = [e["slug"] for e in evidence if e["type"] == "product" and e.get("slug")]
    repos = [e["id"] for e in evidence if e["type"] == "github_repo"]
    # Gather techs
    techs = set()
    for e in evidence:
        for t in (e["meta"].get("technologies") or e["meta"].get("tech_stack") or []):
            techs.add(t)
        if e["meta"].get("language"):
            techs.add(e["meta"]["language"])
    techs = sorted(techs)[:12]
    # If existing description is fresh and evidence unchanged, skip LLM
    # Hash of evidence ids to detect change
    ev_hash = _hash(domain, *sorted([e["type"]+e["id"] for e in evidence]))
    if existing and existing.get("evidence_hash") == ev_hash and existing.get("detailed_description"):
        return None  # no regen needed
    # Build evidence snippets (no secrets)
    snippets = "\n".join([f"- {e['type']}: {(e['text'][:200]).replace(chr(10),' ')}" for e in evidence[:6]])
    # LLM synthesis (cheap, evidence-only)
    short_desc = f"Domain where Rajib has delivered {domain.lower()} solutions."
    detailed = snippets[:800]  # fallback deterministic
    try:
        from app.services.lead_ai import AIService
        from app.config import get_settings
        s = get_settings()
        if s.openai_api_key:
            svc = AIService()
            if svc.configured:
                ctx = _sanitize(f"Domain: {domain}\nEvidence:\n{snippets}\nTechnologies: {', '.join(techs)}")
                out = await svc._complete(
                    [{"role":"system","content":"You are a factual domain summarizer. Using ONLY the evidence, write a 2-sentence short_description and a 60-80 word detailed_description. List business_problems (2 bullets), solutions_delivered (2 bullets), capabilities (3). Return JSON with keys: short_description, detailed_description, business_problems[], solutions_delivered[], capabilities[]. Do not invent clients, metrics, or URLs."},
                     {"role":"user","content": ctx[:3500]}],
                    max_tokens=700, temperature=0.3, tag="domain-desc")
                data = out.get("data", {})
                if data.get("short_description"):
                    short_desc = str(data["short_description"])[:300]
                if data.get("detailed_description"):
                    detailed = str(data["detailed_description"])[:600]
                # keep optional arrays if LLM returned them
                # we store them below via data
                # return full data for merge
                return {"short_description": short_desc, "detailed_description": detailed,
                        "_raw": data, "_ev_hash": ev_hash}
    except Exception as e:
        log.warning("domain LLM failed %s: %s", domain, e)
    return {"short_description": short_desc, "detailed_description": detailed, "_ev_hash": ev_hash}

async def _upsert_domain(db, name: str, evidence: list[dict], threshold: int) -> dict:
    slug = _slug(name)
    score, reasons = _confidence(evidence)
    label = _label(score)
    status = "active" if score >= threshold else "inactive"
    existing = await db["professional_domains"].find_one({"slug": slug})
    # projects/products/portfolio linkage
    projects = list({e["slug"] for e in evidence if e["type"] in ("project","portfolio") and e.get("slug")})
    products = list({e["slug"] for e in evidence if e["type"] == "product" and e.get("slug")})
    portfolio_items = list({e["slug"] for e in evidence if e["type"] == "portfolio" and e.get("slug")})
    github_repos = list({e["id"] for e in evidence if e["type"] == "github_repo"})
    # experience evidence
    exp_ev = [e["meta"].get("company","") for e in evidence if e["type"] == "experience"]
    techs = set()
    for e in evidence:
        for t in (e["meta"].get("technologies") or e["meta"].get("tech_stack") or []):
            techs.add(t)
        if e.get("meta",{}).get("language"):
            techs.add(e["meta"]["language"])
    techs = sorted(techs)[:20]
    # source ids
    source_ids = [f"{e['type']}:{e['id']}" for e in evidence]
    # duplicate merging: if existing slug differs but name similar? Use slug as key; merge via evidence union — already handled by grouping
    # LLM draft
    draft = await _validate_and_generate(name, evidence, existing)
    # Build doc
    now = utcnow()
    base = {
        "name": name, "slug": slug,
        "short_description": (draft.get("short_description") if draft else (existing.get("short_description") if existing else "")),
        "detailed_description": (draft.get("detailed_description") if draft else (existing.get("detailed_description") if existing else "")),
        "business_problems": (draft.get("_raw",{}).get("business_problems") if draft and draft.get("_raw") else (existing.get("business_problems") if existing else [])) or [],
        "solutions_delivered": (draft.get("_raw",{}).get("solutions_delivered") if draft and draft.get("_raw") else (existing.get("solutions_delivered") if existing else [])) or [],
        "capabilities": (draft.get("_raw",{}).get("capabilities") if draft and draft.get("_raw") else (existing.get("capabilities") if existing else [])) or [],
        "technologies": techs,
        "projects": projects,
        "products": products,
        "portfolio_items": portfolio_items,
        "github_repositories": github_repos,
        "experience_evidence": exp_ev[:5],
        "confidence_score": score,
        "confidence_label": label,
        "evidence_count": len(evidence),
        "evidence_reasons": reasons,
        "source_ids": source_ids,
        "evidence_hash": draft.get("_ev_hash") if draft else (existing.get("evidence_hash") if existing else _hash(name, *source_ids)),
        "status": status,
        "featured": existing.get("featured", False) if existing else False,
        "display_order": existing.get("display_order", 0) if existing else 0,
        "seo": existing.get("seo", {"title": "", "description": "", "keywords": []}) if existing else {"title": "", "description": "", "keywords": []},
        "updated_at": now,
        "last_verified_at": now,
    }
    # preserve featured/display_order/seo if existing
    if existing:
        base["created_at"] = existing.get("created_at", now)
        base["featured"] = existing.get("featured", False)
        base["display_order"] = existing.get("display_order", 0)
        base["seo"] = existing.get("seo", base["seo"])
        # validation: never silently lower confidence without audit — but do update score
        base["previous_confidence"] = existing.get("confidence_score")
    else:
        base["created_at"] = now
        base["previous_confidence"] = None
    # Upsert
    await db["professional_domains"].update_one({"slug": slug}, {"$set": base}, upsert=True)
    doc = await db["professional_domains"].find_one({"slug": slug})
    # RAG indexing (only active)
    if status == "active":
        try:
            from app.services import rag_ingest
            content = f"{name}\n{base['short_description']}\n{base['detailed_description']}\nProblems: {', '.join(base['business_problems'])}\nSolutions: {', '.join(base['solutions_delivered'])}\nCapabilities: {', '.join(base['capabilities'])}\nTechnologies: {', '.join(techs)}\nProjects: {', '.join(projects)}"
            await rag_ingest.upsert_document(
                "service", f"domain:{slug}", name, content,
                url=f"https://rajiblabs.com/domains/{slug}",
                tags=["domain", slug],
            )
        except Exception as e:
            log.warning("domain RAG failed %s: %s", slug, e)
    else:
        # deactivate RAG if previously active and now below threshold
        try:
            from app.services import rag_ingest
            kd = await db["knowledge_documents"].find_one({"source_type": "service", "source_id": f"domain:{slug}"})
            if kd:
                await rag_ingest.deactivate_document(str(kd["_id"]))
        except Exception:
            pass
    return doc

async def ensure_linkedin_source(db) -> dict:
    """Seed professional_sources with LinkedIn entry; never invent URL."""
    doc = await db["professional_sources"].find_one({"type": "linkedin"})
    if doc:
        return doc
    # Use site.ts linkedin as default but mark as needs verification
    from app.config import get_settings
    # Try to read frontend config fallback? Keep generic.
    doc = {
        "type": "linkedin",
        "name": "LinkedIn",
        "url": "https://www.linkedin.com/in/rajib-mahata",
        "enabled": False,
        "public_source": True,
        "status": "pending_verification",
        "last_checked_at": None,
        "last_success_at": None,
        "linkedin_text": "",
        "created_at": utcnow(),
        "updated_at": utcnow(),
    }
    await db["professional_sources"].insert_one(doc)
    return doc

async def validate_portfolio_urls(db) -> list[dict]:
    """Check live portfolio URLs (Rajib-owned only, no aggressive crawl).
    Parallel HEAD requests for low latency."""
    import httpx
    import asyncio
    results = []
    seen = set()
    urls_to_check = []
    for coll in ("portfolio", "projects"):
        filt = {"status": "published"} if coll == "portfolio" else {"published": True}
        async for doc in db[coll].find(filt):
            for field in ("live_url", "liveUrl", "live_url"):
                url = doc.get("live_url") or doc.get("liveUrl")
                if url and url not in seen:
                    seen.add(url)
                    urls_to_check.append((url, doc))

    async def _check_url(url, doc):
        try:
            async with httpx.AsyncClient(timeout=8, follow_redirects=True) as client:
                r = await client.head(url, headers={"User-Agent": "RajibLabsBot/1.0"})
                return {"url": url, "slug": doc.get("slug"), "status": r.status_code,
                        "ok": r.status_code < 400, "checked_at": utcnow()}
        except Exception as e:
            try:
                await db["portfolio"].update_one(
                    {"_id": doc["_id"]},
                    {"$set": {"verification_status": "broken", "last_checked": utcnow(),
                              "health_status": "unreachable"}})
            except Exception:
                pass
            return {"url": url, "slug": doc.get("slug"), "status": 0, "ok": False,
                    "error": str(e)[:200], "checked_at": utcnow()}

    if urls_to_check:
        results = await asyncio.gather(*[_check_url(u, d) for u, d in urls_to_check])
    # persist health summary for admin
    try:
        await db["professional_sources"].update_one({"type": "portfolio_health"}, {"$set": {"health": results, "updated_at": utcnow()}}, upsert=True)
    except Exception:
        pass
    return results

async def run_domain_discovery(triggered_by: str = "scheduler") -> dict:
    """Full pipeline: sources -> domains -> DB -> RAG. Token-efficient."""
    db = get_db()
    from app.services import agent_config
    cfg = await agent_config.get_agent(db, agent_config.PROFILE_SLUG)
    policy = (cfg or {}).get("policy", {})
    threshold = int(policy.get("domain_publish_threshold", 50))
    # Step 1: ensure linkedin source exists (no scraping)
    await ensure_linkedin_source(db)
    # Step 2: collect sources (deterministic)
    sources = await _collect_sources(db)
    if not sources:
        await audit("profile_agent", "DOMAIN_DISCOVERY", "no_sources", {"reason": "no verified sources"}, event_type="DOMAIN_DISCOVERY")
        return {"domains": [], "reason": "no sources"}
    # Step 3: discovery + clustering
    buckets = _discover_domains(sources)
    # Step 4: live portfolio health (deterministic, cheap HEAD)
    await validate_portfolio_urls(db)
    # Step 5: upsert each discovered domain, audit, and prune stale
    results = []
    for name, evidence in buckets.items():
        # deduplicate evidence by id
        uniq = {e["type"]+":"+e["id"]: e for e in evidence}
        evidence = list(uniq.values())
        doc = await _upsert_domain(db, name, evidence, threshold)
        results.append({"name": name, "slug": doc["slug"], "confidence": doc["confidence_score"], "status": doc["status"], "evidence": len(evidence)})
        await audit("profile_agent", "DOMAIN_UPSERT", doc["slug"], {"confidence": doc["confidence_score"], "evidence": len(evidence)}, event_type="DOMAIN_UPSERT")
    # Step 6: detect stale domains (existing active but no longer in buckets and score would be 0)
    existing = [d async for d in db["professional_domains"].find({"status": "active"})]
    for ex in existing:
        if ex["name"] not in buckets:
            # re-evaluate confidence would be 0 -> deactivate
            ex["confidence_score"] = 0
            ex["confidence_label"] = "Do not publish"
            ex["status"] = "inactive"
            ex["updated_at"] = utcnow()
            ex["last_verified_at"] = utcnow()
            await db["professional_domains"].update_one({"_id": ex["_id"]}, {"$set": {"confidence_score": 0, "confidence_label": "Do not publish", "status": "inactive", "updated_at": utcnow(), "last_verified_at": utcnow()}})
            # deactivate RAG
            try:
                from app.services import rag_ingest
                kd = await db["knowledge_documents"].find_one({"source_type": "service", "source_id": f"domain:{ex['slug']}"})
                if kd:
                    await rag_ingest.deactivate_document(str(kd["_id"]))
            except Exception:
                pass
    await audit("profile_agent", "DOMAIN_DISCOVERY_COMPLETE", triggered_by, {"domains": len(results)}, event_type="DOMAIN_DISCOVERY_COMPLETE")
    return {"domains": results, "sources": len(sources)}

