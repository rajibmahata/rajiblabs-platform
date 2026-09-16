from __future__ import annotations

import logging
from typing import Any

from app.database import get_db
from app.tools import mcp_tool, TOOL_REGISTRY
from app.config import settings

logger = logging.getLogger(__name__)


@mcp_tool(
    name="system_health",
    description="System health check — MongoDB, Qdrant, Redis, tool registry status.",
    category="system",
    permission="read",
)
async def system_health(agent_id: str = "anonymous") -> dict:
    mongo_ok = False
    redis_ok = False
    qdrant_ok = False

    try:
        db = get_db()
        await db.command("ping")
        mongo_ok = True
    except Exception:
        pass

    try:
        from app.redis import get_redis
        r = get_redis()
        if r:
            await r.ping()
            redis_ok = True
    except Exception:
        pass

    try:
        from qdrant_client import QdrantClient
        qc = QdrantClient(url=settings.QDRANT_URL, timeout=2)
        qc.get_collections()
        qdrant_ok = True
    except Exception:
        pass

    return {
        "success": True,
        "data": {
            "mongo": "ok" if mongo_ok else "error",
            "qdrant": "ok" if qdrant_ok else "unavailable",
            "redis": "ok" if redis_ok else "unavailable",
            "tools_registered": len(TOOL_REGISTRY),
            "status": "healthy" if mongo_ok else "degraded",
        },
        "confidence": 1.0,
    }


@mcp_tool(
    name="system_agent_status",
    description="Get status of registered agents and recent runs.",
    category="system",
    permission="read",
)
async def system_agent_status(agent_id: str = "anonymous") -> dict:
    db = get_db()

    recent_runs = []
    cursor = db.agent_runs.find().sort("started_at", -1).limit(10)
    async for run in cursor:
        run.pop("_id", None)
        recent_runs.append({
            "run_id": run.get("run_id", ""),
            "status": run.get("status", ""),
            "task_type": run.get("task_type", ""),
            "started_at": str(run.get("started_at", "")),
        })

    return {
        "success": True,
        "data": {"recent_runs": recent_runs, "count": len(recent_runs)},
        "confidence": 1.0,
    }


@mcp_tool(
    name="system_rag_status",
    description="Get RAG system status — document count, chunk count, index status.",
    category="system",
    permission="read",
)
async def system_rag_status(agent_id: str = "anonymous") -> dict:
    db = get_db()
    doc_count = await db.knowledge_documents.count_documents({})
    chunk_count = await db.knowledge_chunks.count_documents({})

    return {
        "success": True,
        "data": {"documents": doc_count, "chunks": chunk_count, "status": "ok"},
        "sources": ["knowledge_documents", "knowledge_chunks"],
        "confidence": 0.9,
    }


@mcp_tool(
    name="system_cache_status",
    description="Get Redis cache status.",
    category="system",
    permission="read",
)
async def system_cache_status(agent_id: str = "anonymous") -> dict:
    try:
        from app.redis import get_redis
        r = get_redis()
        if r:
            info = await r.info("memory")
            return {
                "success": True,
                "data": {
                    "status": "connected",
                    "memory_used": info.get("used_memory_human", "unknown"),
                    "keys": info.get("db0", {}).get("keys", 0) if isinstance(info.get("db0"), dict) else 0,
                },
                "confidence": 1.0,
            }
    except Exception:
        pass
    return {
        "success": True,
        "data": {"status": "disconnected", "memory_used": "0", "keys": 0},
        "confidence": 0.5,
    }


@mcp_tool(
    name="system_mcp_status",
    description="Get MCP server status — tool count, uptime, configuration.",
    category="system",
    permission="read",
)
async def system_mcp_status(agent_id: str = "anonymous") -> dict:
    return {
        "success": True,
        "data": {
            "version": "2.0.0",
            "tools": len(TOOL_REGISTRY),
            "transport": settings.MCP_TRANSPORT,
            "port": settings.MCP_PORT,
            "categories": list(set(t["category"] for t in TOOL_REGISTRY.values())),
        },
        "confidence": 1.0,
    }
