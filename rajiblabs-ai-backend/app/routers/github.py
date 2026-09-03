"""Admin GitHub: status, sync now, repo list, map repo → project."""
from fastapi import APIRouter, Depends, HTTPException
from app.auth.dependencies import require_admin
from app.config import get_settings
from app.database import get_db
from app.models import oid_str
from app.services import github_service
from app.services.notify import audit

router = APIRouter(prefix="/api/admin/github")


@router.get("/status")
async def status(email: str = Depends(require_admin)):
    s = get_settings()
    db = get_db()
    last = await db["github_sync_runs"].find_one(sort=[("started_at", -1)])
    if last:
        last = oid_str(last)
    return {"connected": bool(s.github_token), "owner": s.github_owner,
            "count": await db["github_repositories"].count_documents({}), "last_sync": last}


@router.post("/sync")
async def sync(email: str = Depends(require_admin)):
    try:
        result = await github_service.sync_now()
    except RuntimeError as e:
        raise HTTPException(400, str(e))
    await audit(email, "GITHUB_SYNC", "github")
    return result


@router.get("/repositories")
async def repos(tracked: bool | None = None, email: str = Depends(require_admin)):
    db = get_db()
    q = {}
    cur = db["github_repositories"].find(q).sort("stars", -1).limit(200)
    return [oid_str(d) async for d in cur]


@router.post("/repositories/{rid}/map")
async def map_repo(rid: str, project_slug: str, email: str = Depends(require_admin)):
    from bson import ObjectId
    db = get_db()
    await db["github_repositories"].update_one({"_id": ObjectId(rid)}, {"$set": {"project_slug": project_slug}})
    await audit(email, "GITHUB_MAP", rid, {"project": project_slug})
    return {"ok": True}
