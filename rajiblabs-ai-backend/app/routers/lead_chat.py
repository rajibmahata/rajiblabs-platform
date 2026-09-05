"""AI lead-conversation endpoints: session lifecycle, history restore, scope analysis.

Session tokens are unguessable bearer secrets — history only ever returns the
caller’s own conversation. All admin lead views live in admin_projects.py.
"""
import re

from fastapi import APIRouter, HTTPException, Request

from app.database import get_db, utcnow
from app.routers.chat import _limit
from app.schemas import ChatSessionOut
from app.services import leads as rules
from app.services.lead_ai import source_hash

router = APIRouter(prefix="/api/public")

TOKEN_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def _check_token(token: str) -> str:
    token = (token or "").strip()
    if not TOKEN_RE.match(token):
        raise HTTPException(404, "Session not found")
    return token


@router.post("/chat/session", response_model=ChatSessionOut)
async def create_session(request: Request):
    """Start (or resume) an anonymous chat session. Rate-limited, no auth."""
    from app.services.lead_pipeline import get_or_create_session
    _limit("session:" + (request.client.host if request.client else "x"),
           limit=30, window=3600)
    db = get_db()
    _, token = await get_or_create_session(
        db, None, request.client.host if request.client else "unknown")
    return {"session_id": token}


@router.get("/chat/session/{session_id}")
async def get_session(session_id: str, request: Request):
    """Restore a session after refresh: status + recent messages (own only)."""
    from app.services.lead_pipeline import get_active_idea
    _limit("history:" + (request.client.host if request.client else "x"),
           limit=30, window=60)
    token = _check_token(session_id)
    db = get_db()
    sess = await db["customer_conversations"].find_one({"session_token": token})
    if not sess:
        raise HTTPException(404, "Session not found")
    cur = db["customer_messages"].find({"session_token": token}).sort("created_at", 1).limit(100)
    messages = [{"role": ("assistant" if d.get("sender") == "assistant" else "user"),
                 "text": d.get("message", "")} async for d in cur]
    lead, idea = None, {}
    if sess.get("lead_id"):
        try:
            from bson import ObjectId
            lead = await db["customer_leads"].find_one({"_id": ObjectId(sess["lead_id"])})
        except Exception:
            lead = None
        idea = await get_active_idea(db, token) or {}
    lead = lead or {}
    idea = idea or {}
    missing = rules.missing_fields_for(lead, idea)
    return {
        "session_id": token,
        "status": sess.get("status", "active"),
        "messages": messages,
        "lead_captured": not missing,
        "missing_fields": missing,
        "show_blueprint": (not missing) and rules.idea_is_substantive(idea),
        "scope_ready": bool((idea.get("preliminary_scope") or {})),
    }


@router.post("/chat/{session_id}/analyze")
async def analyze_session(session_id: str, request: Request):
    """Generate (or return cached) preliminary scope for the session's idea."""
    from app.services.lead_ai import AIError
    from app.services.lead_pipeline import get_active_idea
    _limit("analyze:" + (request.client.host if request.client else "x"),
           limit=5, window=3600)
    token = _check_token(session_id)
    db = get_db()
    sess = await db["customer_conversations"].find_one({"session_token": token})
    if not sess:
        raise HTTPException(404, "Session not found")
    lead = {}
    if sess.get("lead_id"):
        try:
            from bson import ObjectId
            lead = await db["customer_leads"].find_one({"_id": ObjectId(sess["lead_id"])}) or {}
        except Exception:
            lead = {}
    idea = await get_active_idea(db, token) or {}
    if not rules.idea_is_substantive(idea):
        raise HTTPException(400, {"error": "Not enough business context yet — "
                                           "tell the assistant what you want to build first."})
    h = source_hash(idea.get("description", ""), idea.get("problem_statement", ""),
                      idea.get("current_process", ""), idea.get("desired_outcome", ""))
    if idea.get("scope_source_hash") == h and idea.get("preliminary_scope"):
        return {"scope": idea["preliminary_scope"],
                "scope_markdown": idea.get("scope_markdown", ""),
                "cached": True, "disclaimer": rules.SCOPE_DISCLAIMER}
    from app.services.lead_pipeline import generate_and_store_scope
    try:
        payload, markdown, _ = await generate_and_store_scope(db, lead, idea, h)
    except AIError:
        raise HTTPException(503, {"error": "Analysis is temporarily unavailable. "
                                           "Your conversation is saved — please try again shortly."})
    return {"scope": payload, "scope_markdown": markdown,
            "cached": False, "disclaimer": rules.SCOPE_DISCLAIMER}


@router.get("/chat/health")
async def chat_health():
    from app.config import get_settings
    s = get_settings()
    return {"chat_enabled": s.chat_enabled,
            "ai_configured": s.is_openai_configured(),
            "provider": (s.ai_provider or "openai")}
