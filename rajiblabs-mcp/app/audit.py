from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from app.database import get_db

logger = logging.getLogger(__name__)


async def audit_log(
    tool_name: str,
    agent_id: str,
    arguments: dict,
    result: dict,
    duration_ms: float = 0.0,
    permission_granted: bool = True,
    error: str | None = None,
) -> None:
    if not permission_granted and not error:
        error = "permission_denied"

    log_doc = {
        "tool_name": tool_name,
        "agent_id": agent_id,
        "arguments": {k: v for k, v in arguments.items() if k not in ("api_key", "admin_key")},
        "success": error is None,
        "error": error,
        "duration_ms": round(duration_ms, 2),
        "permission_granted": permission_granted,
        "timestamp": datetime.now(timezone.utc),
    }

    try:
        db = get_db()
        await db.mcp_audit_log.insert_one(log_doc)
    except Exception as e:
        logger.warning("Audit log failed: %s", e)


async def record_tool_usage(tool_name: str, agent_id: str, success: bool, duration_ms: float) -> None:
    try:
        db = get_db()
        await db.mcp_tool_usage.insert_one(
            {
                "tool_name": tool_name,
                "agent_id": agent_id,
                "success": success,
                "duration_ms": round(duration_ms, 2),
                "timestamp": datetime.now(timezone.utc),
            }
        )
    except Exception as e:
        logger.debug("Tool usage record failed: %s", e)


async def get_audit_logs(
    tool_name: str | None = None,
    agent_id: str | None = None,
    limit: int = 50,
) -> list[dict]:
    db = get_db()
    query: dict[str, Any] = {}
    if tool_name:
        query["tool_name"] = tool_name
    if agent_id:
        query["agent_id"] = agent_id
    cursor = db.mcp_audit_log.find(query).sort("timestamp", -1).limit(limit)
    return [doc async for doc in cursor]


async def get_tool_usage_stats() -> list[dict]:
    db = get_db()
    pipeline = [
        {"$group": {
            "_id": "$tool_name",
            "count": {"$sum": 1},
            "success_count": {"$sum": {"$cond": ["$success", 1, 0]}},
            "avg_duration_ms": {"$avg": "$duration_ms"},
        }},
        {"$sort": {"count": -1}},
    ]
    cursor = db.mcp_tool_usage.aggregate(pipeline)
    return [doc async for doc in cursor]
