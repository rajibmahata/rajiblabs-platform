from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from app.database import get_db
from app.tools import mcp_tool, _oid_str
from app.versioning import create_version

logger = logging.getLogger(__name__)


@mcp_tool(
    name="preview_content",
    description="Preview content before publishing (dry run).",
    category="publishing",
    permission="read",
)
async def preview_content(
    entity_type: str, entity_id: str, agent_id: str = "anonymous"
) -> dict:
    db = get_db()
    from bson import ObjectId

    collection_map = {
        "project": "projects",
        "profile": "profiles",
        "product": "products",
    }
    collection = collection_map.get(entity_type)
    if not collection:
        return {"success": False, "error": {"code": "INVALID_TYPE", "message": f"Unknown type: {entity_type}"}}

    doc = await db[collection].find_one({"_id": ObjectId(entity_id)})
    if not doc:
        return {"success": False, "error": {"code": "NOT_FOUND", "message": "Entity not found"}}

    doc["_id"] = _oid_str(doc["_id"])
    return {
        "success": True,
        "data": {"entity_type": entity_type, "entity_id": entity_id, "preview": doc, "status": "preview"},
        "sources": [collection],
        "confidence": 1.0,
    }


@mcp_tool(
    name="publish_content",
    description="Publish content (set status to published, create version snapshot).",
    category="publishing",
    permission="publish",
)
async def publish_content(
    entity_type: str, entity_id: str, reason: str = "", agent_id: str = "anonymous"
) -> dict:
    db = get_db()
    from bson import ObjectId

    collection_map = {
        "project": "projects",
        "profile": "profiles",
        "product": "products",
    }
    collection = collection_map.get(entity_type)
    if not collection:
        return {"success": False, "error": {"code": "INVALID_TYPE", "message": f"Unknown type: {entity_type}"}}

    doc = await db[collection].find_one({"_id": ObjectId(entity_id)})
    if not doc:
        return {"success": False, "error": {"code": "NOT_FOUND", "message": "Entity not found"}}

    before = {k: v for k, v in doc.items() if k != "_id"}
    await create_version(entity_type, entity_id, before, agent_id, reason or "Publish")

    await db[collection].update_one(
        {"_id": ObjectId(entity_id)},
        {"$set": {"status": "published", "published_at": datetime.now(timezone.utc)}},
    )

    return {
        "success": True,
        "data": {"entity_type": entity_type, "entity_id": entity_id, "status": "published"},
        "sources": [collection],
        "changed": True,
        "confidence": 1.0,
    }


@mcp_tool(
    name="unpublish_content",
    description="Unpublish content (set status to draft).",
    category="publishing",
    permission="publish",
)
async def unpublish_content(
    entity_type: str, entity_id: str, agent_id: str = "anonymous"
) -> dict:
    db = get_db()
    from bson import ObjectId

    collection_map = {
        "project": "projects",
        "profile": "profiles",
        "product": "products",
    }
    collection = collection_map.get(entity_type)
    if not collection:
        return {"success": False, "error": {"code": "INVALID_TYPE", "message": f"Unknown type: {entity_type}"}}

    await db[collection].update_one(
        {"_id": ObjectId(entity_id)},
        {"$set": {"status": "draft"}},
    )

    return {
        "success": True,
        "data": {"entity_type": entity_type, "entity_id": entity_id, "status": "draft"},
        "sources": [collection],
        "changed": True,
        "confidence": 1.0,
    }


@mcp_tool(
    name="rollback_content",
    description="Rollback content to a previous version.",
    category="publishing",
    permission="delete",
)
async def rollback_content(
    entity_type: str, entity_id: str, version: int, agent_id: str = "anonymous"
) -> dict:
    from app.versioning import rollback_to_version

    result = await rollback_to_version(entity_type, entity_id, version, agent_id)
    if not result:
        return {"success": False, "error": {"code": "NOT_FOUND", "message": "Version not found"}}

    return {
        "success": True,
        "data": result,
        "changed": True,
        "confidence": 1.0,
    }
