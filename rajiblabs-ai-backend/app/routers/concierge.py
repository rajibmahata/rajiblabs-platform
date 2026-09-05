"""Public Concierge Agent chat (rate-limited, grounded, no secrets).

One endpoint powers the homepage "Chat with RajibLabs Agent": intent →
sanitized public tools → single small LLM reply (or deterministic tool-only
reply). The agent config (enable flag, prompt, tools, policies) is
server-side in MongoDB; admin-only tools can never run here.
"""
import time
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from app.config import get_settings
from app.database import get_db
from app.services import agent_config as agents
from app.services.notify import log_error

router = APIRouter(prefix="/api/public/agent")
_HITS: dict[str, list[float]] = {}


class AgentChatIn(BaseModel):
    message: str = ""
    session_token: str | None = None
    session_id: str | None = None
    language: str | None = None


def _limit(ip: str, limit: int = 20, window: int = 60):
    now = time.time()
    hits = [t for t in _HITS.get(ip, []) if now - t < window]
    if len(hits) >= limit:
        raise HTTPException(429, "Slow down — try again shortly.")
    hits.append(now)
    _HITS[ip] = hits


@router.get("/config")
async def agent_card():
    """Public agent card for the homepage (name, description, starters)."""
    from app.services import concierge as _cg
    db = get_db()
    agent = await agents.get_agent(db, agents.CONCIERGE_SLUG)
    if not agent or not agent.get("enabled") or not agent.get("public_enabled"):
        raise HTTPException(503, "Agent temporarily unavailable.")
    return {
        "name": agent.get("name", "RajibLabs Concierge Agent"),
        "description": agent.get("description", ""),
        "slug": agent.get("slug", agents.CONCIERGE_SLUG),
        "starters": list(_cg.SUGGESTED_STARTERS),
    }


@router.post("/chat")
async def agent_chat(body: AgentChatIn, request: Request):
    s = get_settings()
    if not s.chat_enabled:
        raise HTTPException(503, "Chat temporarily unavailable. Please contact Rajib directly.")
    _limit(request.client.host if request.client else "unknown")
    if not (body.message or "").strip():
        raise HTTPException(400, "Message is required")
    from app.services import concierge as _cg
    db = get_db()
    try:
        return await _cg.run_concierge_turn(
            db, body.message, body.session_token or body.session_id,
            request.client.host if request.client else "unknown",
            language=body.language or "en")
    except HTTPException:
        raise
    except Exception as e:
        try:
            await log_error("concierge", "Agent turn failed", str(e)[:2000],
                            logger="app.routers.concierge")
        except Exception:
            pass
        return {"reply": "I'm having trouble processing that right now. "
                         "Please try again shortly, or reach RajibLabs directly.",
                "sources": [], "intent": "error", "tools_called": [],
                "session_token": body.session_token or "", "lead_captured": False,
                "missing_fields": [], "agent": agents.CONCIERGE_SLUG}
