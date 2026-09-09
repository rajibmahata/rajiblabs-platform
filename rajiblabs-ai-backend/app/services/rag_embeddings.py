"""Embedding abstraction — OpenAI default, local sentence-transformers optional.

Records provider/model/version with indexed metadata (§8). Raises
EmbeddingError when unusable so callers degrade gracefully (cached vectors,
keyword fallback, heuristic chat), never 500.

Local provider notes: different models have different dims, so the vector
store scopes collections per (provider, model, dim) — see
QdrantVectorStore.resolve_collection. Switching providers requires a
re-index (content-hash dedup makes it incremental).
"""
import logging
import threading

from app.config import get_settings

log = logging.getLogger("rajiblabs")

_LOCAL_MODEL = None
_LOCAL_LOCK = threading.Lock()
_LOCAL_MODEL_NAME: str | None = None


class EmbeddingError(Exception):
    """Raised when no embedding can be produced."""


def _local_model(model_name: str):
    """Process-wide cached SentenceTransformer (load once, ~90MB for MiniLM)."""
    global _LOCAL_MODEL, _LOCAL_MODEL_NAME
    with _LOCAL_LOCK:
        if _LOCAL_MODEL is None or _LOCAL_MODEL_NAME != model_name:
            try:
                from sentence_transformers import SentenceTransformer
            except Exception as e:
                raise EmbeddingError(
                    "local embeddings need the optional sentence-transformers "
                    f"package: {e}")
            _LOCAL_MODEL = SentenceTransformer(model_name)
            _LOCAL_MODEL_NAME = model_name
        return _LOCAL_MODEL


class EmbeddingService:
    def __init__(self):
        s = get_settings()
        self.provider = (s.embedding_provider or "openai").lower()
        if self.provider == "local":
            self.model = s.local_embedding_model or "all-MiniLM-L6-v2"
            self.version = "local-v1"
            self.dim = s.local_embedding_dim or 384
        else:
            self.model = s.embedding_model or "text-embedding-3-small"
            self.version = s.embedding_version or "v1"
            self.dim = s.embedding_dim or 1536

    @property
    def configured(self) -> bool:
        s = get_settings()
        if self.provider == "openai":
            return bool(s.openai_api_key and s.openai_enabled)
        if self.provider == "local":
            try:
                import sentence_transformers  # noqa: F401
                return True
            except Exception:
                return False
        return False

    def descriptor(self) -> dict:
        return {"embedding_provider": self.provider, "embedding_model": self.model,
                "embedding_version": self.version, "embedding_dim": self.dim}

    async def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Batch embed. Empty input → []. Raises EmbeddingError on failure."""
        texts = [t for t in (texts or []) if (t or "").strip()]
        if not texts:
            return []
        if self.provider == "local":
            try:
                model = _local_model(self.model)
                vecs = model.encode([t[:8000] for t in texts],
                                    normalize_embeddings=True,
                                    show_progress_bar=False)
                return [list(map(float, v)) for v in vecs]
            except EmbeddingError:
                raise
            except Exception as e:
                log.warning("local embedding failed: %s", e)
                raise EmbeddingError(str(e)[:300])
        if self.provider != "openai":
            raise EmbeddingError(f"unsupported embedding provider: {self.provider}")
        s = get_settings()
        if not s.openai_api_key or not s.openai_enabled:
            raise EmbeddingError("embeddings not configured")
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=s.openai_api_key)
            # OpenAI allows up to 2048 inputs per call; stay well under limits.
            out: list[list[float]] = []
            for i in range(0, len(texts), 100):
                resp = await client.embeddings.create(
                    model=self.model, input=[t[:8000] for t in texts[i:i + 100]])
                out.extend([d.embedding for d in resp.data])
            return out
        except Exception as e:
            log.warning("embedding generation failed: %s", e)
            raise EmbeddingError(str(e)[:300])

    async def generate_embedding(self, text: str) -> list[float]:
        vecs = await self.generate_embeddings([text])
        if not vecs:
            raise EmbeddingError("empty text")
        return vecs[0]
