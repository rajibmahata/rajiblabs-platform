from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any

from bson import ObjectId

from app.database import get_db

logger = logging.getLogger(__name__)


def _oid_str(obj: Any) -> str | None:
    if obj is None:
        return None
    if isinstance(obj, str):
        return obj
    if isinstance(obj, ObjectId):
        return str(obj)
    return str(obj)


def _content_hash(data: dict) -> str:
    serialized = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode()).hexdigest()


async def create_version(
    entity_type: str,
    entity_id: str,
    current_content: dict,
    agent_id: str = "system",
    reason: str = "",
    validation_score: float = 0.0,
) -> dict | None:
    db = get_db()
    existing = await db.content_versions.find_one(
        {"entity_type": entity_type, "entity_id": entity_id},
        sort=[("version", -1)],
    )
    version = (existing["version"] + 1) if existing else 1

    version_doc = {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "version": version,
        "previous_content": current_content,
        "content_hash": _content_hash(current_content),
        "agent_id": agent_id,
        "reason": reason,
        "validation_score": validation_score,
        "created_at": datetime.now(timezone.utc),
    }

    result = await db.content_versions.insert_one(version_doc)
    version_doc["_id"] = _oid_str(result.inserted_id)
    return version_doc


async def rollback_to_version(
    entity_type: str,
    entity_id: str,
    version: int,
    agent_id: str = "system",
) -> dict | None:
    db = get_db()
    version_doc = await db.content_versions.find_one(
        {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "version": version,
        }
    )
    if not version_doc:
        return None

    collection_map = {
        "project": "projects",
        "profile": "profiles",
        "product": "products",
        "portfolio": "portfolio",
        "skill": "skills",
        "resume": "resumes",
        "knowledge": "knowledge_documents",
        "website_content": "website_contents",
    }
    target_collection = collection_map.get(entity_type)
    if not target_collection:
        return None

    await db[target_collection].update_one(
        {"_id": ObjectId(entity_id)},
        {"$set": version_doc["previous_content"]},
    )

    await create_version(
        entity_type=entity_type,
        entity_id=entity_id,
        current_content=version_doc["previous_content"],
        agent_id=agent_id,
        reason=f"Rollback to version {version}",
    )

    return {
        "restored_version": version,
        "entity_type": entity_type,
        "entity_id": entity_id,
    }


async def get_version_history(
    entity_type: str,
    entity_id: str,
    limit: int = 10,
) -> list[dict]:
    db = get_db()
    cursor = db.content_versions.find(
        {"entity_type": entity_type, "entity_id": entity_id}
    ).sort("version", -1).limit(limit)
    results = []
    async for doc in cursor:
        doc["_id"] = _oid_str(doc["_id"])
        if "previous_content" in doc:
            doc.pop("previous_content", None)
        results.append(doc)
    return results


async def get_version_content(
    entity_type: str,
    entity_id: str,
    version: int,
) -> dict | None:
    db = get_db()
    doc = await db.content_versions.find_one(
        {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "version": version,
        }
    )
    if doc:
        doc["_id"] = _oid_str(doc["_id"])
    return doc


async def record_change(
    entity_type: str,
    entity_id: str,
    change_type: str,
    before: dict | None,
    after: dict | None,
    agent_id: str = "system",
    source: str = "",
) -> None:
    db = get_db()
    change_doc = {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "change_type": change_type,
        "before": before,
        "after": after,
        "agent_id": agent_id,
        "source": source,
        "created_at": datetime.now(timezone.utc),
    }
    await db.content_changes.insert_one(change_doc)


async def get_change_history(
    entity_type: str,
    entity_id: str,
    limit: int = 20,
) -> list[dict]:
    db = get_db()
    cursor = db.content_changes.find(
        {"entity_type": entity_type, "entity_id": entity_id}
    ).sort("created_at", -1).limit(limit)
    return [doc async for doc in cursor]
