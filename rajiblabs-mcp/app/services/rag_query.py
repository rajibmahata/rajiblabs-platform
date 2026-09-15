from __future__ import annotations

import logging
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)


async def query_rag(question: str, top_k: int = 5) -> dict:
    try:
        from app.database import get_db
        db = get_db()

        results = []
        async for doc in db.knowledge_documents.find(
            {"$text": {"$search": question}}
        ).limit(top_k):
            results.append({
                "id": str(doc.get("_id", "")),
                "content": doc.get("content", ""),
                "source_type": doc.get("source_type", ""),
                "score": 1.0,
            })

        if not results:
            async for doc in db.knowledge_documents.find(
                {"content": {"$regex": question, "$options": "i"}}
            ).limit(top_k):
                results.append({
                    "id": str(doc.get("_id", "")),
                    "content": doc.get("content", ""),
                    "source_type": doc.get("source_type", ""),
                    "score": 0.5,
                })

        return {
            "success": True,
            "results": results,
            "count": len(results),
            "query": question,
        }
    except Exception as e:
        logger.warning("RAG query failed: %s", e)
        return {"success": False, "results": [], "count": 0, "error": str(e)}


async def index_to_qdrant(document_id: str, content: str, metadata: dict | None = None) -> bool:
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.models import PointStruct

        client = QdrantClient(url=settings.QDRANT_URL)
        collection = "rajiblabs_knowledge"

        point = PointStruct(
            id=hash(document_id) % (2**63),
            vector=[0.0] * 1536,
            payload={"document_id": document_id, "content": content, **(metadata or {})},
        )

        client.upsert(collection_name=collection, points=[point])
        return True
    except Exception as e:
        logger.warning("Qdrant indexing failed: %s", e)
        return False
