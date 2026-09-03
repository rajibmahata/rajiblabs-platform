"""Admin System Logs — failure entries with automatic 5-day retention (TTL index)."""
from fastapi import APIRouter, Depends, Query
from app.auth.dependencies import require_admin
from app.config import get_settings
from app.database import get_db
from app.models import oid_str
from app.services.notify import audit

router = APIRouter(prefix="/api/admin/logs")


@router.get("")
async def list_logs(level: str | None = Query(default=None, pattern="^(error|warning)$"),
                    source: str | None = None,
                    limit: int = Query(default=100, ge=1, le=500),
                    email: str = Depends(require_admin)):
    db = get_db()
    q: dict = {}
    if level:
        q["level"] = level
    if source:
        q["source"] = source
    cur = db["error_logs"].find(q).sort("created_at", -1).limit(limit)
    return [oid_str(d) async for d in cur]


@router.get("/stats")
async def log_stats(email: str = Depends(require_admin)):
    from datetime import timedelta
    from app.database import utcnow
    s = get_settings()
    db = get_db()
    cutoff = utcnow() - timedelta(days=s.log_retention_days)
    by_level = await db["error_logs"].aggregate([
        {"$match": {"created_at": {"$gte": cutoff}}},
        {"$group": {"_id": "$level", "count": {"$sum": 1}}},
    ]).to_list(length=10)
    by_source = await db["error_logs"].aggregate([
        {"$match": {"created_at": {"$gte": cutoff}}},
        {"$group": {"_id": "$source", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]).to_list(length=20)
    newest = await db["error_logs"].find_one(sort=[("created_at", -1)])
    oldest = await db["error_logs"].find_one(sort=[("created_at", 1)])
    return {
        "retention_days": s.log_retention_days,
        "window_start": cutoff,
        "total_in_window": sum(b["count"] for b in by_level),
        "by_level": {b["_id"]: b["count"] for b in by_level},
        "by_source": {b["_id"]: b["count"] for b in by_source},
        "newest": oid_str(newest) if newest else None,
        "oldest": oid_str(oldest) if oldest else None,
    }


@router.delete("")
async def purge_logs(email: str = Depends(require_admin)):
    """Manual early purge (retention TTL handles the normal case)."""
    db = get_db()
    res = await db["error_logs"].delete_many({})
    await audit(email, "LOGS_PURGE", "error_logs", {"deleted": res.deleted_count})
    return {"ok": True, "deleted": res.deleted_count}
