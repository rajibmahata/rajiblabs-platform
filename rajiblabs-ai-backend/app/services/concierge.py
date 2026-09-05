"""RajibLabs Concierge Agent — intent → tools → grounded reply.

Cost-efficient agentic flow: rule-based intent + tool selection (no LLM),
tool/database/RAG lookups, then a SINGLE small LLM call to compose the
reply. Pure lookups (greetings, contact, verified live URLs) and lead
follow-ups never touch the LLM at all. When the provider fails, a
deterministic tool-only composer answers from the same verified results.

Server-side boundaries: only PUBLIC_TOOLS can run (run_public_tool
rejects admin-only/unknown names); RAG hits are filtered by the agent's
knowledge policy; reply URLs are validated against tool-returned URLs.
"""
import json
import re
import logging
import time
from app.database import get_db, utcnow
from app.services import agent_config as agents
from app.services import agent_tools as tools
from app.services.notify import audit, log_error, scrub_text

log = logging.getLogger("rajiblabs")

AGENT_SLUG = "rajiblabs-concierge"

# Conversation starters shown when chat opens (starters, not flows).
SUGGESTED_STARTERS = (
    "Do you know about RajibLabs?",
    "Tell me about Rajib",
    "What projects has Rajib completed?",
    "Tell me about this project",
    "Is there a live URL for this project?",
    "What services does RajibLabs provide?",
    "Show me Rajib's GitHub work",
    "I have a project idea",
    "Contact RajibLabs",
    "About RajibLabs",
)

TECH_VOCAB = (
    ".net", "azure", "react", "python", "fastapi", "mongodb", "sql server",
    "sql", "blazor", "typescript", "javascript", "docker", "rag", "llm",
    "openai", "ai", "qdrant", "tailwind", "angular", "node", "cosmos",
    "microservices", "pwa",
)

INTENT_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("contact", (r"contact", r"\bemail\b", r"\bphone\b", r"whatsapp", r"\breach\b",
                 r"call\s+rajib", r"talk\s+to\s+(rajib|you)", r"get in touch")),
    ("live_url", (r"\blive\b", r"\burl\b", r"\blink\b",
                  r"deployed", r"\bonline\b", r"demo link", r"is it (live|online|up)",
                  r"website.*(live|url|link|online|demo|deployed)",)),
    ("similar_project", (r"similar", r"something like", r"like this", r"related",
                         r"recommend", r"examples? for")),
    ("hire_lead", (r"\bhire\b", r"proposal", r"\bquot", r"pricing", r"\bprice\b",
                   r"\bcost\b", r"how much", r"estimate", r"\bmeeting\b", r"\bcall\b",
                   r"\bdemo\b", r"schedul", r"consult", r"work with",
                   r"\bbuild\b.*\b(me|us|for|an?\b|website|app|software|system|platform)",
                   r"i have (a |an )?(project|idea|requirement)",
                   r"need .*built", r"freelance", r"project idea", r"i need",
                   r"looking for.*(developer|team|agency|freelancer)")),
    ("services", (r"\bservice", r"what .*do (you|rajiblabs)", r"\boffer\b",
                  r"capabilit", r"what can you")),
    ("github_work", (r"github", r"\brepo\b", r"open source", r"\bcode\b")),
    ("products", (r"\bproduct", r"page[\s-]?flow", "docuflow", r"\bsaas\b")),
    ("about_rajib", (r"\brajib\b.*(who|about|experience|background|career|resume)",
                     r"who (is|are) (rajib|he)", r"about (him|rajib)\b",
                     r"\bresume\b", r"\bcv\b", r"experience", r"job history")),
    ("about_rajiblabs", (r"rajiblabs", r"about (the )?(company|studio|firm|site)",
                         r"what (is|does) rajiblabs", r"do you know about rajiblabs")),
    ("project_detail", (r"tell me about", r"what is (the|this|that)",
                       r"technolog", r"problem.*solv", r"what .* (built|used|made)",
                       r"architecture of", r"how .* built", r"is there a github")),
    ("projects_list", (r"\bprojects?\b", r"portfolio", r"\bbuilt\b", r"completed",
                       r"show .*work", r"case stud")),
)


def detect_intent(message: str) -> tuple[str, dict]:
    """Pure rule-based intent + entity extraction (unit-tested, no LLM)."""
    text = (message or "").lower()
    intent = "fallback"
    # standalone friendly greeting only (anything substantive routes by content)
    if re.match(r"^(hi|hello|hey|namaste|yo|good\s?(morning|afternoon|evening|day))\b", text) \
            and len(text) <= 25 \
            and not re.search(r"need|build|hire|project|idea|website|help|looking|question|tell|show|what|how", text):
        intent = "greeting"
    else:
        for name, patterns in INTENT_RULES:
            if any(re.search(p, text) for p in patterns):
                intent = name
                break
    entities: dict = {}
    techs = [t for t in TECH_VOCAB if re.search(rf"(?<![\w.]){re.escape(t)}(?![\w])", text)]
    if techs:
        # prefer the longest/most specific match ("sql server" over "sql")
        techs.sort(key=len, reverse=True)
        entities["tech"] = techs[0]
    quoted = re.findall(r'"([^"]{2,60})"|‘([^’]{2,60})’', message or "")
    if quoted:
        entities["project_ref"] = (quoted[0][0] or quoted[0][1]).strip()
    else:
        m = re.search(
            r"(?:about|for|of|called|named)\s+([A-Za-z][\w\s.&-]{1,40}?)(?:\s+project)?\s*[?.!,]*$",
            (message or "").strip(), re.IGNORECASE)
        if m:
            cand = m.group(1).strip()
            if len(cand) > 2 and cand.lower() not in (
                    "rajib", "rajiblabs", "it", "this", "that", "you", "your"):
                entities["project_ref"] = cand
    return intent, entities


def select_tools(intent: str, entities: dict, allowed: list[str] | None) -> list[tuple[str, dict]]:
    """Intent → tool calls, pruned to the agent's allow-list (pure)."""
    allowed_set = set(allowed or [])
    tech = (entities or {}).get("tech")
    ref = (entities or {}).get("project_ref", "")
    mapping: dict[str, list[tuple[str, dict]]] = {
        "greeting": [],
        "contact": [("get_contact_information", {})],
        "hire_lead": [("search_knowledge", {"top_k": 6}),
                      ("get_projects", {"tech": tech} if tech else {}),
                      ("get_relevant_sources", {})],
        "live_url": [("get_project_live_url", {"ref": ref})],
        "similar_project": [("search_knowledge", {"top_k": 8}),
                            ("get_projects", {"tech": tech} if tech else {})],
        "services": [("get_services", {})],
        "github_work": [("get_github_projects", {"tech": tech} if tech else {}),
                        ("search_knowledge", {"top_k": 6})],
        "products": [("get_products", {})],
        "project_detail": [("get_project_details", {"ref": ref}),
                           ("search_knowledge", {"top_k": 6})],
        "projects_list": [("get_projects", {"tech": tech} if tech else {})],
        "about_rajib": [("get_rajib_profile", {})],
        "about_rajiblabs": [("search_knowledge", {"top_k": 6}),
                            ("get_rajib_profile", {})],
        "fallback": [("search_knowledge", {"top_k": 6})],
    }
    return [(n, a) for n, a in mapping.get(intent, mapping["fallback"])
            if n in tools.PUBLIC_TOOL_NAMES and (not allowed_set or n in allowed_set)]


EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
PHONE_RE = re.compile(r"\+?\d[\d\s\-()]{6,18}\d")
NAME_RES = re.compile(r"(?:my name is|i am|i'm|this is|call me)\s+([A-Za-z][A-Za-z .'-]{1,40})",
                      re.IGNORECASE)


def extract_contact_bits(message: str) -> dict:
    """Pull email/phone/name mentions from free text (pure)."""
    text = message or ""
    out: dict = {}
    m = EMAIL_RE.search(text)
    if m:
        out["email"] = m.group(0)
    m = PHONE_RE.search(text)
    if m and len(re.sub(r"\D", "", m.group(0))) >= 7:
        out["phone"] = m.group(0).strip()
    m = NAME_RES.search(text)
    if m:
        out["name"] = re.sub(r"\s+", " ", m.group(1)).strip(" .")[:80]
    return out


_BUY_WORDS = ("hire", "proposal", "quote", "price", "cost",
              "build", "need", "contact", "call", "demo")


def wants_lead_flow(message: str, has_lead_or_idea: bool) -> bool:
    text = (message or "").lower()
    return has_lead_or_idea or any(w in text for w in _BUY_WORDS) \
        or bool(extract_contact_bits(message))


from app.services.kb_policy import (
    collect_allowed_urls as _collect_urls,
    validate_reply_urls as _validate_urls,
)


def collect_allowed_urls(tool_results: dict) -> set[str]:
    """Central KB implementation (kept importable here for compatibility)."""
    return _collect_urls(tool_results)


def validate_reply_urls(reply: str, allowed: set[str]) -> tuple[str, int]:
    """Strip any URL the tools didn't return. Returns (cleaned, removed)."""
    return _validate_urls(reply, allowed)


def filter_policy_sources(hits: list[dict], policy: dict | None) -> list[dict]:
    """Server-side knowledge guardrail: drop disallowed source types,
    order the rest by configured priority (unknown types denied)."""
    policy = policy or {}
    kept = []
    for h in hits:
        rule = policy.get(h.get("source_type", ""), {})
        if rule.get("public_allowed"):
            h = dict(h)
            h["_priority"] = rule.get("priority", 9)
            kept.append(h)
    kept.sort(key=lambda h: (h["_priority"], -(h.get("score") or 0)))
    return kept


def compose_tool_only(intent: str, results: dict, contact: dict,
                      fallback_message: str) -> tuple[str, list[dict]]:
    """Deterministic reply from verified tool output — no LLM, no invention."""
    sources = results.get("__sources__", [])
    if intent == "greeting":
        return ("Hi — I'm the RajibLabs Concierge Agent. Ask me about Rajib, "
                "projects, services, or GitHub work — or tell me about your project idea."), []
    if intent == "contact":
        c = results.get("get_contact_information", {}) or {}
        bits = [x for x in [
            f"Email: {', '.join(c.get('emails', []))}" if c.get("emails") else "",
            f"Phone: {c.get('primary_phone')}" if c.get("primary_phone") else "",
            f"WhatsApp: {c.get('whatsapp')}" if c.get("whatsapp") else "",
            f"LinkedIn: {c.get('linkedin')}" if c.get("linkedin") else "",
        ] if x]
        if not bits:
            return fallback_message, []
        return ("You can reach RajibLabs here:\n" + "\n".join(bits)), []
    if intent == "live_url":
        r = results.get("get_project_live_url", {}) or {}
        if r.get("project") and r.get("live_url"):
            return (f"Yes — {r['project']} is live at {r['live_url']}."), []
        if r.get("project"):
            return (f"I don't have a verified live URL for {r['project']} in the "
                    f"knowledge base. Ask me about the project itself, or I can "
                    f"connect you with RajibLabs."), []
        return fallback_message, []
    if intent in ("projects_list", "github_work", "products", "services") and sources:
        names = [s.get("title", "") for s in sources[:6] if s.get("title")]
        if names:
            return ("Here's what I found in verified RajibLabs knowledge:\n- "
                    + "\n- ".join(names)), sources
    return fallback_message, sources if intent != "greeting" else []


async def run_concierge_turn(db, message: str, session_token: str | None,
                             client_ip: str, preview: bool = False,
                             language: str = "en") -> dict:
    """One grounded concierge turn. preview=True runs without any writes.

    `language` localizes the final reply through the shared translation
    cache (content-hash keyed, so the first visitor bills at most one LLM
    call and everyone after is free). Retrieval/tools stay English-only."""
    try:
        from app.services import lang_service as _ls
        language, _ = await _ls.response_instruction(language, db)
    except Exception:
        language = "en"
    from app.services import lead_pipeline as _lp
    from app.services.lead_ai import AIService, AIError
    from app.services import leads as rules
    t0 = time.time()
    message = (message or "").strip()[:2000]
    agent = await agents.get_agent(db, AGENT_SLUG)
    contact0 = await tools.get_contact_information(db)
    emails0 = ", ".join((contact0.get("emails") or [])[:2])
    unavailable = (
        "Our AI agent is briefly unavailable. You can reach RajibLabs directly"
        + (f" at {emails0}." if emails0 else "."))
    if not agent or not agent.get("enabled") or not agent.get("public_enabled"):
        return {"reply": unavailable, "sources": [], "intent": "unavailable",
                "tools_called": [], "lead_captured": False, "missing_fields": [],
                "agent": AGENT_SLUG}

    intent, entities = detect_intent(message)
    if not preview:
        sess, token = await _lp.get_or_create_session(db, session_token, client_ip)
        await db["customer_messages"].insert_one({
            "conversation_id": str(sess["_id"]), "session_token": token,
            "sender": "user", "role": "user", "message": message, "content": message,
            "intent": intent, "agent_slug": AGENT_SLUG,
            "ai_provider": None, "ai_model": None, "usage": {}, "created_at": utcnow()})
    else:
        token, sess = (session_token or "preview"), {}

    allowed = agent.get("allowed_tools") or []
    calls = select_tools(intent, {**entities, "message": message}, allowed)
    # search tools need the actual query text
    calls = [(n, ({**a, "query": message} if n in ("search_knowledge", "get_relevant_sources") else a))
             for n, a in calls]
    results: dict = {}
    called: list[str] = []
    for name, args in calls:
        try:
            results[name] = await tools.run_public_tool(name, db, **args)
            called.append(name)
        except tools.ToolAuthError:
            continue
        except Exception as e:
            try:
                await log_error("concierge_tool", f"tool {name} failed",
                                str(e)[:1000], logger="app.services.concierge")
            except Exception:
                pass
    # guardrail: only policy-allowed RAG content may ground the answer
    policy = agent.get("knowledge_policy") or {}
    for key in ("search_knowledge",):
        if isinstance(results.get(key), list):
            results[key] = filter_policy_sources(results[key], policy)
    sources = []
    for h in (results.get("search_knowledge") or [])[:6]:
        sources.append({"title": h.get("title", ""), "url": h.get("url"),
                        "source_type": h.get("source_type", "")})
    for s in (results.get("get_relevant_sources") or [])[:6]:
        if s.get("title") and all(x.get("title") != s["title"] for x in sources):
            sources.append(s)
    # tool-derived sources: verified DB records also ground answers/URLs
    for key in ("get_projects", "get_github_projects", "get_products"):
        for item in (results.get(key) or [])[:6]:
            url = item.get("live_url") or item.get("url") or item.get("product_url")
            title = item.get("name") or item.get("title", "")
            if title and all(x.get("title") != title for x in sources):
                sources.append({"title": title, "url": url,
                                "source_type": "tool:" + key})
    _detail = results.get("get_project_details") or {}
    if _detail.get("name"):
        url = _detail.get("live_url") or _detail.get("github_url")
        if all(x.get("title") != _detail["name"] for x in sources):
            sources.append({"title": _detail["name"], "url": url,
                            "source_type": "tool:get_project_details"})
    results["__sources__"] = sources

    # lead flow: gradual, one field at a time (pipeline owns storage rules)
    lead_captured, missing, lead, idea, just_captured = False, [], {}, {}, False
    lead_mode = bool(agent.get("lead_capture_enabled")) and (
        intent in ("hire_lead", "contact") or wants_lead_flow(
            message, bool((sess.get("lead_id") if isinstance(sess, dict) else None)
                          or (await _lp.get_active_idea(db, token) if not preview else None))))
    if lead_mode and not preview:
        bits = extract_contact_bits(message)
        fields = {"name": bits.get("name", ""), "email": bits.get("email", ""),
                  "phone": bits.get("phone", "")}
        if any(fields.values()) or intent in ("hire_lead", "contact"):
            had_email = False
            try:
                if sess.get("lead_id"):
                    from bson import ObjectId
                    _prev = await db["customer_leads"].find_one(
                        {"_id": ObjectId(sess["lead_id"])})
                    had_email = bool(rules.valid_email((_prev or {}).get("email")))
            except Exception:
                pass
            lead, _ = await _lp.find_or_create_lead(db, fields, token, message)
            if len(message) > 10 and intent == "hire_lead":
                idea, _, _ = await _lp.upsert_idea(
                    db, token, str(lead["_id"]), {"description": message}, message)
            else:
                idea = await _lp.get_active_idea(db, token) or {}
            missing = rules.missing_fields_for(lead, idea)
            lead_captured = bool(rules.valid_email(lead.get("email")))
            just_captured = bool(lead_captured and not had_email and bits.get("email"))
    question = ""
    if lead_mode and missing:
        first = missing[0]
        question = {
            "name": "May I know your name?",
            "email": "What email should Rajib reply to?",
            "phone": "And a phone number where you can be reached? (or say 'skip')",
            "idea": "Briefly, what would you like to build or improve?",
        }.get(first, "")
    has_answer = any(bool(results.get(n)) for n, _ in calls if n != "get_relevant_sources")

    # compose: tool-only fast paths, else one small LLM call, else fallback
    fallback = agent.get("fallback_message") or "I don't have verified information about that."
    reply, used_llm, meta = fallback, False, {"ai_provider": None, "ai_model": None}
    if intent in ("greeting", "contact", "live_url") or (lead_mode and missing and not has_answer):
        reply, _ = compose_tool_only(intent, results, contact0, fallback)
        if lead_mode and missing and question and intent not in ("contact",):
            reply = (reply.rstrip() + f"\n\n{question}") if reply != fallback else question
        elif lead_mode and missing and question and intent == "contact" and reply == fallback:
            reply = question
    else:
        context = scrub_text(json.dumps(results, default=str)[:6000])
        allowed_urls = sorted(collect_allowed_urls(results))
        history = []
        if not preview:
            try:
                cur = db["customer_messages"].find(
                    {"session_token": token}).sort("created_at", -1).limit(5)
                history = [{"role": ("assistant" if d.get("sender") == "assistant" else "user"),
                            "content": (d.get("message") or "")[:400]}
                           async for d in cur][::-1]
            except Exception:
                history = []
        system = ((agent.get("system_prompt") or "") + "\nStyle: "
                  + str(agent.get("response_style") or "") + "\nHallucination policy: "
                  + str(agent.get("hallucination_policy") or "verified-only")
                  + "\nVerified URLs you may use (never invent others): "
                  + (", ".join(allowed_urls) if allowed_urls else "(none)")
                  + (f"\nLead follow-up: end with exactly this question: {question}"
                     if lead_mode and missing and question else ""))
        try:
            svc = AIService()
            out = await svc._complete(
                [{"role": "system", "content": system[:2500]},
                 *history,
                 {"role": "user", "content": f"Intent: {intent}\nVerified tool results:\n{context}"}],
                max_tokens=400, temperature=0.2, tag="concierge-reply")
            reply = str((out.get("data") or {}).get("reply") or "").strip() or fallback
            meta = {"ai_provider": out.get("provider"), "ai_model": out.get("model")}
            used_llm = True
        except (AIError, Exception):
            reply, _ = compose_tool_only(intent, results, contact0, fallback)
            if lead_mode and missing and question and reply == fallback:
                reply = question
    reply, _removed = validate_reply_urls(reply, set(collect_allowed_urls(results)))
    # Central hallucination gate (deterministic, no extra LLM call): validate
    # LLM-composed replies against evidence + resolved KB policy. Tool-only
    # replies are pre-grounded templates and skip this step.
    if used_llm and reply != fallback:
        try:
            from app.services import kb_policy as _kb
            _doc_ids = {h.get("document_id", "")
                        for h in (results.get("search_knowledge") or [])
                        if h.get("document_id")}
            _docs: list[dict] = []
            if _doc_ids and not preview:
                from bson import ObjectId as _Oid
                _oids = []
                for _did in _doc_ids:
                    try:
                        _oids.append(_Oid(_did))
                    except Exception:
                        pass
                if _oids:
                    _docs = [d async for d in
                             db["knowledge_documents"].find({"_id": {"$in": _oids}})]
            _pol = _kb.resolve_request_policy(
                {"hallucination_policy": agent.get("hallucination_policy"),
                 "fallback_message": agent.get("fallback_message")}, _docs)
            _ev = [(h.get("content") or "")
                   for h in (results.get("search_knowledge") or [])]
            _ev.append(scrub_text(json.dumps(
                {k: v for k, v in results.items() if not k.startswith("__")},
                default=str)[:4000]))
            _top = max([h.get("score") or 0
                        for h in (results.get("search_knowledge") or [])] or [0])
            _ok, _reason = _kb.validate_grounding(reply, _ev, _pol, _top)
            _needs_source = _pol["require_source"] and not any(
                s.get("url") for s in sources)
            if (not _ok) or _needs_source:
                if _pol["on_insufficient"] == "clarify":
                    reply = _pol["fallback_message"] + \
                        " Could you share which project or topic you mean?"
                else:
                    reply = _pol["fallback_message"]
                sources = []
        except Exception:
            pass
    if language != "en":
        # Localize the composed reply (tool-only or LLM): cache-first, so the
        # steady state costs zero LLM calls. Falls back to English silently.
        try:
            from app.services.translation_service import (
                TranslationService as _TS, source_hash as _sh)
            reply, _ = await _TS.get_text(
                f"concierge.turn.{_sh(reply)[:12]}", reply, language,
                context="concierge chat reply", generate=True)
        except Exception as e:
            log.warning("concierge reply localization skipped: %s", e)
    if just_captured:
        first = str((lead.get("name") or "")).strip().split()[0:1]
        hello = f"Thanks{(' ' + first[0]) if first else ''} — I've shared your details with RajibLabs. Rajib will get back to you soon."
        if hello.split("—")[0].lower() not in reply.lower()[:120]:
            reply = f"{hello}\n\n{reply}".strip()

    duration_ms = int((time.time() - t0) * 1000)
    if not preview:
        try:
            await db["customer_messages"].insert_one({
                "conversation_id": str(sess["_id"]), "session_token": token,
                "sender": "assistant", "role": "assistant",
                "message": reply, "content": reply,
                "intent": intent, "tools_called": called,
                "sources_used": sources, "lead_id": str(lead["_id"]) if lead else None,
                "idea_id": str(idea["_id"]) if idea else None,
                "agent_slug": AGENT_SLUG, "duration_ms": duration_ms,
                "ai_provider": meta["ai_provider"], "ai_model": meta["ai_model"],
                "usage": {}, "created_at": utcnow()})
            await db["customer_conversations"].update_one(
                {"_id": sess["_id"]}, {"$set": {"last_message_at": utcnow()}})
            await agents.bump_stat(db, AGENT_SLUG, "turns")
            if called:
                await agents.bump_stat(db, AGENT_SLUG, "tool_calls", len(called))
            if lead_captured:
                await agents.bump_stat(db, AGENT_SLUG, "leads")
        except Exception as e:
            try:
                await log_error("concierge_store", "assistant turn persist failed",
                                str(e)[:1000], logger="app.services.concierge")
            except Exception:
                pass
            await agents.bump_stat(db, AGENT_SLUG, "errors")
    return {"reply": reply, "sources": sources, "intent": intent,
            "tools_called": called, "session_token": token, "session_id": token,
            "lead_captured": lead_captured, "missing_fields": missing,
            "agent": AGENT_SLUG, "used_llm": used_llm, "duration_ms": duration_ms,
            "language": language}
