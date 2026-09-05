"""Daily agent pipeline: GitHub scan → change detect → AI draft → quality gate → draft/publish → audit."""
import logging
from app.config import get_settings
from app.database import get_db, utcnow
from app.services import github_service, openai_service, quality
from app.services.notify import log_error, notify, purge_old_logs

log = logging.getLogger("rajiblabs")


async def run_daily_agent(triggered_by: str = "scheduler") -> dict:
    s = get_settings()
    db = get_db()
    run = await db["agent_runs"].insert_one(
        {"agent": "daily", "status": "running", "started_at": utcnow(), "triggered_by": triggered_by,
         "scanned": 0, "updated": 0, "drafts": 0, "errors": []})
    rid = run.inserted_id
    try:
        scanned = updated = drafts = 0
        # Scheduled retention sweep (TTL index is primary; this is the backup).
        try:
            purged = await purge_old_logs(db)
        except Exception:
            purged = 0
        if s.is_github_configured():
            sync = await github_service.sync_now()
            scanned = sync.get("found", 0)
        # For each tracked repo with a mapped project, check readme hash change
        async for repo in db["github_repositories"].find({"project_slug": {"$exists": True}}):
            proj = await db["projects"].find_one({"slug": repo["project_slug"]})
            if not proj or "ai" in (proj.get("locked_fields") or []):
                continue
            content, h = await openai_service.generate_project_content(
                proj["name"], repo.get("readme", ""),
                {"description": repo.get("description", ""), "language": repo.get("language", "")}, proj)
            if h == proj.get("source_hash"):
                continue  # cost control: skip unchanged
            score = quality.score_content(content, repo.get("readme", ""))
            await db["ai_content_versions"].insert_one({
                "project_id": str(proj["_id"]), "new_content": content.model_dump(),
                "model": s.openai_model, "quality_score": score.overall,
                "source_hash": h, "status": "pending", "created_at": utcnow()})
            drafts += 1
            if s.ai_auto_publish and score.passed:
                await db["projects"].update_one({"_id": proj["_id"]}, {"$set": {
                    "short_description": content.short_description,
                    "full_description": content.description, "source_hash": h, "updated_at": utcnow()}})
                updated += 1
        await db["agent_runs"].update_one({"_id": rid}, {"$set": {
            "status": "success", "finished_at": utcnow(), "scanned": scanned,
            "updated": updated, "drafts": drafts, "logs_purged": purged,
            "summary": f"scanned={scanned} updated={updated} drafts={drafts} logs_purged={purged}"}})
        await notify("AGENT", "Daily agent complete", f"scanned={scanned} updated={updated} drafts={drafts}")
        return {"scanned": scanned, "updated": updated, "drafts": drafts, "logs_purged": purged}
    except Exception as e:
        import traceback
        log.exception("daily agent failed")
        await db["agent_runs"].update_one({"_id": rid}, {"$set": {
            "status": "failed", "finished_at": utcnow(), "errors": [str(e)]}})
        await notify("AGENT_FAILURE", "Daily agent failed", str(e)[:500])
        try:
            await log_error("daily_agent", "Daily agent failed", str(e)[:2000],
                            logger="app.agents.daily_agent",
                            stack_trace=traceback.format_exc()[-4000:])
        except Exception:
            pass
        return {"error": str(e)}
