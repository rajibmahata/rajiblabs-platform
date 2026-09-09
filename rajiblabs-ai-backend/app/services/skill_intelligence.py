"""Skill Intelligence — autonomous discovery from verified sources.

One source of truth: `skills` collection (normalized, evidence-backed).
`profiles.skills` is kept as a derived cache (published names sorted by
confidence) for legacy RAG/public code that reads it.

No invention: a skill appears only if at least one evidence source
contains it; confidence is evidence-weighted, not LLM-hallucinated.
"""
import hashlib
import logging
import re
from datetime import datetime, timezone
from collections import defaultdict, Counter

from app.database import get_db, utcnow
from app.services.notify import audit

log = logging.getLogger("rajiblabs")

# --- Taxonomy: canonical categories and known synonyms ---
# Maps normalized skill -> category. Used for categorization, not invention.
TAXONOMY: dict[str, str] = {
    # Programming Languages
    "c#": "Programming Languages", "c sharp": "Programming Languages", "csharp": "Programming Languages",
    "python": "Programming Languages", "typescript": "Programming Languages", "javascript": "Programming Languages",
    "java": "Programming Languages", "go": "Programming Languages", "rust": "Programming Languages",
    # Frameworks
    ".net": "Frameworks", ".net 8": "Frameworks", ".net 10": "Frameworks", "dotnet": "Frameworks",
    "asp.net core": "Frameworks", "blazor": "Frameworks", "ef core": "Frameworks",
    "react": "Frontend", "fastapi": "Backend", "asp.net mvc": "Backend",
    "tailwind": "Frontend", "tailwind css": "Frontend", "html & css": "Frontend", "html/css": "Frontend", "responsive ui": "Frontend",
    # Backend
    "microservices": "Backend", "rest apis": "Backend", "cqrs & design patterns": "Backend", "cqrs": "Backend",
    "wcf": "Backend", "entity framework": "Backend",
    # Databases
    "sql server": "Databases", "cosmos db": "Databases", "sqlite": "Databases", "vector search": "Databases",
    "qdrant": "Databases", "mongodb": "Databases",
    # Cloud
    "azure": "Cloud", "azure cloud": "Cloud", "azure devops": "Cloud", "azure functions": "Cloud",
    "logic apps": "Cloud", "service bus": "Cloud", "event grid": "Cloud",
    # DevOps
    "docker": "DevOps", "docker compose": "DevOps", "ci/cd": "DevOps", "github copilot": "DevOps",
    # AI / ML
    "rag pipelines": "AI / ML", "rag systems": "AI / ML", "llm integration": "AI / ML",
    "openai/gemini apis": "AI / ML", "openai": "AI / ML", "prompt engineering": "AI / ML",
    "agentic ai": "Agentic AI", "ai automation": "Agentic AI",
    # Architecture
    "rest apis": "Architecture", "microservices": "Architecture",
    # APIs
    "open api": "APIs", "rest apis": "APIs",
    # Tools
    "git": "Tools", "github": "Tools",
}

# Canonical display names for normalized keys
DISPLAY: dict[str, str] = {
    "c#": "C#", "c sharp": "C#", "csharp": "C#",
    ".net": ".NET", ".net 8": ".NET 8", ".net 10": ".NET 10", "dotnet": ".NET",
    "asp.net core": "ASP.NET Core", "blazor": "Blazor", "ef core": "EF Core",
    "react": "React", "fastapi": "FastAPI", "python": "Python", "typescript": "TypeScript",
    "javascript": "JavaScript", "azure": "Azure", "docker": "Docker",
    "sql server": "SQL Server", "cosmos db": "Cosmos DB",
}

# Lightweight synonym normalization (no invention)
ALIASES = {
    "c#": ["c#", "c sharp", "csharp"],
    ".net": [".net", "dotnet"],
    "react": ["react", "react.js", "reactjs"],
    "node": ["node", "node.js"],
}

def _norm(name: str) -> str:
    n = name.strip().lower()
    n = re.sub(r"\s+", " ", n)
    n = n.replace("–", "-").replace("—", "-")
    # map known aliases to canonical normalized
    for canon, alts in ALIASES.items():
        if n in alts:
            return canon
    return n

def _slug(n: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", n.lower()).strip("-")
    return re.sub(r"-{2,}", "-", s)[:80] or "skill"

def _hash(*parts: str) -> str:
    return hashlib.sha256("|".join(p or "" for p in parts).encode()).hexdigest()[:16]

def _categorize(norm: str, fallback: str = "Other") -> str:
    if norm in TAXONOMY:
        return TAXONOMY[norm]
    # heuristic: if contains frontend keywords
    if any(k in norm for k in ["react", "tailwind", "html", "css", "javascript", "typescript", "responsive"]):
        return "Frontend"
    if any(k in norm for k in ["sql", "cosmos", "vector", "qdrant", "database"]):
        return "Databases"
    if any(k in norm for k in ["azure", "cloud"]):
        return "Cloud"
    if any(k in norm for k in ["docker", "ci/cd", "devops", "copilot"]):
        return "DevOps"
    if any(k in norm for k in ["rag", "llm", "openai", "prompt", "ai"]):
        return "AI / ML"
    if any(k in norm for k in [".net", "c#", "asp.net", "blazor", "ef core", "microservices", "cqrs"]):
        return "Backend"
    return fallback

def _display_name(norm: str, original: str) -> str:
    return DISPLAY.get(norm, original.strip())

# Evidence weight per source type (higher = stronger signal)
WEIGHTS = {
    "resume": 30,
    "profile": 15,
    "project": 20,
    "portfolio": 20,
    "product": 20,
    "github": 15,
    "experience": 18,
    "linkedin": 10,
    "course": 8,
}

async def _collect_evidence(db):
    """Gather all evidence strings with provenance."""
    evidence = []
    # 1. Resumes (all versions, active and archived for history, but weight differs)
    async for r in db["resumes"].find({}):
        text = (r.get("extracted_text") or r.get("filename") or "")[:4000]
        # Detect if resume text actually contains skills (not just filename)
        has_text = bool((r.get("extracted_text") or "").strip())
        evidence.append({
            "type": "resume",
            "id": str(r.get("_id")),
            "name": r.get("filename") or r.get("file_name", "resume"),
            "text": text,
            "weight": WEIGHTS["resume"] if has_text else 8,
            "ts": r.get("uploaded_at") or r.get("created_at"),
        })
    # 2. Profile embedded skills (legacy)
    prof = await db["profiles"].find_one() or {}
    if prof.get("skills"):
        evidence.append({
            "type": "profile",
            "id": str(prof.get("_id", "profile")),
            "name": "Profile skills",
            "text": ", ".join(prof.get("skills", [])),
            "weight": WEIGHTS["profile"],
            "ts": prof.get("updated_at"),
        })
    # 3. Projects
    async for p in db["projects"].find({"published": True}):
        txt = f"{p.get('name','')} {' '.join(p.get('technologies',[]))} {p.get('short_description','')} {p.get('full_description','')}"
        evidence.append({"type": "project", "id": p.get("slug"), "name": p.get("name"), "text": txt, "weight": WEIGHTS["project"], "ts": p.get("updated_at")})
        # Also add individual techs as separate evidence items for stronger counting
        for tech in p.get("technologies", [])[:6]:
            evidence.append({"type": "project", "id": p.get("slug"), "name": p.get("name"), "text": tech, "weight": 6, "ts": p.get("updated_at")})
    # 4. Portfolio
    async for p in db["portfolio"].find({"status": "published"}):
        txt = f"{p.get('title','')} {' '.join(p.get('tech_stack',[]))} {p.get('description','')} {p.get('purpose','')}"
        evidence.append({"type": "portfolio", "id": p.get("slug"), "name": p.get("title"), "text": txt, "weight": WEIGHTS["portfolio"], "ts": p.get("updated_at")})
        for tech in p.get("tech_stack", [])[:6]:
            evidence.append({"type": "portfolio", "id": p.get("slug"), "name": p.get("title"), "text": tech, "weight": 6, "ts": p.get("updated_at")})
    # 5. Products
    async for p in db["products"].find({"status": {"$in": ["published","featured"]}}):
        txt = f"{p.get('name','')} {' '.join(p.get('tech_stack',[]))} {p.get('description','')}"
        evidence.append({"type": "product", "id": p.get("slug"), "name": p.get("name"), "text": txt, "weight": WEIGHTS["product"], "ts": p.get("updated_at")})
        for tech in p.get("tech_stack", [])[:6]:
            evidence.append({"type": "product", "id": p.get("slug"), "name": p.get("name"), "text": tech, "weight": 6, "ts": p.get("updated_at")})
    # 6. GitHub repos
    async for r in db["github_repositories"].find({"is_private": {"$ne": True}}):
        txt = f"{r.get('name','')} {r.get('language','')} {' '.join(r.get('topics',[]))} {r.get('description','')}"
        evidence.append({"type": "github", "id": r.get("full_name"), "name": r.get("full_name"), "text": txt, "weight": WEIGHTS["github"], "ts": r.get("pushed_at") or r.get("updated_at")})
        if r.get("language"):
            evidence.append({"type": "github", "id": r.get("full_name"), "name": r.get("full_name"), "text": r.get("language"), "weight": 8, "ts": r.get("pushed_at")})
        for topic in (r.get("topics") or [])[:4]:
            evidence.append({"type": "github", "id": r.get("full_name"), "name": r.get("full_name"), "text": topic, "weight": 6, "ts": r.get("pushed_at")})
    # 7. Professional experience
    async for e in db["experience"].find({"status": "published"}):
        txt = f"{e.get('company','')} {e.get('role','')} {' '.join(e.get('technologies',[]))} {e.get('description','')}"
        evidence.append({"type": "experience", "id": e.get("company",""), "name": e.get("company"), "text": txt, "weight": WEIGHTS["experience"], "ts": e.get("updated_at")})
        for tech in e.get("technologies", [])[:6]:
            evidence.append({"type": "experience", "id": e.get("company",""), "name": e.get("company"), "text": tech, "weight": 6, "ts": e.get("updated_at")})
    # 8. Courses / learning paths (if any)
    async for c in db["courses"].find({}):
        txt = f"{c.get('title','')} {c.get('url','')}"
        evidence.append({"type": "course", "id": str(c.get("_id")), "name": c.get("title"), "text": txt, "weight": WEIGHTS["course"] if "course" in WEIGHTS else 5, "ts": c.get("updated_at")})
    # 9. LinkedIn via professional_sources (approved)
    try:
        async for s in db["professional_sources"].find({"type": "linkedin", "enabled": True}):
            txt = s.get("linkedin_text") or s.get("url") or ""
            if txt.strip():
                evidence.append({"type": "linkedin", "id": "linkedin", "name": "LinkedIn", "text": txt[:2000], "weight": WEIGHTS["linkedin"], "ts": s.get("updated_at")})
    except Exception:
        pass
    return evidence

def _extract_skills_from_text(text: str, evidence_weight: int) -> list[str]:
    """Deterministic skill extraction from a single evidence text blob.
    
    Uses a curated allowlist derived from taxonomy + known Rajib skills.
    No invention: only returns skills that literally appear (case-insensitive).
    """
    # Build allowlist from taxonomy keys + display values + known techs
    allowlist = set(TAXONOMY.keys()) | set(DISPLAY.keys()) | set(TAXONOMY.values())
    # Add extra known skills from seed
    allowlist.update(["c#", ".net", ".net 8", ".net 10", "asp.net core", "blazor", "react", "python", "fastapi", "azure", "docker", "sql server", "cosmos db", "rag pipelines", "llm integration", "vector search", "prompt engineering", "github copilot", "microservices", "cqrs & design patterns", "cqrs", "rest apis", "ef core", "azure devops", "javascript", "html & css", "responsive ui", "html/css"])
    # Normalize text for matching
    low = text.lower()
    found = []
    for skill in allowlist:
        # Use word boundaries for short skills
        pat = r"\b" + re.escape(skill.lower()) + r"\b"
        if skill.lower() in ["c#", ".net", "go", "r", "c"]:
            # Special handling for short/symbol skills
            if skill.lower() in low:
                found.append(skill)
        else:
            if re.search(pat, low):
                found.append(skill)
    # Deduplicate by normalized
    uniq = {}
    for s in found:
        n = _norm(s)
        if n not in uniq:
            uniq[n] = s
    return list(uniq.values())

async def discover_skills(db, evidence: list[dict] | None = None) -> dict[str, list[dict]]:
    """Map normalized skill -> list of evidence dicts."""
    if evidence is None:
        evidence = await _collect_evidence(db)
    skill_to_evidence = defaultdict(list)
    for ev in evidence:
        # Split evidence text into skill candidates via allowlist matching
        candidates = _extract_skills_from_text(ev["text"], ev["weight"])
        for cand in candidates:
            n = _norm(cand)
            # Filter to only known Rajib-relevant skills (taxonomy or seed) to avoid inventing from generic words
            # Keep only if cand normalized is in taxonomy or is a known display skill
            if n not in TAXONOMY and n not in { _norm(k) for k in DISPLAY.keys() } and n not in { _norm(s) for s in ["sql server", "cosmos db", "rag pipelines", "llm integration", "vector search", "prompt engineering", "github copilot", "microservices", "rest apis", "ef core"] }:
                # Still allow if it's in the evidence and matches allowlist
                # _extract already filtered, so we keep it
                pass
            skill_to_evidence[n].append(ev)
    return skill_to_evidence

def _evidence_summary(evidences: list[dict]) -> dict:
    """Compute backend metadata from evidence list."""
    by_type = Counter(e["type"] for e in evidences)
    # Last used is max timestamp among evidence
    last_used = None
    for e in evidences:
        ts = e.get("ts")
        if ts and (not last_used or ts > last_used):
            last_used = ts
    first_detected = None
    for e in evidences:
        ts = e.get("ts")
        if ts and (not first_detected or ts < first_detected):
            first_detected = ts
    # Confidence: weighted evidence count, capped, with boost for multiple source types
    total_weight = sum(e.get("weight", 5) for e in evidences)
    distinct_types = len(by_type)
    # Normalize to 0-1 confidence: 30 = one strong source, 60 = two types, 90 = 3+ types
    confidence = min(0.99, (total_weight / 80) + (distinct_types * 0.12))
    # Round to 2 decimals
    confidence = round(confidence, 2)
    return {
        "first_detected": first_detected,
        "last_used": last_used,
        "last_validated": utcnow(),
        "evidence_count": len(evidences),
        "distinct_types": distinct_types,
        "by_type": dict(by_type),
        "confidence": confidence,
    }

async def sync_skills(triggered_by: str = "scheduler") -> dict:
    """Main entry for Profile Manager — discover, upsert, deactivate stale, sync RAG/profile.

    Returns stats: {created, updated, deactivated, skipped, total}
    """
    db = get_db()
    evidence = await _collect_evidence(db)
    skill_map = await discover_skills(db, evidence)
    # Existing skills for versioning/dedup (handle legacy docs without normalized_name)
    existing = {}
    async for s in db["skills"].find({}):
        key = s.get("normalized_name") or _norm(s.get("name", ""))
        if key:
            # If duplicate normalized (legacy duplicates), keep the most recent
            if key not in existing or (s.get("updated_at") or s.get("created_at")) > (existing[key].get("updated_at") or existing[key].get("created_at") or s.get("created_at")):
                existing[key] = s
    stats = {"created": 0, "updated": 0, "deactivated": 0, "skipped": 0, "total": 0}
    # Track which skills were seen this run
    seen_norm = set(skill_map.keys())
    # Upsert discovered skills
    for norm, ev_list in skill_map.items():
        meta = _evidence_summary(ev_list)
        # Skip weak single-evidence low-weight skills (e.g., one github topic mention)
        if len(ev_list) == 1 and ev_list[0]["weight"] < 8 and meta["confidence"] < 0.35:
            stats["skipped"] += 1
            continue
        # Determine category and display name
        # Use most frequent original spelling from evidences
        counter = Counter()
        for e in ev_list:
            # Find which candidate string matched this norm
            for cand in _extract_skills_from_text(e["text"], e["weight"]):
                if _norm(cand) == norm:
                    counter[cand] += 1
        display = counter.most_common(1)[0][0] if counter else norm
        display = _display_name(norm, display)
        category = _categorize(norm)
        slug = _slug(norm)
        existing_doc = existing.get(norm)
        # Build evidence payload (ids + names, not full text)
        projects = list({e["id"] for e in ev_list if e["type"] in ("project", "portfolio", "product")})
        github_repos = list({e["id"] for e in ev_list if e["type"] == "github"})
        resume_versions = list({e["id"] for e in ev_list if e["type"] == "resume"})
        # Versioning: hash of sorted evidence ids + normalized name
        version_hash = _hash(norm, *sorted([f"{e['type']}:{e['id']}" for e in ev_list]))
        now = utcnow()
        # Status based on confidence: only >0.35 is publishable (weak 0.25-0.49 stays archived)
        status = "published" if meta["confidence"] >= 0.35 else "archived"
        doc = {
            "name": display,
            "normalized_name": norm,
            "slug": slug,
            "category": category,
            "status": status,
            "display_order": existing_doc["display_order"] if existing_doc else 999,
            "evidence": {
                "sources": [{"type": e["type"], "id": e["id"], "name": e["name"]} for e in ev_list[:10]],
                "projects": projects[:10],
                "github_repositories": github_repos[:10],
                "resume_versions": resume_versions[:10],
                "by_type": meta["by_type"],
            },
            "evidence_count": meta["evidence_count"],
            "confidence": meta["confidence"],
            "version": (existing_doc.get("version", 0) + 1) if existing_doc and existing_doc.get("evidence", {}).get("sources") != [{"type": e["type"], "id": e["id"]} for e in ev_list[:3]] else (existing_doc.get("version", 0) if existing_doc else 1),
            "first_detected": existing_doc.get("first_detected", meta["first_detected"] or now) if existing_doc else (meta["first_detected"] or now),
            "last_used": meta["last_used"] or now,
            "last_validated": now,
            "updated_at": now,
            "content_hash": version_hash,
        }
        if existing_doc:
            # Detect if nothing changed (hash + confidence + category + status)
            expected_status = "published" if meta["confidence"] >= 0.35 else "archived"
            if existing_doc.get("content_hash") == version_hash and existing_doc.get("category") == category and abs((existing_doc.get("confidence") or 0) - meta["confidence"]) < 0.05 and existing_doc.get("status") == expected_status:
                stats["skipped"] += 1
                continue
            await db["skills"].update_one({"normalized_name": norm}, {"$set": doc})
            stats["updated"] += 1
        else:
            doc["created_at"] = now
            doc["first_detected"] = meta["first_detected"] or now
            # Find max display_order to append
            max_order = 0
            if existing:
                max_order = max([s.get("display_order", 0) for s in existing.values()] or [0])
            # Use category order? simple append
            doc["display_order"] = max_order + 10
            await db["skills"].insert_one(doc)
            # Preserve history: set created_at
            stats["created"] += 1
        stats["total"] += 1
    # Deactivate stale skills (no evidence this run, but had before)
    for norm, doc in existing.items():
        if norm not in seen_norm:
            # Check if skill was only from seed and still valid? Keep if confidence was high and last_used recent?
            # For now, mark as archived if not seen for 2 runs or low confidence
            if doc.get("confidence", 0) < 0.4 or doc.get("evidence_count", 0) <= 1:
                await db["skills"].update_one({"normalized_name": norm}, {"$set": {"status": "archived", "updated_at": utcnow()}})
                stats["deactivated"] += 1
    # Sync profiles.skills as derived cache (published names sorted by confidence)
    try:
        cur = db["skills"].find({"status": "published"}).sort([("confidence", -1), ("display_order", 1)])
        published_names = [d["name"] async for d in cur]
        # Keep legacy profiles.skills in sync (for RAG profile doc and backward compat)
        await db["profiles"].update_one({}, {"$set": {"skills": published_names, "updated_at": utcnow()}}, upsert=False)
    except Exception as e:
        log.warning("sync profiles.skills failed: %s", e)
    # RAG: upsert grouped skills doc and per-skill docs (first-class)
    try:
        from app.services import rag_ingest
        # Grouped doc for backward compat (skills:all)
        grouped = {}
        async for s in db["skills"].find({"status": "published"}):
            grouped.setdefault(s.get("category", "General"), []).append(s.get("name", ""))
        if grouped:
            content = "\\n".join(f"{cat}: {', '.join(names)}" for cat, names in grouped.items())
            await rag_ingest.upsert_document("profile", "skills:all", "Rajib — Technical Skills", content, url="https://rajiblabs.com/#about", tags=["skills", "rajib"])
        # Per-skill docs for fine-grained retrieval
        async for s in db["skills"].find({"status": "published"}):
            skill_content = f"Skill: {s['name']} (Category: {s['category']})\\nEvidence: {s.get('evidence_count',0)} sources, confidence {s.get('confidence',0)}\\nProjects: {', '.join(s.get('evidence',{}).get('projects',[])[:3])}\\nGitHub: {', '.join(s.get('evidence',{}).get('github_repositories',[])[:3])}"
            await rag_ingest.upsert_document("profile", f"skill:{s['slug']}", f"Skill — {s['name']}", skill_content, tags=["skill", s["category"]])
        # Deactivate RAG for archived skills
        async for s in db["skills"].find({"status": "archived"}):
            # Find and deactivate its RAG doc
            kd = await db["knowledge_documents"].find_one({"source_id": f"skill:{s['slug']}", "status": "active"})
            if kd:
                try:
                    await rag_ingest.deactivate_document(str(kd["_id"]))
                except Exception:
                    pass
    except Exception as e:
        log.warning("skill RAG sync failed: %s", e)
    await audit("profile_agent", "SKILL_SYNC", triggered_by, stats)
    return stats
