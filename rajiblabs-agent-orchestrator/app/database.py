"""MongoDB connection for the orchestrator."""

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
    logger.info("Orchestrator MongoDB connected")


async def disconnect_db() -> None:
    global _client, _db
    if _client:
        _client.close()
        _client = None
        _db = None


def get_db() -> AsyncIOMotorDatabase:
    if _db is None:
        raise RuntimeError("Database not initialized")
    return _db


async def _ensure_indexes() -> None:
    db = get_db()
    await db.agent_runs.create_index([("run_id", 1)], unique=True)
    await db.agent_runs.create_index([("status", 1)])
    await db.agent_runs.create_index([("task_type", 1)])
    await db.agent_runs.create_index([("started_at", -1)])
    await db.content_improvements.create_index([("entity_type", 1), ("entity_id", 1)])
    await db.content_improvements.create_index([("run_id", 1)])
    await db.quality_scores.create_index([("entity_type", 1), ("entity_id", 1)])
    await db.quality_scores.create_index([("timestamp", -1)])
    await db.agent_issues.create_index([("issue_hash", 1)])
    await db.agent_issues.create_index([("status", 1)])
    logger.info("Orchestrator indexes created")
