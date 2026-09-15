"""RajibLabs Content Intelligence MCP — FastAPI REST wrapper.

Provides HTTP REST endpoints for non-MCP clients (frontend, admin UI).
The MCP SDK handles the official MCP protocol (SSE/streamable-http).
"""

from __future__ import annotations

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Depends, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.config import settings
from app.database import connect_db, disconnect_db
from app.redis import connect_redis, disconnect_redis
from app.tools import TOOL_REGISTRY
from app.permissions import ROLE_PERMISSIONS, TOOL_PERMISSIONS, has_permission
from app.audit import get_audit_logs, get_tool_usage_stats

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("rajiblabs-mcp-rest")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting RajibLabs MCP REST API")
    await connect_db()
    await connect_redis()
    logger.info("MCP REST API ready — %d tools registered", len(TOOL_REGISTRY))
    yield
    await disconnect_redis()
    await disconnect_db()
    logger.info("MCP REST API stopped")


app = FastAPI(
    title="RajibLabs Content Intelligence MCP",
    version="2.0.0",
    description="REST API for RajibLabs MCP Content Intelligence Platform",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class MCPResponse(BaseModel):
    success: bool
    data: Any = None
    error: Any = None
    sources: list[str] = []
    confidence: float = 0.0
    changed: bool = False


class ToolCallRequest(BaseModel):
    arguments: dict[str, Any] = {}
    agent_id: str = "anonymous"


def _get_agent_id(request: Request) -> str:
    return request.headers.get("X-Agent-ID", "anonymous")


@app.get("/health")
async def health():
    from app.database import get_db
    from motor.motor_asyncio import AsyncIOMotorClient

    mongo_ok = False
    redis_ok = False
    qdrant_ok = False

    try:
        client = AsyncIOMotorClient(settings.DATABASE_URL, serverSelectionTimeoutMS=2000)
        await client.admin.command("ping")
        mongo_ok = True
        client.close()
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

    status = "ok" if mongo_ok else "degraded"
    return {
        "status": status,
        "service": "rajiblabs-mcp",
        "version": "2.0.0",
        "mongo": "ok" if mongo_ok else "error",
        "qdrant": "ok" if qdrant_ok else "unavailable",
        "redis": "ok" if redis_ok else "unavailable",
        "tools_registered": len(TOOL_REGISTRY),
    }


@app.get("/tools")
async def list_tools():
    tools = []
    for name, info in TOOL_REGISTRY.items():
        tools.append({
            "name": name,
            "description": info["description"],
            "category": info["category"],
            "permission": info["permission"],
        })
    return {"tools": tools, "count": len(tools)}


@app.get("/tools/{category}")
async def list_tools_by_category(category: str):
    tools = []
    for name, info in TOOL_REGISTRY.items():
        if info["category"] == category:
            tools.append({
                "name": name,
                "description": info["description"],
                "permission": info["permission"],
            })
    return {"category": category, "tools": tools, "count": len(tools)}


@app.get("/permissions")
async def list_permissions():
    return {
        "roles": {role: [p.value for p in perms] for role, perms in ROLE_PERMISSIONS.items()},
        "tool_permissions": {tool: perm.value for tool, perm in TOOL_PERMISSIONS.items()},
    }


@app.post("/tool/{tool_name}")
async def call_tool(tool_name: str, request: ToolCallRequest):
    if tool_name not in TOOL_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

    agent_id = request.agent_id
    if not has_permission(agent_id, tool_name):
        raise HTTPException(status_code=403, detail=f"Permission denied for role '{agent_id}'")

    tool_info = TOOL_REGISTRY[tool_name]
    fn = tool_info["function"]

    start = time.monotonic()
    try:
        result = await fn(agent_id=agent_id, **request.arguments)
        duration = (time.monotonic() - start) * 1000
        result["_duration_ms"] = round(duration, 2)
        return result
    except Exception as e:
        duration = (time.monotonic() - start) * 1000
        logger.exception("Tool %s failed", tool_name)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/audit/logs")
async def audit_logs(
    tool_name: str | None = None,
    agent_id: str | None = None,
    limit: int = Query(50, ge=1, le=200),
):
    logs = await get_audit_logs(tool_name, agent_id, limit)
    for log in logs:
        if hasattr(log.get("_id"), "isoformat"):
            log["_id"] = str(log["_id"])
        if hasattr(log.get("timestamp"), "isoformat"):
            log["timestamp"] = log["timestamp"].isoformat()
    return {"logs": logs, "count": len(logs)}


@app.get("/audit/stats")
async def audit_stats():
    stats = await get_tool_usage_stats()
    return {"stats": stats}
