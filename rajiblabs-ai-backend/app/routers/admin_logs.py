"""Admin System Logs — failure entries, 7-day window, searchable + paginated.

Retention: MongoDB TTL index on ``created_at`` (LOG_RETENTION_DAYS, default 7)
plus a daily scheduled sweep (``purge_old_logs``, run by the daily agent).
The list endpoint always constrains to the retention window, so only the
latest 7 days are ever displayed.
"""
import re
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from app.auth.dependencies import require_admin
from app.config import get_settings
from app.database import get_db
from app.models import oid_str
from app.services.notify import audit

router = APIRouter(prefix="/api/admin/logs")

LEVELS = ("info", "warning", "error")
SORTS = ("newest", "oldest")
SEARCH_FIELDS = ("message", "source", "logger", "path", "details")


def build_log_query(q: str | None = None, level: str | None = None,
                    source: str | None = None,
                    date_from: datetime | None = None,
                    date_to: datetime | None = None,
                    window_start: datetime | None = None) -> dict:
    """Pure query builder (unit-tested): window cutoff is always applied."""
    query: dict = {}
    if window_start is not None:
        query["created_at"] = {"$gte": window_start}
    if level in LEVELS:
        query["level"] = level
    if source:
        query["source"] = source
    if date_from or date_to:
        rng = dict(query.get("created_at", {}))
        if date_from:
            rng["$gte"] = max(date_from, rng["$gte"]) if "$gte" in rng else date_from
        if date_to:
            rng["$lte"] = date_to
        query["created_at"] = rng
    if q and q.strip():
        rx = {"$regex": re.escape(q.strip()[:200]), "$options": "i"}
        query["$or"] = [{f: rx} for f in SEARCH_FIELDS]
    return query


def log_out(d: dict) -> dict:
    d = oid_str(d)
    return {
        "id": d.get("id"), "level": d.get("level", "error"),
        "source": d.get("source", ""), "logger": d.get("logger"),
        "path": d.get("path"), "message": d.get("message", ""),
        "details": d.get("details", ""),
        "stack_trace": d.get("stack_trace"), "created_at": d.get("created_at"),
    }


async def _find_log(rid: str) -> dict | None:
    db = get_db()
    doc = await db["error_logs"].find_one({"legacy_id": rid})
    if doc:
        return doc
    from bson import ObjectId
    try:
        return await db["error_logs"].find_one({"_id": ObjectId(rid)})
    except Exception:
        return None


@router.get("")
async def list_logs(q: str | None = Query(default=None, max_length=200),
                    level: str | None = Query(default=None, pattern="^(info|warning|error)$"),
                    source: str | None = None,
                    date_from: datetime | None = None,
                    date_to: datetime | None = None,
                    sort: str = Query(default="newest", pattern="^(newest|oldest)$"),
                    page: int = Query(default=1, ge=1),
                    page_size: int = Query(default=25, ge=1, le=200),
                    email: str = Depends(require_admin)):
    from app.services.notify import retention_cutoff
    s = get_settings()
    db = get_db()
    window_start = retention_cutoff(s.log_retention_days)
    query = build_log_query(q, level, source, date_from, date_to, window_start)
    total = await db["error_logs"].count_documents(query)
    order = -1 if sort == "newest" else 1
    cur = (db["error_logs"].find(query).sort("created_at", order)
           .skip((page - 1) * page_size).limit(page_size))
    return {"items": [log_out(d) async for d in cur], "total": total,
            "page": page, "page_size": page_size,
            "retention_days": s.log_retention_days, "window_start": window_start}


@router.get("/stats")
async def log_stats(email: str = Depends(require_admin)):
    from app.services.notify import retention_cutoff
    s = get_settings()
    db = get_db()
    cutoff = retention_cutoff(s.log_retention_days)
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
        "newest": log_out(newest) if newest else None,
        "oldest": log_out(oldest) if oldest else None,
    }


@router.get("/{lid}")
async def log_detail(lid: str, email: str = Depends(require_admin)):
    d = await _find_log(lid)
    if not d:
        raise HTTPException(404, {"error": "Log entry not found"})
    return log_out(d)


@router.delete("")
async def purge_logs(email: str = Depends(require_admin)):
    """Manual early purge (retention TTL + daily sweep handle the normal case)."""
    db = get_db()
    res = await db["error_logs"].delete_many({})
    await audit(email, "LOGS_PURGE", "error_logs", {"deleted": res.deleted_count})
    return {"ok": True, "deleted": res.deleted_count}
