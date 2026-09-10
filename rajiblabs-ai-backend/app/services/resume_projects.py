"""Resume → Projects consolidation (Profile Agent owned).

Extracts ALL projects mentioned across ALL resume versions (not just active),
deduplicates across versions, and merges with existing Projects/Portfolio/GitHub
Products/RAG without inventing details.

- Deterministic first, LLM assist only when configured (cost-controlled).
- Hash/versioning prevents reprocessing unchanged resumes.
- Resume projects without live/github URLs still become valid public records.
- Never deletes history; archived resumes remain source for consolidation.
"""
import hashlib
import logging
import re
from datetime import timezone
from pathlib import Path

from app.config import get_settings
from app.database import get_db, utcnow
from app.services.notify import audit

log = logging.getLogger("rajiblabs")

# Normalized project slug
def _slug(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (name or "").strip().lower()).strip("-")
    return re.sub(r"-{2,}", "-", s)[:80] or "project"

def _hash(*parts: str) -> str:
    return hashlib.sha256("|".join(p or "" for p in parts).encode()).hexdigest()[:16]

def _sanitize(text: str) -> str:
    for pat in [r"sk-[A-Za-z0-9]{10,}", r"ghp_[A-Za-z0-9]{10,}", r"Bearer\s+\S+"]:
        text = re.sub(pat, "***", text, flags=re.I)
    return text[:8000]

# ---------- Canonical evidence ----------
# Every project accumulates verified evidence entries {source, label, url}.
# Sources: resume | github | portfolio | product. The detail page renders
# these; nothing is invented — entries are only added from records that
# actually exist in MongoDB.
def _evidence_entry(source: str, label: str, url: str | None = None) -> dict:
    entry = {"source": source, "label": (label or "")[:120]}
    if url:
        entry["url"] = url[:500]
    return entry


def _merge_evidence(existing: list | None, new_entries: list[dict]) -> list[dict]:
    seen = set()
    out = []
    for e in (existing or []) + (new_entries or []):
        if not isinstance(e, dict):
            continue
        key = (str(e.get("source", "")).lower(), str(e.get("label", "")).lower())
        if not key[0] or key in seen:
            continue
        seen.add(key)
        out.append({"source": str(e.get("source", ""))[:20],
                    "label": str(e.get("label", ""))[:120],
                    **({"url": str(e.get("url", ""))[:500]} if e.get("url") else {})})
    return out[:20]


# ---------- Portfolio classification (configurable, deterministic) ----------
PORTFOLIO_CRITERIA_DEFAULTS = {"score_threshold": 50, "auto_create_draft": False}

# Keywords signaling enterprise scale / business complexity / architecture
# depth. Presence only adds score — never invents size or status.
ENTERPRISE_HINTS = (
    "enterprise", "microservices", "multi-tenant", "saas", "azure", "kubernetes",
    "event-driven", "cqrs", "distributed", "devops", "ci/cd", "serverless",
    "high availability", "scalab", "real-time", "realtime", "omnichannel",
    "blockchain", "ai", "machine learning", "rag", "automation",
)


async def get_portfolio_criteria(db=None) -> dict:
    """Configurable portfolio gate from site_settings (no migration needed)."""
    criteria = dict(PORTFOLIO_CRITERIA_DEFAULTS)
    try:
        db = db if db is not None else get_db()
        doc = await db["site_settings"].find_one({"key": "portfolio_criteria"})
        if isinstance(doc, dict) and isinstance(doc.get("value"), dict):
            v = doc["value"]
            try:
                criteria["score_threshold"] = max(0, min(100, int(v.get("score_threshold", 50))))
            except (TypeError, ValueError):
                pass
            criteria["auto_create_draft"] = bool(v.get("auto_create_draft", False))
    except Exception as e:
        log.warning("portfolio criteria fallback to defaults: %s", e)
    return criteria


def _portfolio_score(name: str, short_description: str = "", technologies: list | None = None,
                     evidence_sources: int = 0, has_live: bool = False,
                     has_github: bool = False, client: str = "") -> int:
    """Deterministic 0-100 portfolio-worthiness score. Evidence-only inputs."""
    score = 0
    desc = (short_description or "")
    if len(desc) >= 80:
        score += 20
    elif len(desc) >= 40:
        score += 12
    elif desc.strip():
        score += 6
    techs = technologies or []
    score += min(18, len(techs) * 3)
    score += min(24, max(0, evidence_sources) * 8)
    low = f"{name} {desc}".lower()
    hits = sum(1 for h in ENTERPRISE_HINTS if h in low)
    score += min(20, hits * 4)
    if has_live:
        score += 5
    if has_github:
        score += 5
    if (client or "").strip():
        score += 5
    return max(0, min(100, score))


def _enrich_from_github(doc_patch: dict, repo: dict | None) -> list[dict]:
    """Fill missing tech/solution from the STORED repo record (no API calls).

    Returns evidence entries. Never overwrites existing content, never invents
    fields the repo record does not have."""
    if not repo:
        return []
    evidence = [_evidence_entry("github", repo.get("full_name") or repo.get("name") or "repository",
                                repo.get("html_url"))]
    existing_techs = doc_patch.get("technologies") or []
    repo_techs = []
    if repo.get("language"):
        repo_techs.append(str(repo["language"])[:40])
    for t in (repo.get("topics") or [])[:4]:
        if str(t).strip():
            repo_techs.append(str(t).strip()[:40])
    merged = list(existing_techs)
    for t in repo_techs:
        if t and t not in merged:
            merged.append(t)
    if merged != existing_techs:
        doc_patch["technologies"] = merged[:12]
    # Repo descriptions are maintainer-written purpose statements — safe to use
    # as solution context only when the project has none.
    if not (doc_patch.get("solution") or "").strip():
        desc = (repo.get("description") or "").strip()
        if len(desc) > 40:
            doc_patch["solution"] = desc[:800]
    return evidence


async def _maybe_create_portfolio_draft(db, slug: str, name: str, short_description: str,
                                        technologies: list, client: str, stats: dict) -> dict | None:
    """Create a portfolio DRAFT for a worthy project (opt-in via criteria).

    Drafts never publish automatically — an admin promotes them. Returns the
    created doc, or None when disabled/exists/failed."""
    try:
        if await db["portfolio"].find_one({"slug": slug}):
            return None
        now = utcnow()
        doc = {
            "title": name, "slug": slug,
            "short_description": (short_description or f"Project: {name}")[:300],
            "description": (short_description or "")[:2000],
            "tech_stack": list(technologies or [])[:12],
            "status": "draft",
            "origin": "client" if (client or "").strip() else "engineering",
            "source": "agent:resume_projects",
            "rag_indexed": True,
            "featured": False,
            "display_order": 900,
            "created_at": now, "updated_at": now,
        }
        res = await db["portfolio"].insert_one(doc)
        doc["_id"] = res.inserted_id
        stats["portfolio_drafts"] += 1
        try:
            await audit("profile_agent", "PORTFOLIO_DRAFT_CREATED", slug,
                        {"source": "resume_projects"})
        except Exception:
            pass
        return doc
    except Exception as e:
        log.warning("portfolio auto-draft failed for %s: %s", slug, e)
        stats["errors"].append(f"{slug}: portfolio draft failed {e}"[:200])
        return None

# ---------- Deterministic extraction ----------
# Project headings often look like "Name - Client - Company, 2019–Present" or "Name - Subtitle"
# We capture blocks separated by blank lines or double newline.
# Known section markers to start capturing
SECTION_MARKERS = [
    "PROFESSIONAL PROJECTS",
    "SELECTED AI / PRODUCT",
    "AI / PRODUCT ENGINEERING PROJECTS",
    "SELECTED AI",
    "PROJECTS",
]

def _deterministic_extract(text: str) -> list[dict]:
    """Very conservative regex extraction — no invention, only splits.
    Returns list of {name, short_description, full_context}.
    """
    if not text or len(text.strip()) < 100:
        return []
    # Find start of professional projects sections
    upper = text.upper()
    start_idx = None
    for m in SECTION_MARKERS:
        idx = upper.find(m)
        if idx != -1:
            if start_idx is None or idx < start_idx:
                start_idx = idx
    proj_text = text[start_idx:] if start_idx is not None else text
    # Split into candidate blocks: double newline preceded by a title-like line
    # Title pattern: starts with capital letters, may include numbers, spaces, /, -, 2-6 words, possibly followed by " - "
    # We'll look for lines that are likely project titles: leading "Name - " and relatively short (<80 chars)
    lines = proj_text.splitlines()
    projects: list[dict] = []
    current: dict | None = None
    buf: list[str] = []
    # Also capture technology hints from nearby tech sections for later merge
    for i, raw in enumerate(lines):
        line = raw.strip()
        if not line:
            if current and buf:
                # flush buffered description into current
                desc = " ".join(buf).strip()
                if desc and not current.get("short_description"):
                    current["short_description"] = desc[:300]
                # keep full context
                if desc:
                    current["_context"] = (current.get("_context","") + " " + desc).strip()[:2000]
                buf = []
            continue
        # Detect title-like lines: short, starts with caps, contains " - " or is standalone and next line is description
        # Heuristic: line length 10-90, first char is A-Z or digit, contains no lowercase sentence start? Actually many titles are capitalized
        # We'll treat lines that are relatively short and next non-empty line is longer (description)
        is_title_candidate = False
        # Pattern: "Name - Something" with 2-5 words before dash, capitalized
        if re.match(r"^[A-Z][A-Za-z0-9\s/&().'-]{4,80}\s+-\s+.+", line) and len(line) < 120:
            is_title_candidate = True
        # Also titles like "ReturnGuard AI - Omnichannel Retail ..." same pattern already matched
        # Fallback: standalone title in ALL CAPS? e.g., "TRANSZOOM" alone
        elif re.match(r"^[A-Z][A-Z0-9\s&/-]{3,50}$", line) and len(line) < 40 and ":" not in line:
            # need next line to be non-title (description)
            is_title_candidate = True
        if is_title_candidate:
            # flush previous
            if current:
                if buf:
                    desc = " ".join(buf).strip()
                    if desc and not current.get("short_description"):
                        current["short_description"] = desc[:300]
                    if desc:
                        current["_context"] = (current.get("_context","") + " " + desc).strip()[:2000]
                # only keep if name is not too generic (avoid section headers)
                if current.get("name") and len(current["name"]) > 3 and current["name"].upper() not in ("PROFESSIONAL PROJECTS - CLIENT & EMPLOYER WORK", "SELECTED AI / PRODUCT ENGINEERING PROJECTS - RAJIBLABS", "PROFESSIONAL EXPERIENCE"):
                    projects.append(current)
            # start new project
            # Extract name as part before " - " if present, else whole line
            name = line.split(" - ")[0].strip()
            # For ALL-CAPS single word titles, keep as is
            if len(name) > 80:
                name = name[:80]
            current = {"name": name, "short_description": "", "_context": ""}
            buf = []
            # If title line contains extra context after dash, treat that as start of description
            if " - " in line:
                remainder = " - ".join(line.split(" - ")[1:])
                if remainder and len(remainder) > 10:
                    buf.append(remainder.strip())
            continue
        # otherwise, accumulate into buffer for current project
        if current is not None:
            # Ignore very long lines that are clearly not part of project (like page numbers)
            if len(line) < 300:
                buf.append(line)
        else:
            # before first title, ignore
            pass
    # flush last
    if current:
        if buf:
            desc = " ".join(buf).strip()
            if desc and not current.get("short_description"):
                current["short_description"] = desc[:300]
            if desc:
                current["_context"] = (current.get("_context","") + " " + desc).strip()[:2000]
        if current.get("name") and len(current["name"]) > 3 and current["name"].upper() not in ("PROFESSIONAL PROJECTS - CLIENT & EMPLOYER WORK", "SELECTED AI / PRODUCT ENGINEERING PROJECTS - RAJIBLABS", "PROFESSIONAL EXPERIENCE"):
            projects.append(current)
    # Clean up and enrich: extract technologies from _context via known tokens
    tech_tokens = [
        ".NET", "C#", "ASP.NET", "Blazor", "React", "Python", "FastAPI", "Azure", "SQL Server",
        "Cosmos DB", "Qdrant", "ChromaDB", "OpenAI", "GPT-4o", "DeepSeek", "RAG", "LLM", "Agent",
        "Docker", "Kubernetes", "Azure Functions", "Service Bus", "Event Grid", "SignalR", "WebSocket",
        "Redis", "PostgreSQL", "MongoDB", "Celery", "PWA", "TypeScript", "JavaScript", "Node.js",
        "Stripe", "HMAC", "Blockchain", "n8n", "Langdock", "Whisper", "Vector", "Embedding",
        "Microservices", "CQRS", "Clean Architecture", "Solid", "WebSocket"
    ]
    for p in projects:
        ctx = (p.get("_context") or "") + " " + (p.get("short_description") or "")
        found = []
        low = ctx.lower()
        for tok in tech_tokens:
            if tok.lower() in low:
                # preserve original casing
                found.append(tok)
        # dedupe
        seen = set()
        uniq = []
        for t in found:
            if t.lower() not in seen:
                seen.add(t.lower())
                uniq.append(t)
        p["technologies"] = uniq[:8]
        # Derive problem/solution from context if possible: first sentence as problem, second as solution?
        # Keep conservative: use full context as description but don't invent separate problem/solution.
        # Fill short_description if empty: first 140 chars of context
        if not p.get("short_description") and p.get("_context"):
            p["short_description"] = p["_context"][:140]
        # cleanup keys
        p.pop("_context", None)
        # Ensure slug later
    # Filter out non-projects (heuristic: must have at least 20 chars description or be known AI/product names)
    HEADERS_DENY = {
        "professional projects", "selected ai", "selected ai / product engineering projects",
        "professional summary", "core expertise", "technical skills", "professional experience",
        "education", "certification", "professional projects - client & employer work",
        "selected ai / product engineering projects - rajiblabs",
        "professional experience ", "select ai", "ai / product engineering projects"
    }
    filtered = []
    for p in projects:
        name_low = p["name"].strip().lower()
        # drop exact header matches and substring headers
        if name_low in HEADERS_DENY or any(h == name_low for h in HEADERS_DENY):
            continue
        if any(h in name_low for h in ["professional summary", "core expertise", "technical skills", "professional experience", "education", "certification", "professional projects", "selected ai / product"]):
            continue
        # also drop overly generic single-word headers that are all caps and short but not known products
        if len(name_low.split()) == 1 and len(name_low) < 25 and name_low.isupper():
            if name_low.lower() not in ["transzoom", "truckit365"]:
                # TRANSZOOM is ok as all caps but known product -> already allowed via known list
                # but generic headers like "PROFESSIONAL" would be dropped anyway
                pass
        if len(p.get("short_description","")) < 20:
            # allow known AI products even with short desc (PestFlow etc)
            if name_low not in ["pestflow", "returnguard ai", "historiaai", "lexvault", "inboxpilot", "transzoom", "cinematic lens", "corporate hour", "empowering weighs", "truckit365", "returnguard", "inboxpilot", "historia"]:
                # if still very short, skip (likely noise)
                if len(p.get("short_description","")) < 10:
                    continue
        # also drop if name is exactly a section header length > 30 and contains "/" or "&"
        if len(p["name"]) > 40 and ("/" in p["name"] or "PROJECTS" in p["name"].upper()):
            if "AI / PRODUCT" in p["name"].upper():
                continue
        filtered.append(p)
    return filtered


async def _llm_extract(text: str) -> list[dict] | None:
    """LLM extraction for higher fidelity (when provider configured). Returns None on fallback."""
    s = get_settings()
    if not s.openai_api_key:
        return None
    try:
        from app.services.lead_ai import AIService
        svc = AIService()
        if not svc.configured:
            return None
        prompt = (
            "Extract ALL distinct projects mentioned in this resume text. "
            "Return JSON array where each element has keys: name (string), short_description (1-2 sentences summarizing what was built), "
            "technologies (array of up to 6 tech strings only if explicitly mentioned), client (string or null), period (string or null). "
            "Do NOT invent URLs, metrics, or technologies not in the text. "
            "If a project has no URL in the text, set live_url and github_url to null. "
            "Be exhaustive: include client work, employer work, and AI/product projects under RajibLabs. "
            "Return JSON array only."
        )
        ctx = _sanitize(text[:6000])
        out = await svc._complete(
            [{"role": "system", "content": prompt},
             {"role": "user", "content": ctx}],
            max_tokens=1500, temperature=0.2, tag="resume-project-extract")
        data = out.get("data")
        # AIService._complete returns parsed JSON in data when response is JSON; if it returned list directly
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "projects" in data:
            return data.get("projects", [])
        # sometimes content is wrapped
        return None
    except Exception as e:
        log.warning("LLM project extraction failed: %s", e)
        return None


async def extract_projects_from_text(text: str) -> list[dict]:
    llm_result = await _llm_extract(text)
    if llm_result is not None and isinstance(llm_result, list) and len(llm_result) > 0:
        # Normalize llm_result entries to our schema
        out = []
        for item in llm_result:
            if not isinstance(item, dict):
                continue
            name = (item.get("name") or item.get("title") or "").strip()
            if not name or len(name) < 2:
                continue
            desc = (item.get("short_description") or item.get("description") or "").strip()
            if not desc:
                desc = (item.get("purpose") or "")[:300]
            techs = item.get("technologies") or item.get("tech_stack") or []
            if not isinstance(techs, list):
                techs = [str(techs)]
            out.append({
                "name": name[:120],
                "short_description": desc[:300],
                "technologies": [str(t)[:40] for t in techs[:6] if str(t).strip()],
                "client": (item.get("client") or "")[:120],
                "period": (item.get("period") or "")[:80],
                "live_url": item.get("live_url"),
                "github_url": item.get("github_url"),
            })
        if out:
            return out
    # fallback deterministic
    return _deterministic_extract(text)


async def consolidate_resume_projects(db=None, triggered_by: str = "profile_agent") -> dict:
    """Collect all resume projects, deduplicate, merge with existing, upsert public projects.

    Returns stats: {resumes_scanned, projects_found, deduped, created, updated, skipped, errors}
    """
    if db is None:
        db = get_db()
    stats = {"resumes_scanned": 0, "projects_found": 0, "deduped": 0, "created": 0, "updated": 0,
             "skipped": 0, "portfolio_worthy": 0, "portfolio_drafts": 0, "errors": []}
    # Collect all resumes (active + archived) for history
    resumes = [d async for d in db["resumes"].find({}).sort("version", 1)]
    stats["resumes_scanned"] = len(resumes)
    all_extracted: list[dict] = []
    seen_file_hash: set[str] = set()
    for resume in resumes:
        text = (resume.get("extracted_text") or "").strip()
        if not text:
            # try to extract on the fly if file exists but text missing (e.g., after fix)
            try:
                from app.services.resume_text import extract_and_store
                rid = resume.get("legacy_id") or str(resume["_id"])
                text = await extract_and_store(rid)
                text = (text or "").strip()
                # re-fetch
                resume = await db["resumes"].find_one({"_id": resume["_id"]})
                text = (resume.get("extracted_text") or "").strip() if resume else text
            except Exception as e:
                log.warning("resume re-extract failed for %s: %s", resume.get("_id"), e)
                continue
        if not text:
            stats["skipped"] += 1
            continue
        # content hash versioning: skip re-processing same extracted_text content for this resume
        cur_hash = _hash(text)
        if resume.get("projects_extracted_hash") == cur_hash:
            # already processed and projects already consolidated; still add its previously extracted? Need to ensure we still count it for dedupe
            # We skip LLM/deterministic re-extraction but we can reload cached projects? Instead we just re-extract but hash check avoids duplicate work per resume
            # For now, skip re-extraction if hash same — but we need its projects for dedupe. So we keep a cached list in resume doc if available
            cached = resume.get("projects_cache")
            if cached and isinstance(cached, list):
                all_extracted.extend(cached)
                stats["projects_found"] += len(cached)
                continue
            # otherwise proceed to re-extract (no cache)
            pass
        extracted = await extract_projects_from_text(text)
        # cache on resume doc for versioning (so unchanged resumes not recomputed)
        try:
            await db["resumes"].update_one({"_id": resume["_id"]}, {"$set": {"projects_extracted_hash": cur_hash, "projects_cache": extracted[:30], "projects_extracted_at": utcnow()}})
        except Exception:
            pass
        all_extracted.extend(extracted)
        stats["projects_found"] += len(extracted)

    # Deduplicate across resume versions by normalized slug (case-insensitive)
    deduped: dict[str, dict] = {}
    for p in all_extracted:
        name = (p.get("name") or "").strip()
        if not name:
            continue
        slug = _slug(name)
        # Keep the longest/best description (don't invent)
        if slug in deduped:
            existing = deduped[slug]
            # merge: keep longest short_description
            if len(p.get("short_description","")) > len(existing.get("short_description","")):
                existing["short_description"] = p["short_description"]
            # merge technologies
            techs = list(set((existing.get("technologies") or []) + (p.get("technologies") or [])))[:8]
            existing["technologies"] = techs
            # keep client/period if missing
            for k in ("client","period"):
                if not existing.get(k) and p.get(k):
                    existing[k] = p[k]
        else:
            deduped[slug] = {**p, "slug": slug}
    stats["deduped"] = len(deduped)
    if not deduped:
        return stats

    # Load existing projects for merge check (published projects + legacy portfolio slugs for dedupe)
    existing_projects = {}
    async for proj in db["projects"].find({}):
        key = (proj.get("slug") or _slug(proj.get("name",""))).lower()
        existing_projects[key] = proj
    # Also portfolio docs (slug → doc) for evidence + auto-draft dedupe
    portfolio_by_slug = {}
    async for d in db["portfolio"].find({}):
        if d.get("slug"):
            portfolio_by_slug[str(d["slug"]).lower()] = d
    # GitHub repos for enrichment (verified URLs). Keyed exact + normalized
    # (dashes/underscores stripped) so "pestflow-app" still links "PestFlow".
    github_by_name = {}
    async for repo in db["github_repositories"].find({"is_private": {"$ne": True}}):
        n = (repo.get("name") or "").lower()
        if n:
            github_by_name[n] = repo
            github_by_name[re.sub(r"[-_]", "", n)] = repo
    criteria = await get_portfolio_criteria(db)
    threshold = criteria["score_threshold"]

    def _norm(s: str) -> str:
        return re.sub(r"[-_]", "", (s or "").lower())

    def _match_repo(key: str) -> dict | None:
        hit = github_by_name.get(key) or github_by_name.get(_norm(key))
        if hit:
            return hit
        # Prefix fallback: repo "pestflow-app" still evidences project "PestFlow".
        # Exact and normalized-exact matches always win; first prefix hit wins.
        nk = _norm(key)
        if len(nk) >= 4:
            for rk, repo in github_by_name.items():
                if len(rk) >= 4 and (rk.startswith(nk) or nk.startswith(rk)):
                    return repo
        return None

    for slug, proj in deduped.items():
        low_slug = slug.lower()
        name = proj["name"]
        repo = _match_repo(low_slug)
        portfolio_doc = portfolio_by_slug.get(low_slug)
        # Resume evidence entry (client/period when the resume stated them)
        client = (proj.get("client") or "").strip()
        period = (proj.get("period") or "").strip()
        resume_label = "Resume" + (f" — {client}" if client else "") + (f" ({period})" if period else "")
        resume_evidence = [_evidence_entry("resume", resume_label)]
        # Check if already exists in projects
        existing = existing_projects.get(low_slug)
        # Also fuzzy: if name contains existing name or vice versa? Keep strict slug for now to avoid false merges
        # Check portfolio existence for info, but still create in projects if not exists (projects is source of truth for public API)
        if existing:
            # enrich only missing fields, never overwrite locked/manual edits or invent
            locked = set(existing.get("locked_fields") or [])
            patch = {}
            # technologies merge
            existing_techs = existing.get("technologies") or []
            new_techs = [t for t in (proj.get("technologies") or []) if t not in existing_techs]
            if new_techs and "technologies" not in locked:
                merged = (existing_techs + new_techs)[:12]
                patch["technologies"] = merged
            # short_description enrichment if existing short is empty or very short and new is substantive
            if not (existing.get("short_description") or "").strip() and proj.get("short_description"):
                if "short_description" not in locked:
                    patch["short_description"] = proj["short_description"][:300]
            # full_description / business value? Keep existing; only fill if missing
            # Don't overwrite problem/solution unless empty
            for field in ["problem", "solution", "business_value"]:
                if not (existing.get(field) or "").strip() and proj.get(field):
                    patch[field] = proj[field][:800]
            # GitHub enrichment from the STORED repo record (no API calls):
            # verified URL + topics/language tech + description→solution fallback.
            gh_patch = {"technologies": list(patch.get("technologies") or existing_techs),
                        "solution": patch.get("solution") or existing.get("solution") or ""}
            gh_evidence = _enrich_from_github(gh_patch, repo)
            if "technologies" in gh_patch and gh_patch["technologies"] != (patch.get("technologies") or existing_techs) \
                    and "technologies" not in locked:
                patch["technologies"] = gh_patch["technologies"]
            if gh_patch.get("solution") and not (existing.get("solution") or "").strip() \
                    and "solution" not in locked and "solution" not in patch:
                patch["solution"] = gh_patch["solution"]
            if not existing.get("github_url") and repo and "github_url" not in locked:
                patch["github_url"] = repo.get("html_url")
            # No live URL invention: only if resume had explicit URL (rare) we could add, but resume text typically has none
            # Canonical evidence: resume + github + portfolio entries, merged append-only
            new_evidence = list(resume_evidence) + list(gh_evidence)
            if portfolio_doc:
                new_evidence.append(_evidence_entry(
                    "portfolio", portfolio_doc.get("title") or slug,
                    f"https://rajiblabs.com/portfolio/{portfolio_doc.get('slug', slug)}"))
            merged_evidence = _merge_evidence(existing.get("evidence"), new_evidence)
            if merged_evidence != (existing.get("evidence") or []):
                patch["evidence"] = merged_evidence
            # Portfolio-worthiness score (agent-owned fields, recomputed; only
            # written when changed so repeat runs stay idempotent)
            ev_sources = len({e.get("source") for e in merged_evidence})
            score = _portfolio_score(
                name, patch.get("short_description") or existing.get("short_description") or "",
                patch.get("technologies") or existing_techs, ev_sources,
                bool(existing.get("live_url")), bool(patch.get("github_url") or existing.get("github_url")),
                client)
            worthy = score >= threshold
            if score != existing.get("portfolio_score"):
                patch["portfolio_score"] = score
            if worthy != existing.get("portfolio_worthy"):
                patch["portfolio_worthy"] = worthy
            if worthy:
                stats["portfolio_worthy"] += 1
            if patch:
                patch["updated_at"] = utcnow()
                # preserve published status
                try:
                    await db["projects"].update_one({"_id": existing["_id"]}, {"$set": patch})
                    stats["updated"] += 1
                except Exception as e:
                    stats["errors"].append(f"{slug}: update failed {e}"[:200])
            else:
                stats["skipped"] += 1
            if worthy and portfolio_doc is None and criteria["auto_create_draft"]:
                created = await _maybe_create_portfolio_draft(
                    db, slug, name, patch.get("short_description") or existing.get("short_description") or "",
                    patch.get("technologies") or existing_techs, client, stats)
                if created:
                    portfolio_by_slug[low_slug] = created
        else:
            # Create new project record — valid even without live/github URLs (confidential handling in UI)
            # Determine category: product if mentions SaaS/multi-tenant/product, else project?
            # Use heuristic: AI/product projects or known product keywords => product, else project
            category = "project"
            ctx_low = (proj.get("short_description","") + " " + " ".join(proj.get("technologies") or [])).lower()
            if any(k in ctx_low for k in ["saas", "multi-tenant", "product", "saas platform"]) or low_slug in ["pestflow", "returnguard-ai", "historiaai", "lexvault", "inboxpilot", "docusign-hub"]:
                # For resume AI products, keep as product? But spec says consolidate with Projects/Portfolio/Products — we choose project for client work, product for RajibLabs products
                if any(x in name.lower() for x in ["returnguard", "historia", "lexvault", "inboxpilot", "pestflow"]):
                    category = "product"
            # Build doc per ProjectIn schema (minimal, no invention)
            # Find github_url if verified repo exists (exact + normalized match)
            github_url = proj.get("github_url")
            matched_repo = _match_repo(low_slug)
            if not github_url and matched_repo:
                github_url = matched_repo.get("html_url")
            # live_url stays None -> confidential
            live_url = proj.get("live_url")
            # Validate github_url per schema validator (must be https://github.com/rajibmahata/<repo>)
            if github_url and not github_url.startswith("https://github.com/"):
                github_url = None
            if github_url == "https://github.com/rajibmahata":
                github_url = None
            technologies = list(proj.get("technologies") or [])
            solution = (proj.get("solution") or "")[:2000]
            gh_evidence: list[dict] = []
            if matched_repo:
                tmp = {"technologies": list(technologies), "solution": solution}
                gh_evidence = _enrich_from_github(tmp, matched_repo)
                technologies = tmp["technologies"]
                solution = tmp["solution"]
            evidence = _merge_evidence(None, list(resume_evidence) + gh_evidence)
            if portfolio_by_slug.get(low_slug):
                pdoc = portfolio_by_slug[low_slug]
                evidence = _merge_evidence(evidence, [_evidence_entry(
                    "portfolio", pdoc.get("title") or slug,
                    f"https://rajiblabs.com/portfolio/{pdoc.get('slug', slug)}")])
            score = _portfolio_score(
                name, (proj.get("short_description") or "")[:300], technologies,
                len({e.get("source") for e in evidence}),
                bool(live_url), bool(github_url), client)
            worthy = score >= threshold
            doc = {
                "slug": slug,
                "name": name,
                "category": category,
                "status": "published",
                "published": True,
                "featured": False,
                "display_order": 900,  # appended after seeded, will be sorted
                "short_description": (proj.get("short_description") or f"Project: {name}")[:300],
                "full_description": (proj.get("short_description") or "")[:2000],
                "problem": (proj.get("problem") or "")[:1000],
                "solution": solution,
                "business_value": (proj.get("business_value") or "")[:1000],
                "role": "",
                "learnings": "",
                "beneficiaries": "",
                "domain": "",
                "evidence": evidence,
                "portfolio_score": score,
                "portfolio_worthy": worthy,
                "features": [],
                "architecture": "",
                "technologies": technologies,
                "github_url": github_url,
                "live_url": live_url,
                "video_url": None,
                "featured_image": None,
                "gallery": [],
                "locked_fields": [],
                "created_at": utcnow(),
                "updated_at": utcnow(),
                "source": "resume",
                "source_resume_stats": {"client": proj.get("client"), "period": proj.get("period")},
            }
            if worthy:
                stats["portfolio_worthy"] += 1
            # Avoid duplicate with portfolio slug? Still create; public API merges but DRY: if portfolio exists with same slug, we might skip creation and instead ensure portfolio is published?
            # For now, if portfolio exists, we still create in projects but with same slug, frontend dedupes; okay.
            # Ensure slug not already in projects (race)
            if await db["projects"].find_one({"slug": slug}):
                stats["skipped"] += 1
                continue
            try:
                await db["projects"].insert_one(doc)
                stats["created"] += 1
                if worthy and portfolio_by_slug.get(low_slug) is None \
                        and criteria["auto_create_draft"]:
                    created = await _maybe_create_portfolio_draft(
                        db, slug, name, doc["short_description"],
                        doc["technologies"], client, stats)
                    if created:
                        portfolio_by_slug[low_slug] = created
                # RAG sync for new project (content_hash dedup will handle)
                try:
                    from app.services import rag_ingest
                    body = "\n".join(filter(None, [
                        doc["short_description"],
                        f"Technologies: {', '.join(doc['technologies'])}" if doc["technologies"] else "",
                        f"Client: {doc['source_resume_stats']['client']}" if doc['source_resume_stats']['client'] else "",
                        f"Business value: {doc['business_value']}" if doc.get("business_value") else "",
                        f"Role: {doc['role']}" if doc.get("role") else "",
                    ]))
                    await rag_ingest.upsert_document(
                        "project" if category != "product" else "product",
                        f"project:{slug}",
                        name, body,
                        url=f"https://rajiblabs.com/portfolio/{slug}" if category != "product" else f"https://rajiblabs.com/products/{slug}",
                        language=(doc["technologies"] or [None])[0],
                        tags=["project", category, "resume"]
                    )
                except Exception as e:
                    log.warning("RAG sync for new resume project %s failed: %s", slug, e)
            except Exception as e:
                stats["errors"].append(f"{slug}: create failed {e}"[:200])

    try:
        await audit("profile_agent", "RESUME_PROJECTS_CONSOLIDATED", triggered_by,
                    {"created": stats["created"], "updated": stats["updated"],
                     "found": stats["deduped"], "portfolio_worthy": stats["portfolio_worthy"],
                     "portfolio_drafts": stats["portfolio_drafts"]})
    except Exception:
        pass
    return stats
