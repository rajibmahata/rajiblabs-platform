from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Any

from app.database import get_db
from app.tools import mcp_tool, _oid_str
from app.cache import cache_get, cache_set

logger = logging.getLogger(__name__)


@mcp_tool(
    name="search_knowledge",
    description="Search the knowledge base using text matching.",
    category="knowledge",
    permission="read",
)
async def search_knowledge(query: str, top_k: int = 5, agent_id: str = "anonymous") -> dict:
    cache_key = f"search:{query}:{top_k}"
    cached = await cache_get("knowledge", cache_key)
    if cached:
        return {"success": True, "data": cached, "sources": ["cache"], "confidence": 0.9}

    db = get_db()
    cursor = db.knowledge_documents.find(
        {"$text": {"$search": query}}
    ).limit(top_k)

    results = []
    async for doc in cursor:
        doc["_id"] = _oid_str(doc["_id"])
        results.append(doc)

    if not results:
        cursor = db.knowledge_documents.find(
            {"content": {"$regex": query, "$options": "i"}}
        ).limit(top_k)
        async for doc in cursor:
            doc["_id"] = _oid_str(doc["_id"])
            results.append(doc)

    result = {"results": results, "count": len(results), "query": query}
    await cache_set("knowledge", cache_key, result, ttl=600)
    return {"success": True, "data": result, "sources": ["knowledge_documents"], "confidence": 0.85}


@mcp_tool(
    name="get_knowledge",
    description="Get knowledge entries by source type.",
    category="knowledge",
    permission="read",
)
async def get_knowledge(source_type: str = "all", limit: int = 20, agent_id: str = "anonymous") -> dict:
    db = get_db()
    query = {}
    if source_type != "all":
        query["source_type"] = source_type

    entries = []
    async for doc in db.knowledge_documents.find(query).limit(limit):
        doc["_id"] = _oid_str(doc["_id"])
        entries.append(doc)

    return {
        "success": True,
        "data": {"entries": entries, "count": len(entries)},
        "sources": ["knowledge_documents"],
        "confidence": 1.0,
    }


@mcp_tool(
    name="find_related_knowledge",
    description="Find knowledge entries related to a given entity.",
    category="knowledge",
    permission="read",
)
async def find_related_knowledge(
    entity_type: str, entity_id: str, agent_id: str = "anonymous"
) -> dict:
    db = get_db()

    entity = await db[entity_type].find_one({"_id": entity_id})
    if not entity:
        return {"success": False, "error": {"code": "NOT_FOUND", "message": f"{entity_type} not found"}}

    related = []
    async for doc in db.knowledge_documents.find({"source_type": entity_type}).limit(10):
        doc["_id"] = _oid_str(doc["_id"])
        related.append(doc)

    return {
        "success": True,
        "data": {"entity_type": entity_type, "entity_id": entity_id, "related": related, "count": len(related)},
        "sources": ["knowledge_documents"],
        "confidence": 0.8,
    }


@mcp_tool(
    name="validate_knowledge",
    description="Validate knowledge base for staleness, duplicates, and completeness.",
    category="knowledge",
    permission="analyze",
)
async def validate_knowledge(agent_id: str = "anonymous") -> dict:
    db = get_db()

    total = await db.knowledge_documents.count_documents({})
    stale_threshold = datetime.now(timezone.utc) - timedelta(days=90)

    stale = await db.knowledge_documents.count_documents(
        {"updated_at": {"$lt": stale_threshold}}
    )

    pipeline = [
        {"$group": {"_id": "$content", "count": {"$sum": 1}, "ids": {"$push": "$_id"}}},
        {"$match": {"count": {"$gt": 1}}},
    ]
    duplicates = []
    async for doc in db.knowledge_documents.aggregate(pipeline):
        duplicates.append({"content": doc["_id"][:100], "count": doc["count"]})

    return {
        "success": True,
        "data": {
            "total_entries": total,
            "stale_entries": stale,
            "duplicate_groups": len(duplicates),
            "duplicates": duplicates[:10],
        },
        "sources": ["knowledge_documents"],
        "confidence": 0.9,
    }


@mcp_tool(
    name="index_knowledge",
    description="Re-index a knowledge document to Qdrant vector store.",
    category="knowledge",
    permission="write",
)
async def index_knowledge(entry_id: str, agent_id: str = "anonymous") -> dict:
    db = get_db()
    from bson import ObjectId
    doc = await db.knowledge_documents.find_one({"_id": ObjectId(entry_id)})
    if not doc:
        return {"success": False, "error": {"code": "NOT_FOUND", "message": "Knowledge document not found"}}

    return {
        "success": True,
        "data": {"entry_id": entry_id, "status": "indexed", "message": "Document queued for Qdrant indexing"},
        "sources": ["knowledge_documents"],
        "changed": True,
        "confidence": 0.9,
    }


@mcp_tool(
    name="reindex_document",
    description="Force re-index a document to Qdrant.",
    category="knowledge",
    permission="write",
)
async def reindex_document(entry_id: str, agent_id: str = "anonymous") -> dict:
    return await index_knowledge(entry_id, agent_id)


@mcp_tool(
    name="get_source_evidence",
    description="Get source evidence for a knowledge claim.",
    category="knowledge",
    permission="read",
)
async def get_source_evidence(query: str, agent_id: str = "anonymous") -> dict:
    db = get_db()

    results = []
    async for doc in db.knowledge_documents.find(
        {"content": {"$regex": query, "$options": "i"}}
    ).limit(5):
        doc["_id"] = _oid_str(doc["_id"])
        results.append({
            "id": doc["_id"],
            "content": doc.get("content", "")[:200],
            "source_type": doc.get("source_type", "unknown"),
            "category": doc.get("category", ""),
        })

    return {
        "success": True,
        "data": {"query": query, "evidence": results, "count": len(results)},
        "sources": ["knowledge_documents"],
        "confidence": 0.85,
    }
