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
        assert r["intent"] == "contact" and "@" in r["reply"]
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
        assert r1["intent"] == "hire_lead"
        token = r1["session_token"]
        assert "name" in (r1["missing_fields"] or [])
        r2 = await cg.run_concierge_turn(db, "My name is Baker Ted", token, "127.0.0.1")
        assert "email" in (r2["missing_fields"] or [])
        r3 = await cg.run_concierge_turn(db, "ted@bakery.example", token, "127.0.0.1")
        assert r3["lead_captured"] is True
        assert "Ted" in r3["reply"] or "ted@bakery.example" in r3["reply"] or "Thanks" in r3["reply"]
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
