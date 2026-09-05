"""Embedding abstraction — OpenAI first, open for other providers later.

Records provider/model/version with indexed metadata (§8). Raises AIError
when unusable so callers degrade gracefully (heuristic chat still works).
"""
import logging

from app.config import get_settings

log = logging.getLogger("rajiblabs")


class EmbeddingError(Exception):
    """Raised when no embedding can be produced."""


class EmbeddingService:
    def __init__(self):
        s = get_settings()
        self.provider = (s.embedding_provider or "openai").lower()
        self.model = s.embedding_model or "text-embedding-3-small"
        self.version = s.embedding_version or "v1"
        self.dim = s.embedding_dim or 1536

    @property
    def configured(self) -> bool:
        s = get_settings()
        if self.provider == "openai":
            return bool(s.openai_api_key and s.openai_enabled)
        return False  # future providers plug in here

    def descriptor(self) -> dict:
        return {"embedding_provider": self.provider, "embedding_model": self.model,
                "embedding_version": self.version, "embedding_dim": self.dim}

    async def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Batch embed. Empty input → []. Raises EmbeddingError on failure."""
        texts = [t for t in (texts or []) if (t or "").strip()]
        if not texts:
            return []
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
