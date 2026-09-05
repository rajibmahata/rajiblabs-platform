"""Lead conversation pipeline — orchestrates one chat turn end-to-end.

AI extracts (lead_ai.AIService); THIS module validates, dedups, merges,
scores and persists. The AI never touches MongoDB directly.
"""
import hashlib
import logging
import secrets

from app.database import get_db, utcnow
from app.services import leads as rules
from app.services.lead_ai import AIError, AIService, source_hash
from app.services.notify import audit, notify

log = logging.getLogger("rajiblabs")

CONTACT_FALLBACK = ("Reach Rajib: rajibmahata143@gmail.com, +91 84202 49020, "
                    "WhatsApp https://wa.me/918420249020.")


async def build_knowledge(db) -> str:
    """Compact approved-site knowledge for grounding (never raw source)."""
    parts = ["RajibLabs is an AI-first venture studio run by Rajib Mahata, "
             "Senior .NET & Azure Solutions Architect (12+ years enterprise)."]
    try:
        cur = db["projects"].find({"published": True}).sort("display_order", 1).limit(8)
        projs = []
        async for p in cur:
            tech = ",".join((p.get("technologies") or [])[:4])
            projs.append(f"{p.get('name')} ({tech}) [{p.get('status','')}]")
        if projs:
            parts.append("Products/projects: " + "; ".join(projs))
    except Exception:
        pass
    parts.append("Contact: rajibmahata143@gmail.com, +91 84202 49020, "
                 "WhatsApp https://wa.me/918420249020. No public pricing — quotes via discovery.")
    return "\n".join(parts)[:3000]


async def heuristic_reply(db, question: str) -> str:
    """Zero-cost fallback when AI is unavailable (mirrors legacy behavior)."""
    q = (question or "").lower()
    if any(k in q for k in ("project", "work", "portfolio", "product")):
        try:
            cur = db["projects"].find({"published": True}).sort("display_order", 1).limit(5)
            names = [f"{d['name']} ({','.join((d.get('technologies') or [])[:3])})" async for d in cur]
            if names:
                return ("Featured work: " + "; ".join(names) + ". Tell me what you want to build.")
        except Exception:
            pass
    if any(k in q for k in ("contact", "hire", "email", "phone", "cost", "price", "quot")):
        return ("You can reach Rajib directly: rajibmahata143@gmail.com, +91 84202 49020. "
                "Or just tell me your name, email, phone and what you want to build.")
    return ("Thanks — tell me a little about what you want to build or improve, "
            "and your name, email and phone so Rajib can follow up. " + CONTACT_FALLBACK)


def _ai_configured() -> bool:
    """True when an AI provider key is present (mock-proof: reads settings)."""
    try:
        from app.config import get_settings
        s = get_settings()
        return bool(s.openai_enabled and (s.openai_api_key or s.deepseek_api_key))
    except Exception:
        return False


def _lead_public(lead: dict) -> dict:
    return {"name": lead.get("name", ""), "email": lead.get("email", ""),
            "phone": lead.get("phone", ""), "company_name": lead.get("company_name", ""),
            "industry": lead.get("industry", "")}


async def get_or_create_session(db, token: str | None, client_ip: str) -> tuple[dict, str]:
    token = (token or "").strip()[:64]
    if token:
        sess = await db["customer_conversations"].find_one({"session_token": token})
        if sess:
            return sess, token
    token = secrets.token_urlsafe(24)
    now = utcnow()
    doc = {"session_token": token, "session_id": token, "lead_id": None,
           "status": "active", "source": "website_chat",
           "started_at": now, "last_message_at": now, "last_activity_at": now,
           "completed_at": None,
           "ip_hash": hashlib.sha256(client_ip.encode()).hexdigest()[:16],
           "metadata": {}}
    res = await db["customer_conversations"].insert_one(doc)
    doc["_id"] = res.inserted_id
    await audit("website_chat", "SESSION_CREATED", token, {"source": "website_chat"},
                event_type="SESSION_CREATED", session_id=token)
    return doc, token


async def find_or_create_lead(db, fields: dict, session_token: str,
                               message_text: str = "") -> tuple[dict, bool]:
    """Email-first, phone-second dedup. Fills missing fields; replaces a
    contact detail only on explicit correction language. Fields the admin
    locked (locked_fields) are never touched. Returns (lead, created)."""
    email = rules.normalize_email(fields.get("email"))
    phone = rules.normalize_phone(fields.get("phone"))
    lead = None
    if email:
        lead = await db["customer_leads"].find_one({"email": email})
    if not lead and phone:
        lead = await db["customer_leads"].find_one({"phone": phone})
    now = utcnow()
    if lead:
        locked = set(lead.get("locked_fields") or [])
        correcting = rules.states_correction(message_text)
        patch: dict = {}
        for key, cap in (("name", 120), ("company_name", 200), ("industry", 120)):
            val = (fields.get(key) or "").strip()
            if not val or key in locked:
                continue
            if not (lead.get(key) or "").strip() or correcting:
                patch[key] = val[:cap]
        if email and "email" not in locked and (not lead.get("email") or correcting):
            patch["email"] = email
        if phone and "phone" not in locked and (not lead.get("phone") or correcting):
            patch["phone"] = phone
        sids = list(lead.get("session_ids") or [])
        if session_token and session_token not in sids:
            sids.append(session_token)
            patch["session_ids"] = sids
        patch["updated_at"] = now
        if patch:
            await db["customer_leads"].update_one({"_id": lead["_id"]}, {"$set": patch})
        lead = await db["customer_leads"].find_one({"_id": lead["_id"]})
        await audit("website_chat", "LEAD_UPDATED", str(lead["_id"]),
                    {"fields": sorted(patch.keys())},
                    event_type="LEAD_UPDATED", session_id=session_token,
                    lead_id=str(lead["_id"]))
        return lead, False
    doc = {
        "name": (fields.get("name") or "").strip()[:120],
        "email": email, "phone": phone,
        "company_name": (fields.get("company_name") or "").strip()[:200],
        "industry": (fields.get("industry") or "").strip()[:120],
        "status": "new", "lead_score": 0, "source": "website_chat",
        "marketing_consent": False, "tags": [], "campaigns": [], "email_history": [],
        "workflow_enrollment": None, "opens": 0, "clicks": 0,
        "last_contacted_at": None, "unsubscribe": False,
        "session_ids": [session_token] if session_token else [], "conversation_id": None,
        "description": "", "product": None,
        "created_at": now, "updated_at": now,
    }
    res = await db["customer_leads"].insert_one(doc)
    doc["_id"] = res.inserted_id
    await audit("website_chat", "LEAD_CREATED", str(res.inserted_id),
                {"source": "website_chat"},
                event_type="LEAD_CREATED", session_id=session_token,
                lead_id=str(res.inserted_id))
    return doc, True


async def get_active_idea(db, session_token: str) -> dict | None:
    cur = db["ideas"].find({"session_id": session_token,
                            "status": {"$ne": "archived"}}).sort("updated_at", -1).limit(1)
    rows = [d async for d in cur]
    return rows[0] if rows else None


async def upsert_idea(db, session_token: str, lead_id, incoming: dict,
                      message_text: str) -> tuple[dict, bool, bool]:
    """Returns (idea, created, archived_previous). One active idea per session;
    a new one starts only on an explicit new-topic signal with substantive prior."""
    current = await get_active_idea(db, session_token)
    has_content = any((incoming.get(k) or "").strip()
                      for k in ("description", "problem_statement",
                                "current_process", "desired_outcome"))
    if current and rules.wants_new_idea(message_text) and rules.idea_is_substantive(current):
        await db["ideas"].update_one({"_id": current["_id"]},
                                     {"$set": {"status": "archived", "updated_at": utcnow()}})
        await audit("website_chat", "IDEA_UPDATED", str(current["_id"]),
                    {"archived": True},
                    event_type="IDEA_UPDATED", session_id=session_token,
                    lead_id=str(current.get("lead_id") or ""))
        current = None
        archived = True
    else:
        archived = False
    now = utcnow()
    if current is None:
        if not has_content:
            return {}, False, archived
        title = (incoming.get("description") or "Untitled idea").strip()[:120]
        doc = {"lead_id": lead_id, "session_id": session_token, "title": title,
               "description": (incoming.get("description") or "").strip()[:2000],
               "problem_statement": (incoming.get("problem_statement") or "").strip()[:2000],
               "desired_outcome": (incoming.get("desired_outcome") or "").strip()[:2000],
               "industry": (incoming.get("industry") or "").strip()[:120],
               "current_process": (incoming.get("current_process") or "").strip()[:2000],
               "ai_analysis": "", "preliminary_scope": None, "scope_markdown": "",
               "scope_source_hash": "", "status": "new",
               "created_at": now, "updated_at": now}
        res = await db["ideas"].insert_one(doc)
        doc["_id"] = res.inserted_id
        await audit("website_chat", "IDEA_CREATED", str(res.inserted_id),
                    {},
                    event_type="IDEA_CREATED", session_id=session_token,
                    lead_id=str(doc.get("lead_id") or ""))
        return doc, True, archived
    if has_content:
        merged = rules.merge_idea(current, incoming)
        merged["updated_at"] = now
        if not (current.get("industry") or "").strip() and (incoming.get("industry") or "").strip():
            merged["industry"] = incoming["industry"].strip()[:120]
        await db["ideas"].update_one({"_id": current["_id"]}, {"$set": merged})
        current = await db["ideas"].find_one({"_id": current["_id"]})
        await audit("website_chat", "IDEA_UPDATED", str(current["_id"]),
                    {},
                    event_type="IDEA_UPDATED", session_id=session_token,
                    lead_id=str(current.get("lead_id") or ""))
    return current, False, archived


async def generate_and_store_scope(db, lead: dict, idea: dict,
                                   h: str) -> tuple[dict, str, dict]:
    """Single AI-scope path used by auto-trigger AND the manual endpoint,
    so tests patch one place (lead_pipeline.AIService) and behavior matches."""
    scope, meta = await AIService().analyze_idea(
        {"name": lead.get("name"), "email": lead.get("email"),
         "phone": lead.get("phone"), "company_name": lead.get("company_name"),
         "industry": lead.get("industry")},
        {"description": idea.get("description"),
         "problem_statement": idea.get("problem_statement"),
         "current_process": idea.get("current_process"),
         "desired_outcome": idea.get("desired_outcome")})
    payload = scope.model_dump()
    markdown = rules.render_scope_markdown(payload)
    await db["ideas"].update_one(
        {"_id": idea["_id"]},
        {"$set": {"preliminary_scope": payload, "scope_markdown": markdown,
                  "scope_source_hash": h, "ai_analysis": meta.get("ai_model", ""),
                  "updated_at": utcnow()}})
    await audit("website_chat", "SCOPE_GENERATED", str(idea["_id"]),
                {"model": meta.get("ai_model", "")},
                event_type="SCOPE_GENERATED",
                session_id=idea.get("session_id"),
                lead_id=str(lead.get("_id")))
    return payload, markdown, meta


async def maybe_auto_analyze(db, lead: dict, idea: dict) -> dict | None:
    """Generate scope once per idea version when lead is captured. Never raises."""
    try:
        if not idea or not idea.get("_id"):
            return None
        if not (lead.get("name") and rules.valid_email(lead.get("email"))
                and rules.valid_phone(lead.get("phone"))):
            return None
        if not rules.idea_is_substantive(idea):
            return None
        h = source_hash(idea.get("description", ""), idea.get("problem_statement", ""),
                        idea.get("current_process", ""), idea.get("desired_outcome", ""))
        if idea.get("scope_source_hash") == h and idea.get("preliminary_scope"):
            return idea["preliminary_scope"]
        payload, _, _ = await generate_and_store_scope(db, lead, idea, h)
        return payload
    except Exception as e:
        log.warning("auto-analyze skipped: %s", e)
        return None

async def process_chat_message(db, session_token: str | None, message: str,
                               client_ip: str,
                               explicit: dict | None = None,
                               language: str | None = None) -> dict:
    """Full 18-step turn. Returns the public response dict (legacy-compatible).

    `language` localizes the reply only — lead capture, scoring and storage
    are language-independent."""
    message = (message or "").strip()[:2000]
    explicit = explicit or {}
    try:
        from app.services import lang_service as _ls
        language, _ = await _ls.response_instruction(language, db)
    except Exception:
        language = "en"

    # 1. session — 2. length already validated by schema
    sess, token = await get_or_create_session(db, session_token, client_ip)

    # 3. persist user message (+ legacy mirrors for old readers)
    now = utcnow()
    await db["customer_messages"].insert_one({
        "conversation_id": str(sess["_id"]), "session_token": token,
        "sender": "user", "role": "user", "message": message, "content": message,
        "ai_provider": None, "ai_model": None, "usage": {}, "created_at": now})
    # 4. audit
    await audit("website_chat", "MESSAGE_RECEIVED", token, {"len": len(message)},
                event_type="MESSAGE_RECEIVED", session_id=token)

    # 5/6. existing lead + idea
    lead = None
    if sess.get("lead_id"):
        try:
            from bson import ObjectId
            lead = await db["customer_leads"].find_one({"_id": ObjectId(sess["lead_id"])})
        except Exception:
            lead = None
    lead = lead or {}
    idea = await get_active_idea(db, token) or {}
    known = {"name": lead.get("name", ""), "email": lead.get("email", ""),
             "phone": lead.get("phone", ""),
             "company": lead.get("company_name", ""), "industry": lead.get("industry", ""),
             "idea": (idea.get("description", "")[:120] if idea else "")}

    # 7/8/9. AI turn (or heuristic fallback)
    ai_meta: dict = {}
    rag_meta: dict = {"intent": None, "sources": []}
    try:
        history_cur = db["customer_messages"].find(
            {"session_token": token}).sort("created_at", 1).limit(30)
        history = [{"role": ("assistant" if d.get("sender") == "assistant" else "user"),
                    "content": (d.get("message") or "")[:1000]}
                   async for d in history_cur][-12:]
        knowledge = await build_knowledge(db)
        # RAG augmentation (§18): verified retrieval grounds the same AI turn.
        # Disabled/misconfigured RAG degrades to the legacy knowledge string.
        try:
            from app.config import get_settings as _rag_settings
            if _rag_settings().rag_enabled:
                from app.services import rag_query as _rag
                _intent, _method = await _rag.classify_intent(message)
                rag_meta["intent"] = _intent
                _chunks = await _rag.retrieve(message, intent=_intent)
                if _chunks:
                    _ctx = "\n\n".join(
                        f"[{c['title']}] ({c['source_type']}): {c['content'][:1200]}"
                        for c in _chunks)
                    knowledge = (knowledge + "\n\nVerified RAG knowledge:\n" + _ctx)[:6000]
                    rag_meta["sources"] = [
                        {"title": c.get("title", ""), "source_type": c.get("source_type", ""),
                         "url": c.get("url"), "score": c.get("score", 0)} for c in _chunks]
                await audit("rag", "RAG_QUERY", token,
                            {"intent": _intent, "method": _method,
                             "retrieved": len(rag_meta["sources"])},
                            event_type="RAG_QUERY", session_id=token)
        except Exception as _e:
            log.warning("RAG augment skipped: %s", _e)
        await audit("website_chat", "AI_REQUEST", token, {},
                    event_type="AI_REQUEST", session_id=token)
        result, ai_meta = await AIService().chat_with_lead(
            history, message, knowledge, known, language=language or "en")
        await audit("website_chat", "AI_RESPONSE", token,
                    {"provider": ai_meta.get("ai_provider", ""),
                     "next_action": result.next_action},
                    event_type="AI_RESPONSE", session_id=token)
        reply = result.reply
        ai_lead = result.lead.model_dump()
        ai_idea = result.idea.model_dump()
    except AIError as e:
        log.warning("AI turn failed: %s", e)
        await audit("website_chat", "AI_FAILURE", token, {"error": str(e)[:300]},
                    event_type="AI_FAILURE", session_id=token)
        try:
            from app.services.notify import log_error
            await log_error("lead_chat", "AI turn failed", str(e)[:2000], level="warning",
                                logger="app.services.lead_pipeline")
        except Exception:
            pass
        if _ai_configured():
            # Provider was configured but failed: spec §12 graceful message.
            # The user message is already persisted; nothing is lost.
            reply = ("I'm having trouble processing that right now. Your message has been saved. "
                     "Please continue or try again shortly. Or contact Rajib directly: "
                     "rajibmahata143@gmail.com / +91 84202 49020.")
        else:
            # Zero-spend heuristic mode (no API key): answer from site knowledge.
            reply = await heuristic_reply(db, message)
        ai_lead, ai_idea = {}, {}

    # 10/11. backend validation — explicit body fields win, then AI extraction
    fields = {
        "name": (explicit.get("name") or ai_lead.get("name") or "").strip()[:120],
        "email": (explicit.get("email") or ai_lead.get("email") or "").strip(),
        "phone": (explicit.get("phone") or ai_lead.get("phone") or "").strip(),
        "company_name": (explicit.get("company_name") or ai_lead.get("company_name") or "").strip()[:200],
        "industry": (ai_lead.get("industry") or "").strip()[:120],
    }
    if fields["email"] and not rules.valid_email(fields["email"]):
        fields["email"] = ""
    if fields["phone"]:
        fields["phone"] = rules.normalize_phone(fields["phone"])
        if not rules.valid_phone(fields["phone"]):
            fields["phone"] = ""
    incoming_idea = {
        "description": (ai_idea.get("description") or "").strip()[:2000],
        "problem_statement": (ai_idea.get("problem_statement") or "").strip()[:2000],
        "current_process": (ai_idea.get("current_process") or "").strip()[:2000],
        "desired_outcome": (ai_idea.get("desired_outcome") or "").strip()[:2000],
        "industry": fields["industry"],
    }

    # Seed idea from a plain business message even when AI is down:
    # a long first message about building/improving something is an idea.
    if (not any(incoming_idea.values()) and len(message) >= 20
            and any(k in message.lower() for k in
                    ("build", "need", "want", "app", "platform", "software", "system",
                     "website", "automate", "manage", "booking", "business", "idea",
                     "project", "help", "looking for"))):
        incoming_idea["description"] = message[:500]

    # 12. create/update lead (email-first, phone-second dedup)
    had_lead_before = bool(lead.get("_id"))
    lead, created = await find_or_create_lead(db, {**fields,
                                                   "company_name": fields["company_name"],
                                                   "industry": fields["industry"]}, token,
                                              message_text=message)
    if not had_lead_before:
        await notify("NEW_LEAD", f"New enquiry from {lead.get('name') or 'website visitor'}",
                     (message)[:200], "lead", str(lead["_id"]))
    # attach session → lead
    if str(sess.get("lead_id") or "") != str(lead["_id"]):
        await db["customer_conversations"].update_one(
            {"_id": sess["_id"]}, {"$set": {"lead_id": str(lead["_id"])}})

    # marketing consent: explicit opt-in only, with evidence
    if rules.gives_marketing_consent(message) and not lead.get("marketing_consent"):
        await db["customer_leads"].update_one(
            {"_id": lead["_id"]},
            {"$set": {"marketing_consent": True, "updated_at": utcnow()}})
        await audit("website_chat", "LEAD_UPDATED", str(lead["_id"]),
                    {"marketing_consent": True, "evidence": message[:200]},
                    event_type="LEAD_UPDATED", session_id=token,
                    lead_id=str(lead["_id"]))
        lead["marketing_consent"] = True

    # 13. create/update idea
    idea, idea_created, _ = await upsert_idea(db, token, lead["_id"], incoming_idea, message)
    idea = idea or {}

    # 14. score (+ hot-lead event on upward crossing)
    old_score = int(lead.get("lead_score") or 0)
    new_score = rules.score_lead(lead, idea, message)
    if new_score != old_score:
        await db["customer_leads"].update_one(
            {"_id": lead["_id"]}, {"$set": {"lead_score": new_score, "updated_at": utcnow()}})
        lead["lead_score"] = new_score
    if old_score < rules.HOT_LEAD_THRESHOLD <= new_score:
        await notify("HotLeadDetected", f"Hot lead: {lead.get('name') or lead.get('email') or 'visitor'} "
                                        f"(score {new_score})", (idea.get("description") or "")[:200],
                     "lead", str(lead["_id"]))
        await audit("website_chat", "HotLeadDetected", str(lead["_id"]),
                    {"score": new_score},
                    event_type="HotLeadDetected", session_id=token,
                    lead_id=str(lead["_id"]))

    # 15. auto scope when captured + substantive (never fails the turn)
    scope = await maybe_auto_analyze(db, lead, idea)

    # authoritative capture state (never trust AI flags)
    missing = rules.missing_fields_for(lead, idea)
    captured = not missing

    # 16/17. persist assistant message + touch session
    await db["customer_messages"].insert_one({
        "conversation_id": str(sess["_id"]), "session_token": token,
        "sender": "assistant", "role": "assistant", "message": reply, "content": reply,
        "ai_provider": ai_meta.get("ai_provider"), "ai_model": ai_meta.get("ai_model"),
        "usage": ai_meta.get("usage", {}), "created_at": utcnow()})
    await db["customer_conversations"].update_one(
        {"_id": sess["_id"]}, {"$set": {"last_message_at": utcnow(),
                                        "last_activity_at": utcnow()}})

    # 18. response (legacy keys reply/session_token kept for the widget)
    return {
        "session_id": token, "session_token": token,
        "message": reply, "reply": reply,
        "lead_captured": captured, "missing_fields": missing,
        "show_blueprint": captured and rules.idea_is_substantive(idea),
        "scope_ready": bool(scope),
        # RAG grounding metadata (§15/§18) — additive, legacy readers ignore.
        "intent": rag_meta.get("intent"),
        "sources": rag_meta.get("sources", []),
        "language": language or "en",
    }
