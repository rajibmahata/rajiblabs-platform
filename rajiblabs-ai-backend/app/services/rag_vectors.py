"""Vector-store abstraction — Qdrant behind a clean interface (§7).

Application code must use VectorStore, never Qdrant APIs directly.
MongoDB remains the source of truth; vectors are a derived index.
Point IDs are deterministic (uuid5 of document+index) so re-ingestion
replaces rather than duplicates vectors (versioning, §27).
"""
import logging
import uuid

from app.config import get_settings

log = logging.getLogger("rajiblabs")


def point_id(document_id: str, chunk_index: int) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{document_id}:{chunk_index}"))


class VectorStore:
    """Interface. Methods raise VectorStoreError when the store is down —
    callers must degrade gracefully (keyword fallback), never 500."""

    async def upsert_chunks(self, chunks: list[dict]) -> int:
        """Upsert [{point_id, vector, payload}]. Returns count stored."""
        raise NotImplementedError

    async def search(self, vector: list[float], top_k: int = 5,
                     must: dict | None = None) -> list[dict]:
        """Return [{point_id, score, payload}...] filtered by exact-match `must`."""
        raise NotImplementedError

    async def delete_document(self, document_id: str) -> int:
        """Remove all points for a document. Returns count removed."""
        raise NotImplementedError

    async def delete_collection(self) -> None:
        raise NotImplementedError

    async def health_check(self) -> dict:
        """{ok, points_count?, error?} — never raises."""
        raise NotImplementedError


class VectorStoreError(Exception):
    pass


class QdrantVectorStore(VectorStore):
    def __init__(self):
        s = get_settings()
        self.url = s.qdrant_url
        self.api_key = s.qdrant_api_key or None
        self.collection = s.qdrant_collection
        self.dim = s.embedding_dim or 1536
        self._client = None

    def _client_or_raise(self):
        if self._client is None:
            try:
                from qdrant_client import AsyncQdrantClient
            except Exception as e:
                raise VectorStoreError(f"qdrant-client unavailable: {e}")
            try:
                self._client = AsyncQdrantClient(url=self.url, api_key=self.api_key,
                                                 timeout=15)
            except Exception as e:
                raise VectorStoreError(f"qdrant connect failed: {e}")
        return self._client

    async def _ensure_collection(self, client) -> None:
        try:
            from qdrant_client.models import Distance, VectorParams
            exists = await client.collection_exists(self.collection)
            if not exists:
                await client.create_collection(
                    self.collection,
                    vectors_config=VectorParams(size=self.dim, distance=Distance.COSINE))
        except Exception as e:
            raise VectorStoreError(f"collection init failed: {e}")

    async def upsert_chunks(self, chunks: list[dict]) -> int:
        if not chunks:
            return 0
        from qdrant_client.models import PointStruct
        client = self._client_or_raise()
        await self._ensure_collection(client)
        try:
            points = [PointStruct(id=c["point_id"], vector=c["vector"],
                                  payload=c.get("payload", {})) for c in chunks]
            # Qdrant caps batch sizes; stay conservative.
            for i in range(0, len(points), 100):
                await client.upsert(self.collection, points[i:i + 100])
            return len(points)
        except Exception as e:
            raise VectorStoreError(f"upsert failed: {e}")

    async def search(self, vector: list[float], top_k: int = 5,
                     must: dict | None = None) -> list[dict]:
        from qdrant_client.models import FieldCondition, Filter, MatchValue
        client = self._client_or_raise()
        try:
            flt = None
            if must:
                flt = Filter(must=[FieldCondition(key=k, match=MatchValue(value=v))
                                   for k, v in must.items()])
            # query_points is the current API; fall back to search for older servers.
            if hasattr(client, "query_points"):
                res = await client.query_points(
                    self.collection, query=vector, limit=top_k,
                    query_filter=flt, with_payload=True)
                pts = res.points or []
                return [{"point_id": str(p.id), "score": float(p.score),
                         "payload": dict(p.payload or {})} for p in pts]
            res = await client.search(
                self.collection, query_vector=vector, limit=top_k,
                query_filter=flt, with_payload=True)
            return [{"point_id": str(p.id), "score": float(p.score),
                     "payload": dict(p.payload or {})} for p in res]
        except Exception as e:
            raise VectorStoreError(f"search failed: {e}")

    async def delete_document(self, document_id: str) -> int:
        from qdrant_client.models import FieldCondition, Filter, MatchValue
        client = self._client_or_raise()
        try:
            await client.delete(
                self.collection,
                points_selector=Filter(must=[FieldCondition(
                    key="document_id", match=MatchValue(value=document_id))]))
            return 1
        except Exception as e:
            raise VectorStoreError(f"delete failed: {e}")

    async def delete_collection(self) -> None:
        client = self._client_or_raise()
        try:
            await client.delete_collection(self.collection)
        except Exception as e:
            raise VectorStoreError(f"delete_collection failed: {e}")
        self._client = None

    async def health_check(self) -> dict:
        try:
            client = self._client_or_raise()
            info = await client.get_collection(self.collection)
            return {"ok": True, "points_count": info.points_count or 0,
                    "collection": self.collection, "url": self.url}
        except Exception as e:
            return {"ok": False, "error": str(e)[:200], "url": self.url}


def get_vector_store() -> VectorStore:
    return QdrantVectorStore()
