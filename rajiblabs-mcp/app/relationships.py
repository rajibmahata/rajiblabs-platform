from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from app.database import get_db

logger = logging.getLogger(__name__)

COLLECTION_MAP = {
    "project": "projects",
    "profile": "profiles",
    "product": "products",
    "portfolio": "portfolio",
    "skill": "skills",
    "resume": "resumes",
    "knowledge": "knowledge_documents",
    "website_content": "website_contents",
    "experience": "experience",
    "domain": "professional_domains",
    "github_repository": "github_repositories",
}


async def add_relationship(
    source_type: str,
    source_id: str,
    target_type: str,
    target_id: str,
    relationship_type: str,
    metadata: dict | None = None,
) -> dict | None:
    db = get_db()
    existing = await db.content_relationships.find_one(
        {
            "source_type": source_type,
            "source_id": source_id,
            "target_type": target_type,
            "target_id": target_id,
            "relationship_type": relationship_type,
        }
    )
    if existing:
        return None

    rel_doc = {
        "source_type": source_type,
        "source_id": source_id,
        "target_type": target_type,
        "target_id": target_id,
        "relationship_type": relationship_type,
        "metadata": metadata or {},
        "created_at": datetime.now(timezone.utc),
    }
    result = await db.content_relationships.insert_one(rel_doc)
    rel_doc["_id"] = str(result.inserted_id)
    return rel_doc


async def get_relationships(
    entity_type: str,
    entity_id: str,
    direction: str = "both",
) -> list[dict]:
    db = get_db()
    query: dict[str, Any] = {}
    if direction == "outgoing":
        query = {"source_type": entity_type, "source_id": entity_id}
    elif direction == "incoming":
        query = {"target_type": entity_type, "target_id": entity_id}
    else:
        query = {
            "$or": [
                {"source_type": entity_type, "source_id": entity_id},
                {"target_type": entity_type, "target_id": entity_id},
            ]
        }

    cursor = db.content_relationships.find(query)
    return [doc async for doc in cursor]


async def remove_relationship(
    source_type: str,
    source_id: str,
    target_type: str,
    target_id: str,
    relationship_type: str,
) -> bool:
    db = get_db()
    result = await db.content_relationships.delete_one(
        {
            "source_type": source_type,
            "source_id": source_id,
            "target_type": target_type,
            "target_id": target_id,
            "relationship_type": relationship_type,
        }
    )
    return result.deleted_count > 0


async def get_content_graph(entity_type: str, entity_id: str) -> dict:
    relationships = await get_relationships(entity_type, entity_id)
    graph: dict[str, Any] = {
        "entity": {"type": entity_type, "id": entity_id},
        "relationships": [],
    }

    for rel in relationships:
        graph["relationships"].append(
            {
                "type": rel["relationship_type"],
                "direction": "outgoing" if rel["source_type"] == entity_type else "incoming",
                "target": {
                    "type": rel["target_type"] if rel["source_type"] == entity_type else rel["source_type"],
                    "id": rel["target_id"] if rel["source_type"] == entity_type else rel["source_id"],
                },
            }
        )

    return graph


async def sync_relationships_from_source(entity_type: str, entity_id: str) -> int:
    db = get_db()
    count = 0

    if entity_type == "project":
        project = await db.projects.find_one({"_id": entity_id})
        if not project:
            return 0

        for skill_name in project.get("skills", []):
            skill = await db.skills.find_one({"name": skill_name})
            if skill:
                added = await add_relationship(
                    "project", entity_id,
                    "skill", str(skill["_id"]),
                    "uses_skill",
                )
                if added:
                    count += 1

        if project.get("github_url"):
            repo = await db.github_repositories.find_one(
                {"html_url": project["github_url"]}
            )
            if repo:
                added = await add_relationship(
                    "project", entity_id,
                    "github_repository", str(repo["_id"]),
                    "has_repository",
                )
                if added:
                    count += 1

    elif entity_type == "skill":
        skill = await db.skills.find_one({"_id": entity_id})
        if not skill:
            return 0

        async for proj in db.projects.find({"skills": skill["name"]}):
            added = await add_relationship(
                "skill", entity_id,
                "project", str(proj["_id"]),
                "used_in_project",
            )
            if added:
                count += 1

    return count
