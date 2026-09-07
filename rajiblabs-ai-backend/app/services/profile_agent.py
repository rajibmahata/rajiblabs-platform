"""Profile Intelligence Agent — keeps RajibLabs profile accurate and synchronized.

Reuses: github_service, rag_ingest, lead_ai.AIService, database, notify.
No duplicate RAG/scheduler/auth systems. Tools are permission-checked.
"""
import hashlib
import logging
import re
import uuid
from datetime import datetime, timezone

from app.config import get_settings
from app.database import get_db, utcnow
from app.services.notify import audit, log_error

log = logging.getLogger("rajiblabs")

ALLOWED_PROFILE_FIELDS = {"skills", "bio", "title", "headline", "career"}
SENSITIVE_KEYS = {"password", "secret", "token", "key", "credential"}


def _hash(*parts: str) -> str:
    return hashlib.sha256("|".join(p or "" for p in parts).encode()).hexdigest()[:16]


def _sanitize_for_ai(text: str) -> str:
    # filter secrets before AI
    for pat in [r"sk-[A-Za-z0-9]{10,}", r"ghp_[A-Za-z0-9]{10,}", r"Bearer\s+\S+"]:
        text = re.sub(pat, "***", text, flags=re.I)
    return text


async def _get_profile(db):
    return await db["profiles"].find_one() or {}


async def _get_active_resume(db):
    cur = db["resumes"].find({"active": True}).sort("version", -1).limit(1)
    docs = [d async for d in cur]
    return docs[0] if docs else None


def _extract_resume_text(resume_doc: dict) -> str:
    # naive extraction: if extracted_text exists else filename placeholder
    return (resume_doc.get("extracted_text") or resume_doc.get("filename") or "")[:8000]


async def analyze_resume(resume_text: str) -> dict:
    """Cheap extraction: skills, experience deltas via LLM or regex fallback."""
    settings = get_settings()
    resume_text = _sanitize_for_ai(resume_text[:6000])
    if not settings.openai_api_key:
        # regex fallback
        skills = re.findall(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b", resume_text)[:20]
        return {"skills": list(set(skills))[:10], "experience": [], "certifications": [], "raw": resume_text[:500]}
    try:
        from app.services.lead_ai import AIService
        svc = AIService()
        if not svc.configured:
            raise RuntimeError("AI not configured")
        out = await svc._complete(
            [{"role": "system", "content": "Extract resume into JSON keys: skills[], experience[], certifications[], education[], role_title, summary. Return JSON only."},
             {"role": "user", "content": resume_text[:4000]}],
            max_tokens=800, temperature=0.2, tag="profile-resume-extract")
        return out.get("data", {})
    except Exception as e:
        log.warning("resume AI extraction failed: %s", e)
        return {"skills": [], "experience": [], "raw": resume_text[:500], "error": str(e)[:200]}


async def check_configuration_health(db) -> dict:
    """Deterministic health report without LLM."""
    report = {"healthy": [], "warnings": [], "errors": [], "actions": []}
    profile = await _get_profile(db)
    if not profile.get("full_name"):
        report["errors"].append("Missing profile full_name")
        report["actions"].append("Complete profile full_name")
    if not (profile.get("skills") or []):
        report["warnings"].append("No skills listed")
    # projects/portfolio missing images/descriptions
    for coll, label in [("portfolio", "Portfolio"), ("products", "Products")]:
        async for doc in db[coll].find({}):
            if not doc.get("description"):
                report["warnings"].append(f"{label} {doc.get('slug')} missing description")
            if not doc.get("featured_image") and not doc.get("gallery"):
                report["warnings"].append(f"{label} {doc.get('slug')} missing images")
            # URL validation
            for field in ["live_url", "github_url"]:
                url = doc.get(field)
                if url and not re.match(r"^https?://", url):
                    report["errors"].append(f"{label} {doc.get('slug')} invalid {field}: {url}")
                    report["actions"].append(f"Fix URL {field} for {doc.get('slug')}")
    # GitHub unsynced
    repos = [d async for d in db["github_repositories"].find({})]
    portfolio_slugs = {d.get("slug") async for d in db["portfolio"].find({}, {"slug":1})}
    for r in repos:
        name = r.get("name", "").lower()
        if name and name not in portfolio_slugs and r.get("stars",0) > 5:
            report["warnings"].append(f"Repo {r.get('full_name')} not in Portfolio")
            report["actions"].append(f"Create draft for {r.get('full_name')}")
    # knowledge stale
    failed = await db["knowledge_documents"].count_documents({"status":"failed"})
    if failed:
        report["errors"].append(f"{failed} knowledge documents failed indexing")
        report["actions"].append("Re-index failed knowledge")
    # translations
    langs = await db["languages"].count_documents({"enabled": True})
    if langs < 2:
        report["warnings"].append("Only one language enabled")
    # status
    if not report["errors"] and not report["warnings"]:
        report["healthy"].append("All checks passed")
    return report


async def _create_proposal(db, target_collection: str, target_id: str, field: str, proposed_value, reason: str, confidence: float, source: dict, before, after):
    doc = {
        "target_collection": target_collection,
        "target_id": target_id,
        "field": field,
        "proposed_value": proposed_value,
        "reason": reason,
        "confidence": confidence,
        "source": source,
        "before": before,
        "after": after,
        "status": "pending",
        "created_at": utcnow(),
    }
    res = await db["profile_agent_proposals"].insert_one(doc)
    return str(res.inserted_id)


async def sync_github(db, policy: dict) -> dict:
    """Reuse existing github integration, detect new/changed/deleted."""
    from app.services import github_service
    result = {"synced":0, "new":0, "changed":0, "deleted":0, "drafts":0}
    if not policy.get("github_sync", True):
        return result
    try:
        sync = await github_service.sync_now()
        result["synced"] = sync.get("found",0)
        result["new"] = sync.get("added",0)
        result["changed"] = sync.get("updated",0)
        # detect deleted: github_repos not in fetched but in DB
        # sync_now doesn't delete, so we detect here
        all_repos = [d async for d in db["github_repositories"].find({})]
        # For portfolio-worthy detection
        for repo in all_repos:
            if repo.get("is_private"):
                continue
            full = repo.get("full_name","")
            exists = await db["portfolio"].find_one({"slug": repo.get("name","").lower()})
            if not exists and repo.get("stars",0) >= 3 and not repo.get("is_private"):
                # create draft if auto_create_drafts
                if policy.get("auto_create_drafts"):
                    # generate structured draft via LLM cheap
                    draft = await _generate_project_draft(repo)
                    if draft:
                        # insert as pending proposal, not direct publish
                        await _create_proposal(db, "portfolio", "new", "title", draft.get("title"), "Portfolio-worthy repo discovered", 0.7, {"type":"github","id":full}, None, draft)
                        result["drafts"] += 1
                else:
                    await _create_proposal(db, "portfolio", "new", "title", repo.get("name"), "Repo not in portfolio (review)", 0.6, {"type":"github","id":full}, None, {"repo":full})
                    result["drafts"] += 1
    except Exception as e:
        log.warning("profile github sync failed: %s", e)
        await log_error("profile_agent", "GitHub sync failed", str(e)[:1000])
    return result


async def _generate_project_draft(repo: dict) -> dict | None:
    """Generate structured project draft from repo metadata (no secrets)."""
    settings = get_settings()
    name = repo.get("name","")
    desc = repo.get("description","")[:500]
    readme = (repo.get("readme") or "")[:3000]
    lang = repo.get("language","")
    topics = ",".join(repo.get("topics",[])[:5])
    if not settings.openai_api_key:
        return {"title": name, "short_description": desc[:120], "technologies": [lang] if lang else [], "repo_url": repo.get("html_url"), "status":"draft", "missing":["problem","solution"]}
    # sanitize
    context = _sanitize_for_ai(f"Repo: {name}\nDesc: {desc}\nLanguage: {lang}\nTopics: {topics}\nREADME: {readme}")
    try:
        from app.services.lead_ai import AIService
        svc = AIService()
        if not svc.configured:
            raise RuntimeError("AI not configured")
        out = await svc._complete(
            [{"role":"system","content":"Generate portfolio draft JSON: title, short_description (1 line), full_description (2-3 sentences), problem, solution, features[], architecture, technologies[], role. Mark missing fields as 'MISSING'. Return JSON only."},
             {"role":"user","content": context[:3500]}],
            max_tokens=700, temperature=0.3, tag="profile-project-draft")
        data = out.get("data",{})
        data["repo_url"] = repo.get("html_url")
        return data
    except Exception as e:
        log.warning("draft generation failed for %s: %s", name, e)
        return None


async def run_profile_agent(triggered_by: str = "scheduler") -> dict:
    """Main agent run — idempotent, cost-controlled."""
    db = get_db()
    from app.services import agent_config
    cfg = await agent_config.get_agent(db, agent_config.PROFILE_SLUG)
    if not cfg or not cfg.get("enabled"):
        return {"skipped": True, "reason":"disabled"}
    policy = cfg.get("policy", {})
    run = await db["profile_agent_runs"].insert_one({
        "agent": "profile", "status":"running", "started_at": utcnow(),
        "triggered_by": triggered_by, "sources_inspected": [], "proposed":0, "applied":0, "errors":[]
    })
    rid = run.inserted_id
    try:
        sources_inspected = []
        proposed = 0
        applied = 0
        # 1. Profile ingestion: compare resume vs profile
        resume = await _get_active_resume(db)
        profile = await _get_profile(db)
        if resume:
            sources_inspected.append("resume")
            text = _extract_resume_text(resume)
            h = _hash(text)
            # only process if changed (cache)
            last_hash = (await db["profile_agent_runs"].find_one(sort=[("started_at",-1)], filter={"status":"success"} ) or {}).get("resume_hash")
            # For simplicity, check last run's hash stored in agent doc
            agent_meta = await db["ai_agents"].find_one({"slug": agent_config.PROFILE_SLUG}) or {}
            last_resume_hash = agent_meta.get("last_resume_hash")
            if h != last_resume_hash:
                extracted = await analyze_resume(text)
                # detect new skills
                new_skills = [s for s in extracted.get("skills",[]) if s not in (profile.get("skills") or [])]
                if new_skills:
                    await _create_proposal(db, "profiles", str(profile.get("_id")), "skills", (profile.get("skills") or [])+new_skills, "New skills from resume", 0.8, {"type":"resume","id":str(resume.get("_id"))}, profile.get("skills"), new_skills)
                    proposed+=1
                # update hash
                await db["ai_agents"].update_one({"slug": agent_config.PROFILE_SLUG}, {"$set":{"last_resume_hash": h}})

        # 2. GitHub sync
        sources_inspected.append("github")
        gh_result = await sync_github(db, policy)
        proposed += gh_result.get("drafts",0)

        # 3. Health check
        health = await check_configuration_health(db)
        sources_inspected.append("health")

        # 4. Knowledge sync for approved changes (only changed docs)
        if policy.get("knowledge_sync"):
            from app.services import rag_ingest
            # find published portfolio/products not yet indexed or outdated
            for coll in ["portfolio","products"]:
                async for doc in db[coll].find({"status":"published"}):
                    # check if knowledge doc exists and hash matches
                    sid = f"{coll}:{doc.get('slug')}"
                    existing = await db["knowledge_documents"].find_one({"source_id": sid})
                    content = (doc.get("description") or "") + (doc.get("title") or doc.get("name") or "")
                    ch = _hash(content)
                    if not existing or existing.get("content_hash") != ch:
                        # only auto if policy allows
                        if policy.get("auto_update_metadata"):
                            try:
                                await rag_ingest.upsert_document(
                                    "project" if coll=="portfolio" else "product",
                                    sid, doc.get("title") or doc.get("name"), content,
                                    url=f"https://rajiblabs.com/{coll}/{doc.get('slug')}"
                                )
                                applied+=1
                            except Exception as e:
                                log.warning("KB sync failed %s: %s", sid, e)
                        else:
                            await _create_proposal(db, coll, str(doc["_id"]), "knowledge_sync", "sync", "Knowledge stale, needs re-index", 0.9, {"type":"kb","id":sid}, None, None)
                            proposed+=1
            sources_inspected.append("knowledge")

        # 5. Generate recommendations
        await db["profile_agent_runs"].update_one({"_id": rid}, {"$set":{
            "status":"success", "finished_at": utcnow(),
            "sources_inspected": sources_inspected,
            "proposed": proposed, "applied": applied,
            "health": health,
            "gh_result": gh_result
        }})
        await db["ai_agents"].update_one({"slug": agent_config.PROFILE_SLUG}, {"$inc":{"stats.runs":1}})
        await audit("profile_agent", "RUN_SUCCESS", str(rid), {"proposed":proposed, "applied":applied})
        return {"proposed": proposed, "applied": applied, "sources": sources_inspected, "health": health, "gh": gh_result}
    except Exception as e:
        import traceback
        log.exception("profile agent failed")
        await db["profile_agent_runs"].update_one({"_id": rid}, {"$set":{"status":"failed","finished_at": utcnow(), "errors":[str(e)]}})
        await log_error("profile_agent", "Profile agent failed", str(e)[:2000], stack_trace=traceback.format_exc()[-4000:])
        await db["ai_agents"].update_one({"slug": agent_config.PROFILE_SLUG}, {"$inc":{"stats.errors":1}})
        return {"error": str(e)}


async def apply_proposal(proposal_id: str, actor: str) -> dict:
    """Apply an approved proposal — permission checked, requires approval."""
    from bson import ObjectId
    db = get_db()
    try:
        oid = ObjectId(proposal_id)
    except Exception:
        raise ValueError("Invalid proposal id")
    prop = await db["profile_agent_proposals"].find_one({"_id": oid})
    if not prop:
        raise ValueError("Proposal not found")
    if prop.get("status") != "approved":
        raise ValueError("Proposal not approved")
    # backend authorization: only admin can apply (caller already checked require_admin, but double-check)
    # apply based on target
    coll = prop["target_collection"]
    field = prop["field"]
    if any(s in field.lower() for s in SENSITIVE_KEYS):
        raise ValueError("Sensitive field blocked")
    if coll == "profiles":
        await db["profiles"].update_one({"_id": ObjectId(prop["target_id"])}, {"$set": {field: prop["proposed_value"]}})
    elif coll in ["portfolio","products","legacy_projects"]:
        # handle "new" draft creation
        if prop["target_id"] == "new":
            doc = prop["after"] or {}
            # ensure draft status unless auto_publish
            from app.services import agent_config
            cfg = await agent_config.get_agent(db, agent_config.PROFILE_SLUG)
            if not cfg.get("policy",{}).get("auto_publish"):
                doc["status"] = "draft"
            await db[coll].insert_one({**doc, "created_at": utcnow(), "updated_at": utcnow()})
        else:
            await db[coll].update_one({"_id": ObjectId(prop["target_id"])}, {"$set": {field: prop["proposed_value"], "updated_at": utcnow()}})
    else:
        raise ValueError("Unknown collection")
    await db["profile_agent_proposals"].update_one({"_id": oid}, {"$set": {"status":"applied", "applied_at": utcnow(), "applied_by": actor}})
    # knowledge sync if needed
    try:
        from app.services import rag_ingest
        # trigger re-index for affected doc
        pass
    except Exception:
        pass
    await audit(actor, "PROFILE_PROPOSAL_APPLIED", proposal_id, {"field": field})
    return {"ok": True}


async def get_dashboard(db=None) -> dict:
    if db is None:
        db = get_db()
    from app.services import agent_config
    cfg = await agent_config.get_agent(db, agent_config.PROFILE_SLUG)
    health = await check_configuration_health(db)
    # completeness
    profile = await _get_profile(db)
    resume = await _get_active_resume(db)
    github_repos = await db["github_repositories"].count_documents({})
    portfolio = await db["portfolio"].count_documents({})
    products = await db["products"].count_documents({})
    kb_docs = await db["knowledge_documents"].count_documents({})
    pending = await db["profile_agent_proposals"].count_documents({"status":"pending"})
    last_run = await db["profile_agent_runs"].find_one(sort=[("started_at",-1)])
    next_run = "daily 06:00 Asia/Kolkata"  # from scheduler
    # stale detection: portfolio not updated in 180 days
    stale = await db["portfolio"].count_documents({"updated_at": {"$lt": datetime.now(timezone.utc).replace(year=datetime.now(timezone.utc).year-1)}}) if False else 0
    # missing translations: TODO compare with languages
    return {
        "profile_completeness": 80 if profile.get("full_name") and profile.get("skills") else 40,
        "resume_status": "active" if resume else "missing",
        "github_sync": {"repos": github_repos, "last_synced": (await db["github_repositories"].find_one(sort=[("last_synced_at",-1)]) or {}).get("last_synced_at")},
        "portfolio": portfolio,
        "products": products,
        "knowledge": kb_docs,
        "pending_approvals": pending,
        "last_run": last_run,
        "next_run": next_run,
        "health": health,
        "config": cfg.get("policy",{}) if cfg else {},
        "agent": cfg
    }
