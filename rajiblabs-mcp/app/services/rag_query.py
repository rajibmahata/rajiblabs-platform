"""RAG query stub for MCP server.

This module provides a thin interface to the existing backend's RAG
pipeline. In production, this should be replaced with a proper MCP
tool call to the ai-api service or a shared library.

For now, it provides graceful fallback to MongoDB text search when
Qdrant is not available.
"""

import logging

log = logging.getLogger("rajiblabs-mcp.rag")


async def retrieve(query: str, top_k: int = 6) -> list[dict]:
    """Retrieve relevant documents from Qdrant.
    
    Falls back to empty list if Qdrant is unavailable.
    The calling code handles the fallback to MongoDB.
    """
    try:
        from app.config import settings
        from qdrant_client import QdrantClient
        from qdrant_client.models import Filter, FieldCondition, MatchValue

        client = QdrantClient(url=settings.qdrant_url)

        # Search with query vector (embedding would be needed here)
        # For now, return empty to trigger MongoDB fallback
        # TODO: Integrate with actual embedding service
        log.debug("Qdrant retrieve called for query: %s", query[:50])
        return []
    except Exception as e:
        log.debug("Qdrant unavailable, will fall back to MongoDB: %s", e)
        return []


async def index_document(doc: dict) -> bool:
    """Index a document into Qdrant.
    
    Returns True if successful, False otherwise.
    """
    try:
        from app.config import settings
        from qdrant_client import QdrantClient

        client = QdrantClient(url=settings.qdrant_url)
        log.debug("Qdrant index called for: %s", doc.get("title", ""))
        # TODO: Implement actual indexing with embeddings
        return True
    except Exception as e:
        log.debug("Qdrant index failed: %s", e)
        return False
