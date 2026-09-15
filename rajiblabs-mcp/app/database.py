"""MongoDB connection for MCP server."""

from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings

_client: AsyncIOMotorClient | None = None
_db = None


async def connect_db():
    """Initialize MongoDB connection."""
    global _client, _db
    if _client is None:
        _client = AsyncIOMotorClient(settings.database_url)
        _db = _client[settings.mongo_db_name]
    return _db


async def close_db():
    """Close MongoDB connection."""
    global _client, _db
    if _client:
        _client.close()
        _client = None
        _db = None


def get_db():
    """Get the database instance."""
    if _db is None:
        raise RuntimeError("Database not initialized. Call connect_db() first.")
    return _db


def utcnow() -> datetime:
    """Current UTC time."""
    return datetime.now(timezone.utc)


async def ensure_indexes():
    """Create indexes for MCP collections."""
    db = get_db()

    # Tool usage audit log
    await db["mcp_audit_log"].create_index(
        [("tool", 1), ("started_at", -1)], background=True)
    await db["mcp_audit_log"].create_index(
        [("agent", 1), ("started_at", -1)], background=True)
    await db["mcp_audit_log"].create_index(
        [("status", 1), ("started_at", -1)], background=True)

    # Content versions
    await db["content_versions"].create_index(
        [("entity_type", 1), ("entity_id", 1), ("version", -1)],
        background=True)
    await db["content_versions"].create_index(
        [("created_at", -1)], background=True)

    # MCP tool registry
    await db["mcp_tools"].create_index(
        [("name", 1)], unique=True, background=True)

    # Skill evidence
    await db["skill_evidence"].create_index(
        [("skill", 1), ("category", 1)], background=True)
    await db["skill_evidence"].create_index(
        [("confidence", -1)], background=True)

    # Content intelligence
    await db["content_intelligence"].create_index(
        [("entity_type", 1), ("entity_id", 1)], background=True)
    await db["content_intelligence"].create_index(
        [("last_analyzed", -1)], background=True)
