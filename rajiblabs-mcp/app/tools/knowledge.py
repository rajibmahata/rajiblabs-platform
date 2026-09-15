"""Knowledge MCP tools — RAG knowledge management.

MongoDB remains source of truth. Qdrant remains vector retrieval layer.
Never make Qdrant the authoritative database.
"""

import re
from datetime import datetime, timezone

from app.database import get_db, utcnow
from app.tools import mcp_tool, _oid_str, _clean_secret_keys


@mcp_tool("search_knowledge", "Search the knowledge base",
          "knowledge", permission="public")
async def search_knowledge(query: str, top_k: int = 6) -> dict:
    """Search knowledge using RAG retrieval."""
    db = get_db()
    # Try Qdrant first, fall back to MongoDB text search
    try:
        from app.services import rag_query as _rq
        hits = await _rq.retrieve(query[:500], top_k=min(top_k, 10))
        results = [{
            "title": h.get("title", ""),
            "url": h.get("url"),
            "source_type": h.get("source_type", ""),
            "score": h.get("score", 0),
            "snippet": (h.get("content") or "")[:600],
        } for h in hits]
        return {"results": results, "count": len(results), "source": "qdrant"}
    except Exception:
        pass

    # Fallback: MongoDB text search
    docs = await db["knowledge"].find(
        {"$text": {"$search": query[:200]}}).limit(top_k).to_list(top_k)
    results = [{
        "title": d.get("title", ""),
        "url": d.get("url"),
        "source_type": d.get("source_type", ""),
        "snippet": (d.get("content") or "")[:600],
    } for d in docs]
    return {"results": results, "count": len(results), "source": "mongodb"}


@mcp_tool("get_knowledge", "Get knowledge entries by source type",
          "knowledge", permission="agent")
async def get_knowledge(source_type: str | None = None,
                        limit: int = 50) -> dict:
    """Retrieve knowledge entries, optionally filtered by source type."""
    db = get_db()
    query = {}
    if source_type:
        query["source_type"] = source_type
    docs = await db["knowledge"].find(query).sort(
        "created_at", -1).limit(limit).to_list(limit)
    return {"entries": [_oid_str(d) for d in docs], "count": len(docs)}


@mcp_tool("validate_knowledge", "Validate knowledge for staleness and accuracy",
          "knowledge", permission="agent")
async def validate_knowledge() -> dict:
    """Check knowledge base for stale, duplicate, or invalid entries."""
    db = get_db()
    issues = []

    # Check for stale entries (older than 90 days with no update)
    cutoff = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0)

    # Count by source type
    pipeline = [
        {"$group": {"_id": "$source_type", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
    by_source = await db["knowledge"].aggregate(pipeline).to_list(50)

    # Check for duplicates by title
    dup_pipeline = [
        {"$group": {"_id": "$title", "count": {"$sum": 1},
                     "ids": {"$push": "$_id"}}},
        {"$match": {"count": {"$gt": 1}}},
    ]
    duplicates = await db["knowledge"].aggregate(dup_pipeline).to_list(50)
    for dup in duplicates:
        issues.append({
            "type": "duplicate",
            "title": dup["_id"],
            "count": dup["count"],
            "ids": [str(i) for i in dup["ids"]],
        })

    total = await db["knowledge"].count_documents({})

    return {
        "total_entries": total,
        "by_source": [{"source": s["_id"], "count": s["count"]}
                      for s in by_source],
        "duplicates_found": len(duplicates),
        "issues": issues[:20],
    }


@mcp_tool("index_knowledge", "Re-index a knowledge entry into Qdrant",
          "knowledge", permission="admin")
async def index_knowledge(entry_id: str) -> dict:
    """Re-index a specific knowledge entry into the vector store."""
    db = get_db()
    from bson import ObjectId
    try:
        entry = await db["knowledge"].find_one({"_id": ObjectId(entry_id)})
    except Exception:
        return {"error": f"Invalid entry ID: {entry_id}"}

    if not entry:
        return {"error": f"Knowledge entry not found: {entry_id}"}

    # Index into Qdrant
    try:
        from app.services import rag_query as _rq
        await _rq.index_document(entry)
        return {"status": "indexed", "entry_id": entry_id,
                "title": entry.get("title", "")}
    except Exception as e:
        return {"error": f"Indexing failed: {str(e)[:200]}"}


@mcp_tool("detect_stale_knowledge", "Find knowledge entries that may be outdated",
          "knowledge", permission="agent")
async def detect_stale_knowledge(days_threshold: int = 90) -> dict:
    """Find knowledge entries older than threshold days."""
    db = get_db()
    from datetime import timedelta
    cutoff = datetime.now(timezone.utc) - timedelta(days=days_threshold)

    stale = await db["knowledge"].find(
        {"updated_at": {"$lt": cutoff}}).sort(
        "updated_at", 1).limit(50).to_list(50)

    return {
        "stale_count": len(stale),
        "threshold_days": days_threshold,
        "entries": [{"id": str(e["_id"]), "title": e.get("title", ""),
                     "updated_at": e.get("updated_at"),
                     "source_type": e.get("source_type", "")}
                    for e in stale],
    }
