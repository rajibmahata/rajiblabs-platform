"""Public chat (rate-limited, sandboxed) + lead capture + quote requests.

The turn pipeline lives in app.services.lead_pipeline (AI extracts, FastAPI
applies business rules, MongoDB stores). This module keeps the HTTP contract
and legacy fallbacks stable.
"""
import time
from fastapi import APIRouter, HTTPException, Request
from app.config import get_settings
from app.database import get_db, utcnow
from app.schemas import ChatMessageIn, LeadIn
from app.services.notify import notify

router = APIRouter(prefix="/api/public")
CHAT_HITS: dict[str, list[float]] = {}


def _limit(ip: str, limit: int = 20, window: int = 60):
    now = time.time()
    hits = [t for t in CHAT_HITS.get(ip, []) if now - t < window]
    if len(hits) >= limit:
        raise HTTPException(429, "Slow down — try again shortly.")
    hits.append(now)
    CHAT_HITS[ip] = hits


@router.post("/chat")
async def chat(body: ChatMessageIn, request: Request):
    s = get_settings()
    if not s.chat_enabled:
        raise HTTPException(503, "Chat temporarily unavailable. Please contact Rajib directly.")
    _limit(request.client.host if request.client else "unknown")
    from app.services.lead_pipeline import process_chat_message
    db = get_db()
    try:
        # mode="rag" needs no second LLM call: the pipeline already grounds
        # the reply in RAG retrieval and returns intent+sources for the UI.
        resp = await process_chat_message(
            db, body.session_token or body.session_id, body.message,
            request.client.host if request.client else "unknown",
            explicit={"name": body.name, "email": body.email, "phone": body.phone},
            language=body.language)
        if (body.mode or "").lower() == "rag":
            resp["mode"] = "rag"
        return resp
    except HTTPException:
        raise
    except Exception as e:
        # Never lose the turn with a 500: persist + graceful reply.
        try:
            from app.services.notify import log_error
            await log_error("lead_chat", "Chat turn failed", str(e)[:2000], level="error",
                                logger="app.routers.chat")
        except Exception:
            pass
        return {"session_id": body.session_token or "", "session_token": body.session_token or "",
                "message": "I'm having trouble processing that right now. Your message has been saved. "
                           "Please continue or try again shortly.",
                "reply": "I'm having trouble processing that right now. Your message has been saved. "
                         "Please continue or try again shortly.",
                "lead_captured": False, "missing_fields": ["name", "email", "phone", "idea"],
                "show_blueprint": False, "scope_ready": False}


@router.post("/leads")
async def lead(body: LeadIn, request: Request):
    _limit("lead:" + (request.client.host if request.client else "x"), limit=10, window=3600)
    db = get_db()
    # Reuse the dedup path so form leads never duplicate chat leads.
    from app.services import leads as rules
    from app.services.lead_pipeline import find_or_create_lead
    email = rules.normalize_email(body.email)
    lead, _ = await find_or_create_lead(db, {
        "name": body.name.strip(), "email": email,
        "phone": rules.normalize_phone(body.phone),
        "company_name": "", "industry": ""}, session_token="")
    # Record the enquiry text on the lead without overwriting profile fields.
    desc = (body.description or "").strip()[:5000]
    patch = {"updated_at": utcnow()}
    if body.product:
        patch["product"] = body.product[:200]
    if desc and not (lead.get("description") or ""):
        patch["description"] = desc
    await db["customer_leads"].update_one({"_id": lead["_id"]}, {"$set": patch})
    await notify("NEW_LEAD", f"New enquiry from {body.name}", desc[:200], "lead", str(lead["_id"]))
    return {"ok": True}


@router.post("/quote")
async def quote(body: LeadIn, request: Request):
    return await lead(body, request)
