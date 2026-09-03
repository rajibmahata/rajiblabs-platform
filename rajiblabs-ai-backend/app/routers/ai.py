"""Admin AI: rewrite draft, review score, approve/reject with versioning."""
from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from app.auth.dependencies import require_admin
from app.config import get_settings
from app.database import get_db, utcnow
from app.models import oid_str
from app.services import openai_service, quality
from app.services.notify import audit, notify

router = APIRouter(prefix="/api/admin/ai")


@router.post("/rewrite/{pid}")
async def rewrite(pid: str, email: str = Depends(require_admin)):
    db = get_db()
    p = await db["projects"].find_one({"_id": ObjectId(pid)})
    if not p:
        raise HTTPException(404, "Project not found")
    repo = None
    if p.get("github_url"):
        repo = await db["github_repositories"].find_one({"html_url": p["github_url"]})
    content, h = await openai_service.generate_project_content(
        p["name"], (repo or {}).get("readme", ""), {"description": p.get("short_description", ""), "language": ""}, p)
    # Hash dedup — skip if unchanged
    if h == p.get("source_hash"):
        return {"skipped": True, "reason": "no meaningful change"}
    score = quality.score_content(content, (repo or {}).get("readme", ""))
    await db["ai_jobs"].insert_one({"job_type": "rewrite", "entity_id": pid, "status": "completed",
                                    "input_hash": h, "result": content.model_dump(),
                                    "score": score.model_dump(), "created_at": utcnow()})
    await db["ai_content_versions"].insert_one({"project_id": pid, "new_content": content.model_dump(),
                                                "model": get_settings().openai_model, "quality_score": score.overall,
                                                "source_hash": h, "status": "pending", "created_at": utcnow()})
    s = get_settings()
    if s.ai_auto_publish and score.passed:
        await db["projects"].update_one({"_id": p["_id"]}, {"$set": {
            "short_description": content.short_description, "full_description": content.description,
            "source_hash": h, "updated_at": utcnow()}})
        await audit(email, "AI_APPROVE", p.get("slug", pid))
    else:
        await notify("AI_REVIEW", f"AI draft ready: {p['name']}", f"Score {score.overall}",
                     "project", pid)
    return {"content": content.model_dump(), "score": score.model_dump(), "source_hash": h}


@router.post("/review/{pid}")
async def review(pid: str, email: str = Depends(require_admin)):
    db = get_db()
    p = await db["projects"].find_one({"_id": ObjectId(pid)})
    if not p:
        raise HTTPException(404, "Project not found")
    from app.schemas import AIContentOut
    c = AIContentOut(title=p["name"], short_description=p.get("short_description", ""),
                     description=p.get("full_description", ""), technology_summary=",".join(p.get("technologies", [])),
                     seo_title=p["name"], seo_description=p.get("short_description", "")[:160])
    return quality.score_content(c, "").model_dump()


@router.post("/versions/{vid}/decision")
async def decide(vid: str, approve: bool, email: str = Depends(require_admin)):
    db = get_db()
    v = await db["ai_content_versions"].find_one({"_id": ObjectId(vid)})
    if not v:
        raise HTTPException(404, "Version not found")
    await db["ai_content_versions"].update_one({"_id": v["_id"]}, {"$set": {
        "status": "approved" if approve else "rejected", "approved_by": email, "approved_at": utcnow()}})
    if approve:
        nc = v["new_content"]
        await db["projects"].update_one({"_id": ObjectId(v["project_id"])}, {"$set": {
            "short_description": nc.get("short_description", ""),
            "full_description": nc.get("description", ""), "source_hash": v.get("source_hash", ""),
            "updated_at": utcnow()}})
    await audit(email, "AI_APPROVE" if approve else "AI_REJECT", v["project_id"])
    return {"ok": True}


@router.get("/versions/{pid}")
async def versions(pid: str, email: str = Depends(require_admin)):
    db = get_db()
    cur = db["ai_content_versions"].find({"project_id": pid}).sort("created_at", -1).limit(20)
    return [oid_str(d) async for d in cur]
