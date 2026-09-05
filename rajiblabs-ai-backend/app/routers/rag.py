"""Public RAG endpoints (§19): stateless grounded Q&A + health.

Lead capture keeps flowing through POST /api/public/chat (RAG-augmented in
the pipeline); this router answers pure knowledge questions with the §15
contract {answer, intent, sources[]}.
"""
import time
from fastapi import APIRouter, HTTPException, Request
from app.config import get_settings
from app.database import get_db
from app.schemas import RagQueryIn

router = APIRouter(prefix="/api/rag")
_RAG_HITS: dict[str, list[float]] = {}


def _limit(ip: str, limit: int = 20, window: int = 60):
    now = time.time()
    hits = [t for t in _RAG_HITS.get(ip, []) if now - t < window]
    if len(hits) >= limit:
        raise HTTPException(429, "Slow down — try again shortly.")
    hits.append(now)
    _RAG_HITS[ip] = hits


@router.get("/health")
async def rag_health():
    """RAG readiness: Mongo counts + Qdrant collection info (§24). Never 500s."""
    from app.services.rag_vectors import VectorStoreError, get_vector_store
    s = get_settings()
    out: dict = {"enabled": s.rag_enabled, "mongo": {}, "qdrant": {"ok": False}}
    try:
        db = get_db()
        out["mongo"] = {
            "documents": await db["knowledge_documents"].count_documents({}),
            "active": await db["knowledge_documents"].count_documents({"status": "active"}),
            "failed": await db["knowledge_documents"].count_documents({"status": "failed"}),
            "chunks": await db["knowledge_chunks"].count_documents({}),
        }
    except Exception as e:
        out["mongo"] = {"error": str(e)[:200]}
    # health_check() never raises, but stay defensive — health must not 500.
    try:
        out["qdrant"] = await get_vector_store().health_check()
    except Exception as e:
        out["qdrant"] = {"ok": False, "error": str(e)[:200]}
    return out


@router.post("/query")
async def rag_query(body: RagQueryIn, request: Request):
    """Grounded answer with intent + sources (§14/§15). Rate-limited, audited."""
    from app.services import rag_query as rq
    s = get_settings()
    ip = request.client.host if request.client else "unknown"
    _limit(ip)
    if not s.chat_enabled:
        raise HTTPException(503, "Chat temporarily unavailable. Please contact Rajib directly.")
    history: list[dict] = []
    if body.session_id:
        try:
            db = get_db()
            cur = db["customer_messages"].find(
                {"session_token": body.session_id[:64]}).sort("created_at", 1).limit(30)
            history = [{"role": ("assistant" if d.get("sender") == "assistant" else "user"),
                        "content": (d.get("message") or "")[:1000]}
                       async for d in cur][-6:]
        except Exception:
            history = []
    try:
        # answer_question audits RAG_QUERY/RAG_ANSWER itself (§32).
        ans = await rq.answer_question(body.question, history=history,
                                       session_id=body.session_id or ip,
                                       top_k=body.top_k or 0,
                                       language=body.language or "en")
    except HTTPException:
        raise
    except Exception as e:
        try:
            from app.services.notify import log_error
            await log_error("rag_query", "RAG query failed", str(e)[:2000], level="error",
                                logger="app.routers.rag")
        except Exception:
            pass
        raise HTTPException(500, "Knowledge search failed. Please try again shortly.")
    return ans.model_dump()
