"""MCP audit log router."""

from fastapi import APIRouter, Depends, Query

from app.auth import verify_admin_key
from app.database import get_db

router = APIRouter(prefix="/api/mcp/audit", tags=["mcp-audit"])


@router.get("/logs")
async def get_audit_logs(
    tool: str | None = Query(None),
    agent: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    api_key: str = Depends(verify_admin_key),
):
    """Get MCP audit logs. Admin only."""
    db = get_db()
    query = {}
    if tool:
        query["tool"] = tool
    if agent:
        query["agent"] = agent

    logs = await db["mcp_audit_log"].find(query).sort(
        "started_at", -1).limit(limit).to_list(limit)
    return {"logs": logs, "count": len(logs)}


@router.get("/stats")
async def get_audit_stats(api_key: str = Depends(verify_admin_key)):
    """Get MCP tool usage statistics. Admin only."""
    db = get_db()
    pipeline = [
        {"$group": {
            "_id": "$tool",
            "count": {"$sum": 1},
            "avg_duration_ms": {"$avg": "$duration_ms"},
            "errors": {"$sum": {"$cond": [{"$eq": ["$status", "error"]}, 1, 0]}},
        }},
        {"$sort": {"count": -1}},
    ]
    stats = await db["mcp_audit_log"].aggregate(pipeline).to_list(50)
    return {"stats": stats}
