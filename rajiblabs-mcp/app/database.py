from __future__ import annotations

import logging
from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import settings

logger = logging.getLogger(__name__)

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


async def connect_db() -> None:
    global _client, _db
    _client = AsyncIOMotorClient(settings.DATABASE_URL)
    _db = _client[settings.MONGO_DB_NAME]
    await _ensure_indexes()
    logger.info("MongoDB connected: %s", settings.MONGO_DB_NAME)


async def disconnect_db() -> None:
    global _client, _db
    if _client:
        _client.close()
        _client = None
        _db = None
        logger.info("MongoDB disconnected")


def get_db() -> AsyncIOMotorDatabase:
    if _db is None:
        raise RuntimeError("Database not initialized")
    return _db


async def _ensure_indexes() -> None:
    db = get_db()
    await db.mcp_audit_log.create_index([("timestamp", -1)])
    await db.mcp_audit_log.create_index([("tool_name", 1)])
    await db.mcp_audit_log.create_index([("agent_id", 1)])
    await db.content_versions.create_index([("entity_type", 1), ("entity_id", 1)])
    await db.content_versions.create_index([("created_at", -1)])
    await db.content_changes.create_index([("entity_type", 1), ("entity_id", 1)])
    await db.content_changes.create_index([("created_at", -1)])
    await db.content_relationships.create_index([("source_type", 1), ("source_id", 1)])
    await db.content_relationships.create_index([("target_type", 1), ("target_id", 1)])
    await db.skill_evidence.create_index([("skill_name", 1)])
    await db.skill_evidence.create_index([("source_type", 1), ("source_id", 1)])
    await db.mcp_tool_usage.create_index([("tool_name", 1)])
    await db.mcp_tool_usage.create_index([("timestamp", -1)])
    logger.info("MCP indexes created")
