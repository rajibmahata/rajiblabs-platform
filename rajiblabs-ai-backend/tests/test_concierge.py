"""Concierge agent tests: intent, tools, guardrails, grounding, leads.

Pure unit tests run everywhere; live tests need MongoDB (skip otherwise).
LLM calls are monkeypatched to explode unless the test explicitly allows
them — proving the cost-efficient tool-only paths.
"""
import pytest

from app.services.concierge import (
    SUGGESTED_STARTERS, collect_allowed_urls, compose_tool_only,
    detect_intent, extract_contact_bits, filter_policy_sources,
    select_tools, validate_reply_urls, wants_lead_flow,
    is_business_application_intent, is_universal_business_intent,
    _compute_conversation_stage,
    _get_capture_prompt, _is_capture_stage, _next_capture_stage,
    STAGE_DISCOVER_INTENT, STAGE_BUSINESS_APPLICATION, STAGE_CAPTURE_NAME,
    STAGE_CAPTURE_EMAIL, STAGE_CAPTURE_PHONE, STAGE_CONTACT_CAPTURED,
    STAGE_PROJECT_DISCOVERY,
)
from app.services.agent_tools import (
    ADMIN_ONLY_TOOLS, PUBLIC_TOOL_NAMES, _clean, run_public_tool,
)


async def _live_db():
    try:
        from app.database import get_db
        db = get_db()
        await db.command("ping")
        return db
    except Exception:
        pytest.skip("MongoDB not running locally")


# ── intent detection ──

INTENT_CASES = [
    ("Hi there", "greeting"), ("hello", "greeting"),
    ("Tell me about Rajib", "about_rajib"),
    ("Who is Rajib Mahata?", "about_rajib"),
    ("Do you know about RajibLabs?", "about_rajiblabs"),
    ("About RajibLabs", "about_rajiblabs"),
    ("What is RajibLabs?", "about_rajiblabs"),
    ("What projects has Rajib completed?", "projects_list"),
    ("Which projects use Azure?", "projects_list"),
    ("Tell me about PestFlow", "project_detail"),
    ("What technologies were used?", "project_detail"),
    ("What problem did it solve?", "project_detail"),
    ("Tell me about this project", "project_detail"),
    ("Is there a live URL for this project?", "live_url"),
    ("Is the pharmacy app live?", "live_url"),
    ("Show me similar projects", "similar_project"),
    ("I need something similar to PestFlow", "similar_project"),
    ("What services does RajibLabs provide?", "services"),
    ("Show me Rajib's GitHub work", "github_work"),
    ("Tell me about Page Flow", "products"),
    ("Contact RajibLabs", "contact"),
    ("What is your email?", "contact"),
    ("I have a project idea", "hire_lead"),
    ("I want to hire you for a website", "hire_lead"),
    ("How much does a website cost?", "hire_lead"),
    ("random gibberish xyzzy", "fallback"),
]


@pytest.mark.parametrize("message,expected", INTENT_CASES)
def test_intent_detection(message, expected):
    assert detect_intent(message)[0] == expected


def test_starters_all_route_sensibly():
    for s in SUGGESTED_STARTERS:
        assert detect_intent(s)[0] != "fallback", s


def test_entity_extraction():
    _, e = detect_intent("Which projects use Azure?")
    assert e.get("tech") == "azure"
    _, e = detect_intent('Tell me about "Pest Flow" please')
    assert e.get("project_ref") == "Pest Flow"


# ── tool selection + authorization ──

def test_tool_selection_mapping():
    assert select_tools("live_url", {"project_ref": "X"}, None)[0][0] == "get_project_live_url"
    assert "get_contact_information" in [n for n, _ in select_tools("contact", {}, None)]
    assert select_tools("greeting", {}, None) == []
    assert select_tools("nonsense-intent", {}, None)[0][0] == "search_knowledge"


def test_tool_selection_respects_allow_list():
    got = select_tools("contact", {}, ["search_knowledge"])
    assert got == []  # contact tool pruned → deterministic question path still safe


@pytest.mark.asyncio
async def test_tool_authorization_rejects():
    from app.services.agent_tools import ToolAuthError
    with pytest.raises(ToolAuthError):
        await run_public_tool("run_daily_agent")
    with pytest.raises(ToolAuthError):
        await run_public_tool("set_github_token")
    with pytest.raises(ToolAuthError):
        await run_public_tool("no_such_tool")
    for name in ADMIN_ONLY_TOOLS:
        with pytest.raises(ToolAuthError):
            await run_public_tool(name)


def test_clean_drops_secret_keys():
    dirty = {"name": "x", "password": "p", "nested": {"api_key": "k", "ok": 1},
             "token_list": [], "github_url": "https://github.com/a/b"}
    out = _clean(dirty)
    assert "password" not in out and "api_key" not in out["nested"]
    assert out["nested"]["ok"] == 1 and out["github_url"].endswith("/a/b")


# ── guardrails + URL validation (pure) ──

def test_policy_filter_denies_unknown_and_orders():
    policy = {"project": {"public_allowed": True, "priority": 1},
              "github_commit": {"public_allowed": False, "priority": 4}}
    hits = [
        {"source_type": "github_commit", "score": 0.99},
        {"source_type": "mystery_type", "score": 0.99},
        {"source_type": "project", "score": 0.5},
    ]
    kept = filter_policy_sources(hits, policy)
    assert [h["source_type"] for h in kept] == ["project"]


def test_url_validation_strips_invented():
    allowed = {"https://rajiblabs.com", "https://live.example.com/x"}
    reply = "See https://live.example.com/x and https://evil.example.com/y now."
    cleaned, removed = validate_reply_urls(reply, allowed)
    assert removed == 1 and "evil.example.com" not in cleaned
    assert "https://live.example.com/x" in cleaned


def test_allowed_url_collection():
    urls = collect_allowed_urls({"a": {"live_url": "https://a.example.com/p,"}})
    assert "https://a.example.com/p" in urls and "https://rajiblabs.com" in urls


# ── hallucination control (pure composers) ──

def test_fallback_never_invents():
    fb = "FALLBACK-MARKER"
    reply, sources = compose_tool_only("project_detail", {}, {}, fb)
    assert reply == fb and sources == []
    reply, _ = compose_tool_only("live_url", {"get_project_live_url": {"project": None}}, {}, fb)
    assert reply == fb
    reply, _ = compose_tool_only(
        "live_url", {"get_project_live_url": {"project": "X", "live_url": None}}, {}, fb)
    assert "X" in reply and "http" not in reply  # no URL invented


def test_contact_composer_uses_only_verified():
    reply, _ = compose_tool_only(
        "contact", {"get_contact_information": {"emails": ["a@b.c"], "primary_phone": "+123"}}, {}, "FB")
    assert "a@b.c" in reply and "+123" in reply


# ── lead helpers (pure) ──

def test_contact_extraction():
    bits = extract_contact_bits("Hi, my name is Ada Lovelace, email ada@x.io, phone +1 555 123 4567")
    assert bits["email"] == "ada@x.io" and "Ada" in bits["name"]
    assert "555" in bits["phone"]
    assert extract_contact_bits("just browsing thanks") == {}


def test_lead_flow_trigger():
    assert wants_lead_flow("I want to hire you", False) is True
    assert wants_lead_flow("my email is a@b.c", False) is True
    assert wants_lead_flow("tell me about projects", False) is False
    assert wants_lead_flow("tell me about projects", True) is True


# ── live: config, tools, full turns ──

@pytest.mark.asyncio
async def test_agent_config_crud_live(monkeypatch):
    db = await _live_db()
    from app.services import agent_config as ac
    agent = await ac.get_agent(db, ac.CONCIERGE_SLUG)
    assert agent["enabled"] and agent["public_enabled"]
    assert "get_projects" in agent["allowed_tools"]
    updated = await ac.update_agent(db, ac.CONCIERGE_SLUG,
                                    {"description": "e2e", "nope": 1}, actor="e2e")
    assert updated["description"] == "e2e" and "nope" not in updated
    with pytest.raises(ValueError):
        await ac.create_agent(db, {"slug": ac.CONCIERGE_SLUG, "name": "dup"})
    doc = await ac.create_agent(db, {"slug": "e2e-proposal", "name": "E2E",
                                     "agent_type": "proposal"})
    assert doc["public_enabled"] is False
    await db["ai_agents"].delete_many({"slug": "e2e-proposal"})
    await ac.update_agent(db, ac.CONCIERGE_SLUG, {"description": agent["description"]})


@pytest.mark.asyncio
async def test_public_tools_live():
    db = await _live_db()
    from app.services import agent_tools as at
    prof = await at.get_rajib_profile(db)
    assert prof.get("full_name") and "password" not in str(prof).lower()
    projs = await at.get_projects(db)
    assert isinstance(projs, list)
    contact = await at.get_contact_information(db)
    assert contact.get("emails") and contact.get("website") == "https://rajiblabs.com"
    gh = await at.get_github_projects(db)
    for r in gh:
        assert not {"token", "password", "secret"} & {k.lower() for k in r.keys()}
        assert r.get("url", "").startswith("https://github.com/") or not r.get("url")


@pytest.mark.asyncio
async def test_tool_only_turns_skip_llm_live(monkeypatch):
    from app.services import concierge as cg
    from app.services.lead_ai import AIService
    db = await _live_db()

    async def _boom(*a, **k):
        raise AssertionError("LLM must not be called on tool-only paths")

    monkeypatch.setattr(AIService, "_complete", _boom)
    token = None
    try:
        r = await cg.run_concierge_turn(db, "Hello!", None, "127.0.0.1")
        assert r["intent"] == "greeting" and r["tools_called"] == []
        r = await cg.run_concierge_turn(db, "What is your email?", None, "127.0.0.1")
        assert r["intent"] == "contact"
        # Contact intent now triggers universal capture (asks for name first)
        assert "name" in r["reply"].lower()
        token = r["session_token"]
    finally:
        if token:
            await db["customer_messages"].delete_many({"session_token": token})
            await db["customer_conversations"].delete_many({"session_token": token})


@pytest.mark.asyncio
async def test_lead_capture_flow_live():
    from app.services import concierge as cg
    db = await _live_db()
    token = None
    try:
        r1 = await cg.run_concierge_turn(
            db, "Hi, I need a website built for my bakery", None, "127.0.0.1")
        assert r1["intent"] == "business_application"
        token = r1["session_token"]
        # business_application fast path should ask for name
        assert "name" in r1["reply"].lower()
        r2 = await cg.run_concierge_turn(db, "My name is Baker Ted", token, "127.0.0.1")
        assert "email" in r2["reply"].lower()
        r3 = await cg.run_concierge_turn(db, "ted@bakery.example", token, "127.0.0.1")
        assert "phone" in r3["reply"].lower() or "reach" in r3["reply"].lower()
        r4 = await cg.run_concierge_turn(db, "+1 555 123 4567", token, "127.0.0.1")
        assert r4["reply"]
    finally:
        if token:
            lead = await db["customer_leads"].find_one(
                {"email": "ted@bakery.example"})
            await db["customer_messages"].delete_many({"session_token": token})
            await db["customer_conversations"].delete_many({"session_token": token})
            await db["ideas"].delete_many({"session_id": token})
            if lead:
                await db["customer_leads"].delete_one({"_id": lead["_id"]})


@pytest.mark.asyncio
async def test_disabled_agent_degrades_live():
    from app.services import concierge as cg
    from app.services import agent_config as ac
    db = await _live_db()
    agent = await ac.get_agent(db, ac.CONCIERGE_SLUG)
    try:
        await ac.update_agent(db, ac.CONCIERGE_SLUG, {"enabled": False})
        r = await cg.run_concierge_turn(db, "Hello", None, "127.0.0.1")
        assert r["intent"] == "unavailable" and r["tools_called"] == []
    finally:
        await ac.update_agent(db, ac.CONCIERGE_SLUG, {"enabled": agent["enabled"]})


@pytest.mark.asyncio
async def test_provider_failure_falls_back_live(monkeypatch):
    from app.services import concierge as cg
    from app.services.lead_ai import AIService, AIError
    db = await _live_db()

    async def _fail(*a, **k):
        raise AIError("down")

    monkeypatch.setattr(AIService, "_complete", _fail)
    token = None
    try:
        r = await cg.run_concierge_turn(db, "What is RajibLabs?", None, "127.0.0.1")
        assert r["reply"]
        low = r["reply"].lower()
        assert ("http" not in low) or ("verified" in low) or ("rajiblabs.com" in low)
        token = r["session_token"]
    finally:
        if token:
            await db["customer_messages"].delete_many({"session_token": token})
            await db["customer_conversations"].delete_many({"session_token": token})


@pytest.mark.asyncio
async def test_admin_endpoints_require_auth():
    from httpx import ASGITransport, AsyncClient
    from app.main import create_app
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app),
                           base_url="http://test") as c:
        assert (await c.get("/api/admin/agents")).status_code == 401
        assert (await c.get("/api/admin/agents/rajiblabs-concierge")).status_code == 401
        assert (await c.post("/api/admin/agents/rajiblabs-concierge/test",
                             json={"message": "hi"})).status_code == 401
        r = await c.get("/api/public/agent/config")
        assert r.status_code in (200, 503)


# ── live-agent UX: intents, greeting warmth, card data (pure, no LLM) ──

LIVE_AGENT_INTENT_CASES = [
    ("Are you hiring developers?", "recruiter"),
    ("Is Rajib open to new roles?", "recruiter"),
    ("Tell me about Rajib's career", "career"),
    ("Where did Rajib work before?", "career"),
    ("How would you design a SaaS platform?", "business_application"),
    ("Can Rajib build an AI agent system?", "hire_lead"),
    ("How does PestFlow compare to alternatives?", "technical"),
    ("I have an idea for a restaurant app", "hire_lead"),
    ("Help me explore a prototype", "idea_discovery"),
    ("thanks!", "general_conversation"),
    ("tell me more", "general_conversation"),
    ("yes", "general_conversation"),
    # existing behavior must not shift
    ("Tell me about Rajib", "about_rajib"),
    ("I have a project idea", "hire_lead"),
    ("What is PestFlow?", "project_detail"),
    ("What is Docusign Hub?", "project_detail"),
]


@pytest.mark.parametrize("message,expected", LIVE_AGENT_INTENT_CASES)
def test_live_agent_intents(message, expected):
    from app.services.concierge import detect_intent
    assert detect_intent(message)[0] == expected


def test_live_agent_tool_mapping():
    from app.services.concierge import select_tools
    names = [n for n, _ in select_tools("recruiter", {}, None)]
    assert "get_rajib_profile" in names
    names = [n for n, _ in select_tools("technical", {"tech": "azure"}, None)]
    assert "search_knowledge" in names
    names = [n for n, _ in select_tools("idea_discovery", {}, None)]
    assert "get_projects" in names
    names = [n for n, _ in select_tools("general_conversation", {}, None)]
    assert "search_knowledge" in names
    names = [n for n, _ in select_tools("career", {}, None)]
    assert "get_rajib_profile" in names


def test_greeting_is_warm_not_robotic():
    from app.services.concierge import compose_tool_only
    reply, sources = compose_tool_only("greeting", {}, {}, "FB")
    assert sources == []
    assert "Live Agent" in reply
    assert "Concierge Agent" not in reply
    for banned in ("How can I assist you", "How may I", "As an AI"):
        assert banned not in reply


def test_about_composer_stays_verified_and_offers_next_step():
    from app.services.concierge import compose_tool_only
    p = {"full_name": "Rajib Mahata", "title": "Architect",
         "bio": "Builds systems.", "skills": ["A", "B"]}
    reply, sources = compose_tool_only("about_rajib", {"get_rajib_profile": p}, {}, "FB")
    assert "Rajib Mahata is" in reply and "Builds systems." in reply
    assert "walk you through" in reply
    assert sources and sources[0]["source_type"] == "profile"


def test_project_composer_no_marketing_voice():
    from app.services.concierge import compose_tool_only
    d = {"name": "PestFlow", "description": "Manages pest-control ops.",
         "tech_stack": [".NET"], "github_url": "https://github.com/x/y",
         "live_url": ""}
    reply, sources = compose_tool_only("project_detail", {"get_project_details": d}, {}, "FB")
    assert reply.startswith("PestFlow is")
    assert "comprehensive end-to-end" not in reply.lower()
    assert "GitHub: https://github.com/x/y" in reply
    assert "Live:" not in reply  # no live URL invented


def test_response_guidance_bans_stock_phrases():
    from app.services.concierge import RESPONSE_GUIDANCE
    for banned in ("Certainly", "Absolutely", "Great question", "Based on the information",
                   "In conclusion", "AI model"):
        assert banned in RESPONSE_GUIDANCE


def test_social_ack_needs_no_llm():
    from app.services.concierge import compose_tool_only
    reply, sources = compose_tool_only("general_conversation", {}, {}, "FB",
                                       message="thanks a lot!")
    assert "welcome" in reply.lower() and sources == []
    reply, _ = compose_tool_only("general_conversation", {}, {}, "FB",
                                 message="bye for now")
    assert "Goodbye" in reply
    # non-social general turns still fall through honestly
    reply, _ = compose_tool_only("general_conversation", {}, {}, "FB",
                                 message="ok")
    assert reply == "FB"


def test_social_ack_is_deterministic():
    from app.services.concierge import compose_tool_only
    # thanks/bye short-circuit without tools or LLM-shaped content
    r, s = compose_tool_only("general_conversation", {}, {}, "FB",
                             message="thanks so much")
    assert "welcome" in r.lower() and s == []
    r, _ = compose_tool_only("general_conversation", {}, {}, "FB",
                             message="bye!")
    assert "Goodbye" in r


# ── business application intent detection ──

BUSINESS_APPLICATION_CASES = [
    ("I want to create an application for inventory management", "business_application"),
    ("I need a website built for my restaurant", "business_application"),
    ("I'd like to develop a SaaS platform for HR management", "business_application"),
    ("Help me make a tool for tracking expenses", "business_application"),
    ("Looking to build a system for order processing", "business_application"),
    ("I have a business idea for a marketplace app", "business_application"),
    ("I want to launch an MVP for my startup", "business_application"),
    ("Need a custom software solution for our warehouse", "business_application"),
    ("I want to automate our invoice processing", "business_application"),
    # hire_lead with application keywords should also match
    ("I want to hire you to build a web app", "hire_lead"),
    ("Can you build a mobile app for booking appointments?", "hire_lead"),
    ("I need a developer for my SaaS product", "business_application"),
    # Non-application intents should not match
    ("What projects has Rajib completed?", "projects_list"),
    ("Tell me about Rajib", "about_rajib"),
    ("Contact RajibLabs", "contact"),
]


@pytest.mark.parametrize("message,expected", BUSINESS_APPLICATION_CASES)
def test_business_application_intent_detection(message, expected):
    intent, _ = detect_intent(message)
    assert intent == expected


def test_business_application_tool_mapping():
    names = [n for n, _ in select_tools("business_application", {}, None)]
    assert "search_knowledge" in names
    assert "get_projects" in names
    assert "get_relevant_sources" in names


def test_is_business_application_intent():
    assert is_business_application_intent("business_application", "I want to build an app") is True
    assert is_business_application_intent("hire_lead", "I need a website") is True
    assert is_business_application_intent("hire_lead", "How much does it cost?") is False
    assert is_business_application_intent("idea_discovery", "I have an app idea") is True
    assert is_business_application_intent("about_rajib", "Tell me about Rajib") is False
    assert is_business_application_intent("contact", "What's your email?") is False


# ── conversation stage state machine (pure) ──

def test_stage_computation_from_discover_intent():
    """Starting from DISCOVER_INTENT, business intent moves to BUSINESS_APPLICATION."""
    stage = _compute_conversation_stage(
        "I want to create an application", {}, {}, STAGE_DISCOVER_INTENT)
    assert stage == STAGE_BUSINESS_APPLICATION


def test_stage_computation_business_to_name():
    """After business intent detected, next stage is CAPTURE_NAME."""
    stage = _compute_conversation_stage(
        "I want to build an app", {}, {}, STAGE_BUSINESS_APPLICATION)
    assert stage == STAGE_CAPTURE_NAME


def test_stage_computation_name_provided():
    """When name is provided in CAPTURE_NAME, advance to CAPTURE_EMAIL."""
    stage = _compute_conversation_stage(
        "My name is John Smith", {}, {}, STAGE_CAPTURE_NAME)
    assert stage == STAGE_CAPTURE_EMAIL


def test_stage_computation_name_not_provided():
    """When name is NOT provided in CAPTURE_NAME, stay in CAPTURE_NAME."""
    stage = _compute_conversation_stage(
        "just browsing", {}, {}, STAGE_CAPTURE_NAME)
    assert stage == STAGE_CAPTURE_NAME


def test_stage_computation_email_provided():
    """When email is provided in CAPTURE_EMAIL, advance to CAPTURE_PHONE."""
    stage = _compute_conversation_stage(
        "john@example.com", {}, {}, STAGE_CAPTURE_EMAIL)
    assert stage == STAGE_CAPTURE_PHONE


def test_stage_computation_email_not_provided():
    """When email is NOT provided in CAPTURE_EMAIL, stay in CAPTURE_EMAIL."""
    stage = _compute_conversation_stage(
        "not sure yet", {}, {}, STAGE_CAPTURE_EMAIL)
    assert stage == STAGE_CAPTURE_EMAIL


def test_stage_computation_phone_provided():
    """When phone is provided in CAPTURE_PHONE, advance to CONTACT_CAPTURED."""
    stage = _compute_conversation_stage(
        "+1 555 123 4567", {}, {}, STAGE_CAPTURE_PHONE)
    assert stage == STAGE_CONTACT_CAPTURED


def test_stage_computation_phone_skip():
    """When 'skip' is provided in CAPTURE_PHONE, advance to CONTACT_CAPTURED."""
    stage = _compute_conversation_stage(
        "skip", {}, {}, STAGE_CAPTURE_PHONE)
    assert stage == STAGE_CONTACT_CAPTURED


def test_stage_computation_phone_not_provided():
    """When phone is NOT provided in CAPTURE_PHONE, stay in CAPTURE_PHONE."""
    stage = _compute_conversation_stage(
        "let me think", {}, {}, STAGE_CAPTURE_PHONE)
    assert stage == STAGE_CAPTURE_PHONE


def test_stage_computation_existing_lead_fields():
    """If lead already has fields, skip those stages."""
    lead = {"name": "John", "email": "john@example.com"}
    stage = _compute_conversation_stage(
        "I want to build an app", lead, {}, STAGE_DISCOVER_INTENT)
    # Should jump to CAPTURE_PHONE since name and email already exist
    assert stage == STAGE_CAPTURE_PHONE


def test_stage_computation_all_fields_present():
    """If all fields are present, jump to CONTACT_CAPTURED."""
    lead = {"name": "John", "email": "john@example.com", "phone": "+15551234567"}
    stage = _compute_conversation_stage(
        "Let's proceed", lead, {}, STAGE_CAPTURE_NAME)
    assert stage == STAGE_CONTACT_CAPTURED


def test_stage_computation_project_discovery_stays():
    """Once in PROJECT_DISCOVERY, stay there."""
    stage = _compute_conversation_stage(
        "Tell me more", {}, {}, STAGE_PROJECT_DISCOVERY)
    assert stage == STAGE_PROJECT_DISCOVERY


def test_stage_computation_contact_captured_stays():
    """Once in CONTACT_CAPTURED, stay there."""
    stage = _compute_conversation_stage(
        "Let's talk about my project", {}, {}, STAGE_CONTACT_CAPTURED)
    assert stage == STAGE_CONTACT_CAPTURED


def test_is_capture_stage():
    assert _is_capture_stage(STAGE_BUSINESS_APPLICATION) is True
    assert _is_capture_stage(STAGE_CAPTURE_NAME) is True
    assert _is_capture_stage(STAGE_CAPTURE_EMAIL) is True
    assert _is_capture_stage(STAGE_CAPTURE_PHONE) is True
    assert _is_capture_stage(STAGE_DISCOVER_INTENT) is False
    assert _is_capture_stage(STAGE_CONTACT_CAPTURED) is False
    assert _is_capture_stage(STAGE_PROJECT_DISCOVERY) is False


def test_next_capture_stage():
    assert _next_capture_stage(STAGE_BUSINESS_APPLICATION) == STAGE_CAPTURE_NAME
    assert _next_capture_stage(STAGE_CAPTURE_NAME) == STAGE_CAPTURE_EMAIL
    assert _next_capture_stage(STAGE_CAPTURE_EMAIL) == STAGE_CAPTURE_PHONE
    assert _next_capture_stage(STAGE_CAPTURE_PHONE) == STAGE_CONTACT_CAPTURED
    assert _next_capture_stage(STAGE_CONTACT_CAPTURED) == STAGE_PROJECT_DISCOVERY
    assert _next_capture_stage(STAGE_PROJECT_DISCOVERY) == STAGE_PROJECT_DISCOVERY


# ── capture prompts (pure) ──

def test_capture_prompt_business_application():
    reply, next_stage = _get_capture_prompt(
        STAGE_BUSINESS_APPLICATION, {}, {}, "I want to build an app")
    assert "exciting project" in reply.lower() or "name" in reply.lower()
    assert next_stage == STAGE_CAPTURE_NAME


def test_capture_prompt_name_not_provided():
    reply, next_stage = _get_capture_prompt(
        STAGE_CAPTURE_NAME, {}, {}, "just browsing")
    assert "name" in reply.lower()
    assert next_stage == STAGE_CAPTURE_NAME


def test_capture_prompt_name_provided():
    reply, next_stage = _get_capture_prompt(
        STAGE_CAPTURE_NAME, {}, {}, "My name is John Smith")
    assert "email" in reply.lower() or "john" in reply.lower()
    assert next_stage == STAGE_CAPTURE_EMAIL


def test_capture_prompt_email_not_provided():
    reply, next_stage = _get_capture_prompt(
        STAGE_CAPTURE_EMAIL, {}, {}, "not sure")
    assert "email" in reply.lower()
    assert next_stage == STAGE_CAPTURE_EMAIL


def test_capture_prompt_email_provided():
    reply, next_stage = _get_capture_prompt(
        STAGE_CAPTURE_EMAIL, {}, {}, "john@example.com")
    assert "phone" in reply.lower() or "reach" in reply.lower()
    assert next_stage == STAGE_CAPTURE_PHONE


def test_capture_prompt_phone_skip():
    reply, next_stage = _get_capture_prompt(
        STAGE_CAPTURE_PHONE, {}, {}, "skip")
    assert "talk" in reply.lower() or "project" in reply.lower() or "build" in reply.lower()
    assert next_stage == STAGE_CONTACT_CAPTURED


def test_capture_prompt_phone_provided():
    reply, next_stage = _get_capture_prompt(
        STAGE_CAPTURE_PHONE, {}, {}, "+1 555 123 4567")
    assert "talk" in reply.lower() or "project" in reply.lower() or "build" in reply.lower()
    assert next_stage == STAGE_CONTACT_CAPTURED


def test_capture_prompt_phone_not_provided():
    reply, next_stage = _get_capture_prompt(
        STAGE_CAPTURE_PHONE, {}, {}, "let me think")
    assert "phone" in reply.lower() or "reach" in reply.lower()
    assert next_stage == STAGE_CAPTURE_PHONE


# ── live: business application flow ──

@pytest.mark.asyncio
async def test_business_application_fast_path_live(monkeypatch):
    """Business application intent triggers deterministic fast path (no LLM)."""
    from app.services import concierge as cg
    from app.services.lead_ai import AIService
    db = await _live_db()

    async def _boom(*a, **k):
        raise AssertionError("LLM must not be called on capture fast path")

    monkeypatch.setattr(AIService, "_complete", _boom)
    token = None
    try:
        r1 = await cg.run_concierge_turn(
            db, "I want to create an application for managing inventory", None, "127.0.0.1")
        assert r1["intent"] == "business_application"
        token = r1["session_token"]
        # Should get a deterministic reply asking for name
        assert r1["reply"]
        assert "name" in r1["reply"].lower()
        assert r1["used_llm"] is False

        # Provide name
        r2 = await cg.run_concierge_turn(db, "My name is Alice Johnson", token, "127.0.0.1")
        assert r2["reply"]
        assert "email" in r2["reply"].lower()
        assert r2["used_llm"] is False

        # Provide email
        r3 = await cg.run_concierge_turn(db, "alice@example.com", token, "127.0.0.1")
        assert r3["reply"]
        assert "phone" in r3["reply"].lower() or "reach" in r3["reply"].lower()
        assert r3["used_llm"] is False

        # Provide phone
        r4 = await cg.run_concierge_turn(db, "+1 555 123 4567", token, "127.0.0.1")
        assert r4["reply"]
        assert r4["used_llm"] is False
        # After phone, should transition to PROJECT_DISCOVERY
    finally:
        if token:
            lead = await db["customer_leads"].find_one({"email": "alice@example.com"})
            await db["customer_messages"].delete_many({"session_token": token})
            await db["customer_conversations"].delete_many({"session_token": token})
            await db["ideas"].delete_many({"session_id": token})
            if lead:
                await db["customer_leads"].delete_one({"_id": lead["_id"]})


@pytest.mark.asyncio
async def test_business_application_skip_phone_live(monkeypatch):
    """Skip phone during capture flow."""
    from app.services import concierge as cg
    from app.services.lead_ai import AIService
    db = await _live_db()

    async def _boom(*a, **k):
        raise AssertionError("LLM must not be called on capture fast path")

    monkeypatch.setattr(AIService, "_complete", _boom)
    token = None
    try:
        r1 = await cg.run_concierge_turn(
            db, "I need a SaaS platform", None, "127.0.0.1")
        token = r1["session_token"]

        r2 = await cg.run_concierge_turn(db, "Bob Smith", token, "127.0.0.1")
        r3 = await cg.run_concierge_turn(db, "bob@test.com", token, "127.0.0.1")
        r4 = await cg.run_concierge_turn(db, "skip", token, "127.0.0.1")
        assert r4["reply"]
        assert r4["used_llm"] is False
    finally:
        if token:
            lead = await db["customer_leads"].find_one({"email": "bob@test.com"})
            await db["customer_messages"].delete_many({"session_token": token})
            await db["customer_conversations"].delete_many({"session_token": token})
            await db["ideas"].delete_many({"session_id": token})
            if lead:
                await db["customer_leads"].delete_one({"_id": lead["_id"]})


@pytest.mark.asyncio
async def test_business_application_batch_input_live(monkeypatch):
    """Batch all contact fields in one message during capture."""
    from app.services import concierge as cg
    from app.services.lead_ai import AIService
    db = await _live_db()

    async def _boom(*a, **k):
        raise AssertionError("LLM must not be called on capture fast path")

    monkeypatch.setattr(AIService, "_complete", _boom)
    token = None
    try:
        r1 = await cg.run_concierge_turn(
            db, "I want to build an app", None, "127.0.0.1")
        token = r1["session_token"]

        # Provide all fields at once
        r2 = await cg.run_concierge_turn(
            db, "My name is Carol, email carol@test.com, phone +1 555 999 0000",
            token, "127.0.0.1")
        assert r2["reply"]
        assert r2["used_llm"] is False
    finally:
        if token:
            lead = await db["customer_leads"].find_one({"email": "carol@test.com"})
            await db["customer_messages"].delete_many({"session_token": token})
            await db["customer_conversations"].delete_many({"session_token": token})
            await db["ideas"].delete_many({"session_id": token})
            if lead:
                await db["customer_leads"].delete_one({"_id": lead["_id"]})


@pytest.mark.asyncio
async def test_regular_chat_not_affected_live(monkeypatch):
    """Regular chat intents still work through normal path."""
    from app.services import concierge as cg
    from app.services.lead_ai import AIService
    db = await _live_db()

    async def _boom(*a, **k):
        raise AssertionError("LLM must not be called on greeting/contact fast paths")

    monkeypatch.setattr(AIService, "_complete", _boom)
    token = None
    try:
        r = await cg.run_concierge_turn(db, "Hello!", None, "127.0.0.1")
        assert r["intent"] == "greeting"
        token = r["session_token"]
        r = await cg.run_concierge_turn(db, "What is your email?", token, "127.0.0.1")
        assert r["intent"] == "contact"
        # Contact intent now triggers universal capture (asks for name first)
        assert "name" in r["reply"].lower()
    finally:
        if token:
            await db["customer_messages"].delete_many({"session_token": token})
            await db["customer_conversations"].delete_many({"session_token": token})


# ── universal lead capture tests ──
# Tests for the universal contact capture system that works across ALL
# conversation types (services, products, technical, contact, etc.)

def test_universal_intent_services_triggers_capture():
    """Services inquiry should trigger contact capture."""
    intent, _ = detect_intent("What services do you offer?")
    assert intent == "services"
    assert is_universal_business_intent(intent, "What services do you offer?")


def test_universal_intent_products_triggers_capture():
    """Product inquiry should trigger contact capture."""
    intent, _ = detect_intent("Tell me about DocuFlow")
    assert intent == "products"
    assert is_universal_business_intent(intent, "Tell me about DocuFlow")


def test_universal_intent_contact_triggers_capture():
    """Contact request should trigger contact capture."""
    intent, _ = detect_intent("How can I contact Rajib?")
    assert intent == "contact"
    assert is_universal_business_intent(intent, "How can I contact Rajib?")


def test_universal_intent_technical_triggers_capture():
    """Technical question should trigger contact capture."""
    intent, _ = detect_intent("How would you architect a microservices system?")
    assert intent == "technical"
    assert is_universal_business_intent(intent, "How would you architect a microservices system?")


def test_universal_intent_about_rajiblabs_triggers_capture():
    """Company inquiry should trigger contact capture."""
    intent, _ = detect_intent("What is RajibLabs?")
    assert intent == "about_rajiblabs"
    assert is_universal_business_intent(intent, "What is RajibLabs?")


def test_universal_intent_project_detail_triggers_capture():
    """Project detail inquiry should trigger contact capture."""
    intent, _ = detect_intent("Tell me about PestFlow")
    assert intent == "project_detail"
    assert is_universal_business_intent(intent, "Tell me about PestFlow")


def test_universal_intent_greeting_no_capture():
    """Greeting should NOT trigger contact capture."""
    intent, _ = detect_intent("Hello!")
    assert intent == "greeting"
    assert not is_universal_business_intent(intent, "Hello!")


def test_universal_intent_general_conversation_no_capture():
    """General conversation should NOT trigger contact capture."""
    intent, _ = detect_intent("Thanks!")
    assert intent == "general_conversation"
    assert not is_universal_business_intent(intent, "Thanks!")


def test_universal_stage_computation_services_intent():
    """Services inquiry should advance to BUSINESS_APPLICATION stage."""
    stage = _compute_conversation_stage(
        "What services do you offer?", {}, {}, STAGE_DISCOVER_INTENT)
    assert stage == STAGE_BUSINESS_APPLICATION


def test_universal_stage_computation_with_existing_lead():
    """If lead already has fields, skip those stages."""
    lead = {"name": "John", "email": "john@example.com"}
    stage = _compute_conversation_stage(
        "What services do you offer?", lead, {}, STAGE_DISCOVER_INTENT)
    # Should jump to CAPTURE_PHONE since name and email already exist
    assert stage == STAGE_CAPTURE_PHONE


def test_universal_capture_prompt_services():
    """Services inquiry should get contextually appropriate prompt."""
    reply, next_stage = _get_capture_prompt(
        STAGE_BUSINESS_APPLICATION, {}, {}, "What services do you offer?",
        intent="services")
    assert "help" in reply.lower() or "name" in reply.lower()
    assert next_stage == STAGE_CAPTURE_NAME


def test_universal_capture_prompt_contact():
    """Contact request should get contextually appropriate prompt."""
    reply, next_stage = _get_capture_prompt(
        STAGE_BUSINESS_APPLICATION, {}, {}, "How can I contact Rajib?",
        intent="contact")
    assert "connect" in reply.lower() or "name" in reply.lower()
    assert next_stage == STAGE_CAPTURE_NAME


@pytest.mark.asyncio
async def test_universal_services_flow_live(monkeypatch):
    """Services inquiry triggers deterministic fast path (no LLM)."""
    from app.services import concierge as cg
    from app.services.lead_ai import AIService
    db = await _live_db()

    async def _boom(*a, **k):
        raise AssertionError("LLM must not be called on capture fast path")

    monkeypatch.setattr(AIService, "_complete", _boom)
    token = None
    try:
        r1 = await cg.run_concierge_turn(
            db, "What services do you offer?", None, "127.0.0.1")
        assert r1["intent"] == "services"
        token = r1["session_token"]
        # Should get a deterministic reply asking for name
        assert r1["reply"]
        assert "name" in r1["reply"].lower()
        assert r1["used_llm"] is False

        # Provide name
        r2 = await cg.run_concierge_turn(db, "My name is Dave Wilson", token, "127.0.0.1")
        assert r2["reply"]
        assert "email" in r2["reply"].lower()
        assert r2["used_llm"] is False

        # Provide email
        r3 = await cg.run_concierge_turn(db, "dave@example.com", token, "127.0.0.1")
        assert r3["reply"]
        assert "phone" in r3["reply"].lower() or "reach" in r3["reply"].lower()
        assert r3["used_llm"] is False

        # Skip phone
        r4 = await cg.run_concierge_turn(db, "skip", token, "127.0.0.1")
        assert r4["reply"]
        assert r4["used_llm"] is False
    finally:
        if token:
            lead = await db["customer_leads"].find_one({"email": "dave@example.com"})
            await db["customer_messages"].delete_many({"session_token": token})
            await db["customer_conversations"].delete_many({"session_token": token})
            await db["ideas"].delete_many({"session_id": token})
            if lead:
                await db["customer_leads"].delete_one({"_id": lead["_id"]})


@pytest.mark.asyncio
async def test_universal_products_flow_live(monkeypatch):
    """Product inquiry triggers deterministic fast path (no LLM)."""
    from app.services import concierge as cg
    from app.services.lead_ai import AIService
    db = await _live_db()

    async def _boom(*a, **k):
        raise AssertionError("LLM must not be called on capture fast path")

    monkeypatch.setattr(AIService, "_complete", _boom)
    token = None
    try:
        r1 = await cg.run_concierge_turn(
            db, "Tell me about DocuFlow", None, "127.0.0.1")
        assert r1["intent"] == "products"
        token = r1["session_token"]
        assert r1["reply"]
        assert "name" in r1["reply"].lower()
        assert r1["used_llm"] is False
    finally:
        if token:
            await db["customer_messages"].delete_many({"session_token": token})
            await db["customer_conversations"].delete_many({"session_token": token})


@pytest.mark.asyncio
async def test_universal_contact_request_flow_live(monkeypatch):
    """Contact request triggers deterministic fast path (no LLM)."""
    from app.services import concierge as cg
    from app.services.lead_ai import AIService
    db = await _live_db()

    async def _boom(*a, **k):
        raise AssertionError("LLM must not be called on capture fast path")

    monkeypatch.setattr(AIService, "_complete", _boom)
    token = None
    try:
        r1 = await cg.run_concierge_turn(
            db, "How can I contact Rajib?", None, "127.0.0.1")
        assert r1["intent"] == "contact"
        token = r1["session_token"]
        assert r1["reply"]
        assert "name" in r1["reply"].lower()
        assert r1["used_llm"] is False
    finally:
        if token:
            await db["customer_messages"].delete_many({"session_token": token})
            await db["customer_conversations"].delete_many({"session_token": token})


@pytest.mark.asyncio
async def test_universal_technical_flow_live(monkeypatch):
    """Technical question triggers deterministic fast path (no LLM)."""
    from app.services import concierge as cg
    from app.services.lead_ai import AIService
    db = await _live_db()

    async def _boom(*a, **k):
        raise AssertionError("LLM must not be called on capture fast path")

    monkeypatch.setattr(AIService, "_complete", _boom)
    token = None
    try:
        r1 = await cg.run_concierge_turn(
            db, "How would you architect a microservices system?", None, "127.0.0.1")
        token = r1["session_token"]
        # Technical questions should trigger capture
        assert r1["reply"]
        assert "name" in r1["reply"].lower()
        assert r1["used_llm"] is False
    finally:
        if token:
            await db["customer_messages"].delete_many({"session_token": token})
            await db["customer_conversations"].delete_many({"session_token": token})


@pytest.mark.asyncio
async def test_universal_batch_input_all_fields_live(monkeypatch):
    """Batch all contact fields in one message during universal capture."""
    from app.services import concierge as cg
    from app.services.lead_ai import AIService
    db = await _live_db()

    async def _boom(*a, **k):
        raise AssertionError("LLM must not be called on capture fast path")

    monkeypatch.setattr(AIService, "_complete", _boom)
    token = None
    try:
        r1 = await cg.run_concierge_turn(
            db, "What services do you offer?", None, "127.0.0.1")
        token = r1["session_token"]

        # Provide all fields at once
        r2 = await cg.run_concierge_turn(
            db, "My name is Eve, email eve@test.com, phone +1 555 111 2222",
            token, "127.0.0.1")
        assert r2["reply"]
        assert r2["used_llm"] is False
    finally:
        if token:
            lead = await db["customer_leads"].find_one({"email": "eve@test.com"})
            await db["customer_messages"].delete_many({"session_token": token})
            await db["customer_conversations"].delete_many({"session_token": token})
            await db["ideas"].delete_many({"session_id": token})
            if lead:
                await db["customer_leads"].delete_one({"_id": lead["_id"]})


@pytest.mark.asyncio
async def test_universal_contact_request_name_capture_live(monkeypatch):
    """Contact request triggers name capture as first step."""
    from app.services import concierge as cg
    from app.services.lead_ai import AIService
    db = await _live_db()

    async def _boom(*a, **k):
        raise AssertionError("LLM must not be called on capture fast path")

    monkeypatch.setattr(AIService, "_complete", _boom)
    token = None
    try:
        r1 = await cg.run_concierge_turn(
            db, "How can I contact Rajib?", None, "127.0.0.1")
        assert r1["intent"] == "contact"
        token = r1["session_token"]
        # Should ask for name
        assert "name" in r1["reply"].lower()
        assert r1["used_llm"] is False

        # Provide name
        r2 = await cg.run_concierge_turn(db, "My name is Frank Lee", token, "127.0.0.1")
        assert "email" in r2["reply"].lower()
        assert r2["used_llm"] is False
    finally:
        if token:
            await db["customer_messages"].delete_many({"session_token": token})
            await db["customer_conversations"].delete_many({"session_token": token})


@pytest.mark.asyncio
async def test_universal_phone_decline_live(monkeypatch):
    """User can decline phone by saying 'skip' during universal capture."""
    from app.services import concierge as cg
    from app.services.lead_ai import AIService
    db = await _live_db()

    async def _boom(*a, **k):
        raise AssertionError("LLM must not be called on capture fast path")

    monkeypatch.setattr(AIService, "_complete", _boom)
    token = None
    try:
        r1 = await cg.run_concierge_turn(
            db, "What services do you offer?", None, "127.0.0.1")
        token = r1["session_token"]

        r2 = await cg.run_concierge_turn(db, "Grace Park", token, "127.0.0.1")
        r3 = await cg.run_concierge_turn(db, "grace@test.com", token, "127.0.0.1")
        r4 = await cg.run_concierge_turn(db, "no", token, "127.0.0.1")
        assert r4["reply"]
        assert r4["used_llm"] is False
    finally:
        if token:
            lead = await db["customer_leads"].find_one({"email": "grace@test.com"})
            await db["customer_messages"].delete_many({"session_token": token})
            await db["customer_conversations"].delete_many({"session_token": token})
            await db["ideas"].delete_many({"session_id": token})
            if lead:
                await db["customer_leads"].delete_one({"_id": lead["_id"]})


@pytest.mark.asyncio
async def test_universal_existing_lead_skip_stages_live(monkeypatch):
    """Existing lead fields cause stage skipping during universal capture."""
    from app.services import concierge as cg
    from app.services.lead_ai import AIService
    db = await _live_db()

    async def _boom(*a, **k):
        raise AssertionError("LLM must not be called on capture fast path")

    monkeypatch.setattr(AIService, "_complete", _boom)
    token = None
    try:
        # First create a lead with name and email
        r1 = await cg.run_concierge_turn(
            db, "I want to build an app", None, "127.0.0.1")
        token = r1["session_token"]
        r2 = await cg.run_concierge_turn(db, "My name is Test User", token, "127.0.0.1")
        r3 = await cg.run_concierge_turn(db, "test@example.com", token, "127.0.0.1")
        r4 = await cg.run_concierge_turn(db, "skip", token, "127.0.0.1")

        # Now start a new session with the same email
        r5 = await cg.run_concierge_turn(
            db, "What services do you offer?", None, "127.0.0.1")
        token2 = r5["session_token"]
        # Should ask for name
        assert "name" in r5["reply"].lower()

        # Provide name
        r6 = await cg.run_concierge_turn(db, "My name is Test User", token2, "127.0.0.1")
        # Should ask for email
        assert "email" in r6["reply"].lower()

        # Provide email (same as existing lead)
        r7 = await cg.run_concierge_turn(db, "test@example.com", token2, "127.0.0.1")
        # Should skip to phone (existing email matched)
        assert "phone" in r7["reply"].lower() or "reach" in r7["reply"].lower()
        assert r7["used_llm"] is False
    finally:
        if token:
            await db["customer_messages"].delete_many({"session_token": token})
            await db["customer_conversations"].delete_many({"session_token": token})
            await db["ideas"].delete_many({"session_id": token})
        if token2:
            await db["customer_messages"].delete_many({"session_token": token2})
            await db["customer_conversations"].delete_many({"session_token": token2})
            await db["ideas"].delete_many({"session_id": token2})
        lead = await db["customer_leads"].find_one({"email": "test@example.com"})
        if lead:
            await db["customer_leads"].delete_one({"_id": lead["_id"]})


@pytest.mark.asyncio
async def test_universal_project_detail_flow_live(monkeypatch):
    """Project detail inquiry triggers deterministic fast path (no LLM)."""
    from app.services import concierge as cg
    from app.services.lead_ai import AIService
    db = await _live_db()

    async def _boom(*a, **k):
        raise AssertionError("LLM must not be called on capture fast path")

    monkeypatch.setattr(AIService, "_complete", _boom)
    token = None
    try:
        r1 = await cg.run_concierge_turn(
            db, "Tell me about PestFlow", None, "127.0.0.1")
        token = r1["session_token"]
        assert r1["reply"]
        assert "name" in r1["reply"].lower()
        assert r1["used_llm"] is False
    finally:
        if token:
            await db["customer_messages"].delete_many({"session_token": token})
            await db["customer_conversations"].delete_many({"session_token": token})
