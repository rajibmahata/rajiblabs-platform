"""AI Lead Conversation end-to-end tests (22 cases, §25).

Uses the live local MongoDB with uniquely-tagged data + teardown cleanup
(same pattern as test_api.py graceful skips). AI is faked at the service
boundary — no network, no secrets, deterministic.
"""
import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.database import get_db
from app.services.lead_ai import AIError, LeadAssistantOut

TAG = "t_" + uuid.uuid4().hex[:8]
_created = {"leads": [], "sessions": [], "ideas": []}


class FakeAI:
    """Scripted stand-in for AIService. Pops canned turns, else echoes."""

    def __init__(self, turns=None, analyze=None):
        self.turns = list(turns or [])
        self.analyze_result = analyze
        self.calls = 0

    async def chat_with_lead(self, history, message, knowledge, known, language="en"):
        self.calls += 1
        if self.turns:
            t = self.turns.pop(0)
            return LeadAssistantOut(**t), {"ai_provider": "fake", "ai_model": "fake",
                                           "usage": {}}
        return LeadAssistantOut(reply=f"Noted: {message[:60]}"), \
            {"ai_provider": "fake", "ai_model": "fake", "usage": {}}

    async def analyze_idea(self, lead, idea):
        from app.schemas import ScopeSection
        if isinstance(self.analyze_result, Exception):
            raise self.analyze_result
        data = self.analyze_result or {
            "problem_understanding": "Manual bookings via Excel/WhatsApp.",
            "proposed_solution": "Centralized booking platform.",
            "core_features": ["Online booking", "Notifications"],
            "user_roles": ["Customer", "Admin"],
            "main_workflow": ["Book", "Confirm"],
            "mvp_scope": ["Booking"], "future_features": [],
            "technology_direction": "FastAPI + React",
            "risks_assumptions": [], "discovery_questions": ["Timeline?"]}
        return ScopeSection(**data), {"ai_provider": "fake", "ai_model": "fake",
                                      "usage": {}}


@pytest.fixture
def fake_ai(monkeypatch):
    fake = FakeAI()
    monkeypatch.setattr("app.services.lead_pipeline.AIService", lambda: fake)
    return fake


@pytest.fixture(autouse=True)
async def _mongo_guard():
    try:
        await get_db().command("ping")
    except Exception:
        pytest.skip("MongoDB not running locally")


@pytest.fixture(autouse=True)
async def _isolation():
    """Reset in-memory rate-limit buckets so tests never throttle each other."""
    from app.routers import chat as chat_router
    chat_router.CHAT_HITS.clear()
    yield


@pytest.fixture(autouse=True)
async def _cleanup():
    yield
    db = get_db()
    from bson import ObjectId
    oids = []
    for x in _created["leads"]:
        try:
            oids.append(ObjectId(x))
        except Exception:
            pass
    if oids:
        await db["customer_leads"].delete_many({"_id": {"$in": oids}})
    if _created["sessions"]:
        await db["customer_conversations"].delete_many(
            {"session_token": {"$in": _created["sessions"]}})
        await db["customer_messages"].delete_many(
            {"session_token": {"$in": _created["sessions"]}})
        await db["ideas"].delete_many({"session_id": {"$in": _created["sessions"]}})
    _created["leads"].clear()
    _created["sessions"].clear()
    _created["ideas"].clear()


def _client():
    from app.main import create_app
    return AsyncClient(transport=ASGITransport(app=create_app()),
                       base_url="http://test")


async def _turn(client, token, message, **kw):
    r = await client.post("/api/public/chat",
                          json={"session_id": token, "message": message, **kw})
    assert r.status_code == 200, r.text
    return r.json()


def _track(body):
    if body.get("session_id"):
        _created["sessions"].append(body["session_id"])


JOHN = ("My name is John, I own ABC Logistics, my email is "
        "john@abc.com and my number is 9876543210. "
        "We need software to manage driver assignments.")


def _john_turn(name="John", email=None, phone=None):
    email = email or f"{TAG}_john@abc.com"
    phone = phone or "9876543210"
    return {"reply": "Nice to meet you.",
            "lead": {"name": name, "email": email, "phone": phone,
                     "company_name": "ABC Logistics", "industry": "Logistics"},
            "idea": {"description": "driver assignment management software",
                     "problem_statement": "Driver assignments are managed manually.",
                     "current_process": "Phone calls and spreadsheets",
                     "desired_outcome": "Online assignment board"},
            "missing_fields": [], "is_lead_captured": True,
            "next_action": "lead_captured"}


@pytest.mark.asyncio
async def test_01_create_session(fake_ai):
    async with _client() as c:
        r = await c.post("/api/public/chat/session")
        assert r.status_code == 200
        sid = r.json()["session_id"]
        assert len(sid) >= 16
        _created["sessions"].append(sid)
        db = get_db()
        assert await db["audit_logs"].find_one(
            {"event_type": "SESSION_CREATED", "entity": sid})


@pytest.mark.asyncio
async def test_02_first_message(fake_ai):
    async with _client() as c:
        body = await _turn(c, "", "I want to build a booking platform.")
        _track(body)
        assert body["reply"] and body["session_id"]
        assert body["lead_captured"] is False
        # the substantive message seeds the idea, so only contact fields miss
        assert set(body["missing_fields"]) == {"name", "email", "phone"}


@pytest.mark.asyncio
async def test_03_user_message_saved(fake_ai):
    async with _client() as c:
        body = await _turn(c, "", "Hello booking world")
        _track(body)
        db = get_db()
        m = await db["customer_messages"].find_one(
            {"session_token": body["session_id"], "sender": "user"})
        assert m and "Hello booking world" in m["message"]


@pytest.mark.asyncio
async def test_04_ai_response_saved(fake_ai):
    async with _client() as c:
        body = await _turn(c, "", "Hi there")
        _track(body)
        db = get_db()
        m = await db["customer_messages"].find_one(
            {"session_token": body["session_id"], "sender": "assistant"})
        assert m and m["ai_provider"] == "fake" and m["ai_model"] == "fake"


@pytest.mark.asyncio
async def test_05_name_extraction(fake_ai):
    fake_ai.turns.append({"reply": "Nice to meet you, Testy.",
                          "lead": {"name": "Testy McTest"},
                          "missing_fields": ["email", "phone", "idea"]})
    async with _client() as c:
        body = await _turn(c, "", "My name is Testy McTest")
        _track(body)
        db = get_db()
        sess = await db["customer_conversations"].find_one(
            {"session_token": body["session_id"]})
        from bson import ObjectId
        lead = await db["customer_leads"].find_one({"_id": ObjectId(sess["lead_id"])})
        _created["leads"].append(str(lead["_id"]))
        assert lead["name"] == "Testy McTest"


@pytest.mark.asyncio
async def test_06_email_extraction(fake_ai):
    email = f"{TAG}_mail@abc.com"
    fake_ai.turns.append({"reply": "Thanks.",
                          "lead": {"email": email},
                          "missing_fields": ["name", "phone", "idea"]})
    async with _client() as c:
        body = await _turn(c, "", f"reach me at {email}")
        _track(body)
        db = get_db()
        assert await db["customer_leads"].find_one({"email": email}) is not None
        lead = await db["customer_leads"].find_one({"email": email})
        _created["leads"].append(str(lead["_id"]))


@pytest.mark.asyncio
async def test_07_phone_extraction(fake_ai):
    fake_ai.turns.append({"reply": "Got it.",
                          "lead": {"phone": "+91 84202 49021"},
                          "missing_fields": ["name", "email", "idea"]})
    async with _client() as c:
        body = await _turn(c, "", "call me on +91 84202 49021")
        _track(body)
        db = get_db()
        lead = await db["customer_leads"].find_one({"phone": "+918420249021"})
        assert lead is not None
        _created["leads"].append(str(lead["_id"]))


@pytest.mark.asyncio
async def test_08_multi_field_message(fake_ai):
    email = f"{TAG}_john@abc.com"
    fake_ai.turns.append(_john_turn(email=email))
    async with _client() as c:
        body = await _turn(c, "", JOHN.replace("john@abc.com", email))
        _track(body)
        assert body["lead_captured"] is True
        assert body["missing_fields"] == []
        assert body["show_blueprint"] is True
        db = get_db()
        lead = await db["customer_leads"].find_one({"email": email})
        assert lead["name"] == "John" and lead["company_name"] == "ABC Logistics"
        assert lead["phone"] == "9876543210" and lead["industry"] == "Logistics"
        assert lead["marketing_consent"] is False  # never auto-subscribed
        _created["leads"].append(str(lead["_id"]))


@pytest.mark.asyncio
async def test_09_duplicate_email_reuses_lead(fake_ai):
    email = f"{TAG}_dup@abc.com"
    fake_ai.turns.append(_john_turn(email=email))
    fake_ai.turns.append({"reply": "Welcome back.",
                          "lead": {"email": email, "phone": "9111111111"},
                          "missing_fields": ["name", "idea"]})
    db = get_db()
    async with _client() as c:
        b1 = await _turn(c, "", JOHN.replace("john@abc.com", email))
        b2 = await _turn(c, "", "hi again, new number 9111111111")
        assert b1["session_id"] != b2["session_id"]
        assert await db["customer_leads"].count_documents({"email": email}) == 1
        lead = await db["customer_leads"].find_one({"email": email})
        _created["leads"].append(str(lead["_id"]))
        _track(b1)
        _track(b2)
        # manual name preserved, missing phone filled, both sessions attached
        assert lead["name"] == "John" and lead["phone"] == "9111111111"
        assert set(lead["session_ids"]) == {b1["session_id"], b2["session_id"]}


@pytest.mark.asyncio
async def test_10_existing_lead_updated(fake_ai):
    from bson import ObjectId
    from app.database import utcnow
    db = get_db()
    email = f"{TAG}_exist@abc.com"
    res = await db["customer_leads"].insert_one({
        "name": "", "email": email, "phone": "", "company_name": "", "industry": "",
        "status": "new", "lead_score": 0, "source": "website_chat",
        "marketing_consent": False, "session_ids": [],
        "created_at": utcnow(), "updated_at": utcnow()})
    _created["leads"].append(str(res.inserted_id))
    fake_ai.turns.append({"reply": "Hi Sam.", "lead": {"name": "Sam", "email": email},
                          "missing_fields": ["phone", "idea"]})
    async with _client() as c:
        body = await _turn(c, "", f"I'm Sam, {email} here")
        _track(body)
        lead = await db["customer_leads"].find_one({"_id": ObjectId(res.inserted_id)})
        assert lead["name"] == "Sam" and lead["email"] == email


@pytest.mark.asyncio
async def test_11_new_lead_created(fake_ai):
    async with _client() as c:
        body = await _turn(c, "", "Just browsing the site")
        _track(body)
        db = get_db()
        sess = await db["customer_conversations"].find_one(
            {"session_token": body["session_id"]})
        from bson import ObjectId
        lead = await db["customer_leads"].find_one({"_id": ObjectId(sess["lead_id"])})
        _created["leads"].append(str(lead["_id"]))
        assert lead["status"] == "new" and lead["source"] == "website_chat"
        assert await db["audit_logs"].find_one(
            {"event_type": "LEAD_CREATED", "entity": str(lead["_id"])})
        assert body["lead_captured"] is False


@pytest.mark.asyncio
async def test_12_idea_created(fake_ai):
    fake_ai.turns.append({"reply": "Tell me more.",
                          "idea": {"description": "A booking platform for salons"},
                          "missing_fields": ["name", "email", "phone"]})
    async with _client() as c:
        body = await _turn(c, "", "I want a booking platform for salons")
        _track(body)
        db = get_db()
        idea = await db["ideas"].find_one({"session_id": body["session_id"]})
        assert idea and "booking" in idea["description"]
        assert idea["status"] == "new"
        assert await db["audit_logs"].find_one(
            {"event_type": "IDEA_CREATED", "entity": str(idea["_id"])})
        _created["ideas"].append(str(idea["_id"]))


@pytest.mark.asyncio
async def test_13_idea_updated_not_duplicated(fake_ai):
    fake_ai.turns.append({"reply": "Tell me more.",
                          "idea": {"description": "A booking platform for salons"},
                          "missing_fields": ["name", "email", "phone"]})
    fake_ai.turns.append({"reply": "Noted.",
                          "idea": {"problem_statement": "They lose walk-ins without reminders"},
                          "missing_fields": ["name", "email", "phone"]})
    async with _client() as c:
        b1 = await _turn(c, "", "I want a booking platform for salons")
        b2 = await _turn(c, b1["session_id"], "They lose walk-ins without reminders")
        _track(b2)
        db = get_db()
        ideas = [d async for d in db["ideas"].find({"session_id": b2["session_id"]})]
        for i in ideas:
            _created["ideas"].append(str(i["_id"]))
        active = [i for i in ideas if i.get("status") != "archived"]
        assert len(active) == 1
        assert "booking" in active[0]["description"]
        assert "walk-ins" in active[0]["problem_statement"]


@pytest.mark.asyncio
async def test_14_multiple_ideas_on_new_topic(fake_ai):
    fake_ai.turns.append({"reply": "Tell me more.",
                          "idea": {"description": "A booking platform for salons"},
                          "missing_fields": ["name", "email", "phone"]})
    fake_ai.turns.append({"reply": "New project noted.",
                          "idea": {"description": "A payroll product for factories"},
                          "missing_fields": ["name", "email", "phone"]})
    async with _client() as c:
        b1 = await _turn(c, "", "I want a booking platform for salons")
        b2 = await _turn(c, b1["session_id"],
                         "Actually I have another idea, a payroll product for factories")
        _track(b2)
        db = get_db()
        ideas = [d async for d in db["ideas"].find({"session_id": b2["session_id"]})]
        for i in ideas:
            _created["ideas"].append(str(i["_id"]))
        by_status = {i["status"]: i for i in ideas}
        assert "archived" in by_status and "payroll" in [
            i["description"] for i in ideas if i["status"] != "archived"][0]


@pytest.mark.asyncio
async def test_15_preliminary_scope(fake_ai):
    email = f"{TAG}_scope@abc.com"
    fake_ai.turns.append(_john_turn(email=email))
    async with _client() as c:
        body = await _turn(c, "", JOHN.replace("john@abc.com", email))
        _track(body)
        db = get_db()
        lead = await db["customer_leads"].find_one({"email": email})
        _created["leads"].append(str(lead["_id"]))
        r = await c.post(f"/api/public/chat/{body['session_id']}/analyze")
        assert r.status_code == 200, r.text
        payload = r.json()
        assert "AI-generated preliminary scope" in payload["scope_markdown"]
        assert payload["scope"]["core_features"] == ["Online booking", "Notifications"]
        assert payload["cached"] is True  # auto-analyze already ran during the turn
        # change the idea → source hash changes → fresh regeneration
        await db["ideas"].update_one(
            {"session_id": body["session_id"]},
            {"$set": {"description": "driver assignment management plus payroll"}})
        r2 = await c.post(f"/api/public/chat/{body['session_id']}/analyze")
        assert r2.status_code == 200, r2.text
        assert r2.json()["cached"] is False
        r3 = await c.post(f"/api/public/chat/{body['session_id']}/analyze")
        assert r3.json()["cached"] is True
        idea = await db["ideas"].find_one({"session_id": body["session_id"]})
        _created["ideas"].append(str(idea["_id"]))
        assert idea["preliminary_scope"]["core_features"] == ["Online booking", "Notifications"]
        assert await db["audit_logs"].find_one(
            {"event_type": "SCOPE_GENERATED", "entity": str(idea["_id"])})


@pytest.mark.asyncio
async def test_16_ai_failure_graceful(monkeypatch):
    from app.services import lead_pipeline
    import app.services.lead_ai as lai
    orig = lead_pipeline.AIService

    class Boom:
        async def chat_with_lead(self, *a, **k):
            raise lai.AIError("down")

        async def analyze_idea(self, *a, **k):
            raise lai.AIError("down")

    lead_pipeline.AIService = Boom
    # provider configured but failing → spec §12 graceful message (not heuristic)
    monkeypatch.setattr(lead_pipeline, "_ai_configured", lambda: True)
    try:
        async with _client() as c:
            body = await _turn(c, "", "I need a booking system please")
            _track(body)
            assert "trouble processing" in body["message"] or "contact Rajib" in body["message"]
            db = get_db()
            m = await db["customer_messages"].find_one(
                {"session_token": body["session_id"], "sender": "user"})
            assert m is not None  # user message preserved
            assert await db["audit_logs"].find_one(
                {"event_type": "AI_FAILURE", "entity": body["session_id"]})
            sess = await db["customer_conversations"].find_one(
                {"session_token": body["session_id"]})
            from bson import ObjectId
            _created["leads"].append(str(sess["lead_id"]))
    finally:
        lead_pipeline.AIService = orig


@pytest.mark.asyncio
async def test_17_invalid_ai_json(monkeypatch):
    import httpx
    from app.services import lead_ai

    class BadResp:
        def raise_for_status(self):
            return None

        def json(self):
            return {"choices": [{"message": {"content": "not json {{{" }}]}

    class BadClient:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, *a, **k):
            return BadResp()

    monkeypatch.setattr(httpx, "AsyncClient", BadClient)
    svc = lead_ai.AIService()
    import pytest as pt
    with pt.raises(lead_ai.AIError):
        await svc.chat_with_lead([], "hi", "knowledge", {})


@pytest.mark.asyncio
async def test_18_rate_limiting():
    async with _client() as c:
        codes = []
        for _ in range(31):
            r = await c.post("/api/public/chat/session", json={})
            codes.append(r.status_code)
        assert 429 in codes


@pytest.mark.asyncio
async def test_19_session_isolation(fake_ai):
    async with _client() as c:
        a = await _turn(c, "", "Session A booking talk")
        b = await _turn(c, "", "Session B payroll talk")
        _track(a)
        _track(b)
        assert a["session_id"] != b["session_id"]
        h = await c.get(f"/api/public/chat/session/{a['session_id']}")
        assert h.status_code == 200
        texts = [m["text"] for m in h.json()["messages"]]
        assert any("Session A" in t for t in texts)
        assert not any("Session B" in t for t in texts)
        r = await c.get("/api/public/chat/session/does-not-exist-zzz")
        assert r.status_code == 404


@pytest.mark.asyncio
async def test_20_marketing_consent(fake_ai):
    # explicit opt-in → True
    fake_ai.turns.append({"reply": "Subscribed!", "lead": {},
                          "missing_fields": ["name", "email", "phone", "idea"]})
    # no signal → stays False
    fake_ai.turns.append({"reply": "OK", "lead": {},
                          "missing_fields": ["name", "email", "phone", "idea"]})
    async with _client() as c:
        b1 = await _turn(c, "", "yes, please subscribe me to updates")
        b2 = await _turn(c, "", "just tell me about pricing")
        _track(b1)
        _track(b2)
        db = get_db()
        from bson import ObjectId
        for b in (b1, b2):
            sess = await db["customer_conversations"].find_one(
                {"session_token": b["session_id"]})
            _created["leads"].append(str(sess["lead_id"]))
        s1 = await db["customer_conversations"].find_one({"session_token": b1["session_id"]})
        s2 = await db["customer_conversations"].find_one({"session_token": b2["session_id"]})
        l1 = await db["customer_leads"].find_one({"_id": ObjectId(s1["lead_id"])})
        l2 = await db["customer_leads"].find_one({"_id": ObjectId(s2["lead_id"])})
        assert l1["marketing_consent"] is True
        assert l2["marketing_consent"] is False


@pytest.mark.asyncio
async def test_21_admin_authorization():
    async with _client() as c:
        for path in ("/api/admin/leads", "/api/admin/leads/507f1f77bcf86cd799439011",
                     "/api/admin/leads/507f1f77bcf86cd799439011/sessions",
                     "/api/admin/leads/507f1f77bcf86cd799439011/ideas",
                     "/api/admin/chat/sessions/abc/messages"):
            r = await c.get(path)
            assert r.status_code == 401, path
        r = await c.patch("/api/admin/leads/507f1f77bcf86cd799439011",
                          json={"status": "bogus"})
        assert r.status_code in (401, 422)


@pytest.mark.asyncio
async def test_22_audit_logging(fake_ai):
    email = f"{TAG}_audit@abc.com"
    fake_ai.turns.append(_john_turn(email=email))
    async with _client() as c:
        body = await _turn(c, "", JOHN.replace("john@abc.com", email))
        _track(body)
        db = get_db()
        lead = await db["customer_leads"].find_one({"email": email})
        _created["leads"].append(str(lead["_id"]))
        events = {d["event_type"] async for d in db["audit_logs"].find(
            {"entity": {"$in": [body["session_id"], str(lead["_id"])]}})}
        for expected in ("SESSION_CREATED", "MESSAGE_RECEIVED", "AI_REQUEST",
                         "AI_RESPONSE", "LEAD_CREATED"):
            assert expected in events, expected
        # no secrets persisted in audit metadata
        async for d in db["audit_logs"].find(
                {"entity": {"$in": [body["session_id"], str(lead["_id"])]}}):
            blob = str(d.get("metadata", {})).lower()
            assert "sk-" not in blob and "ghp_" not in blob


@pytest.mark.asyncio
async def test_23_prose_wrapped_json_repaired(monkeypatch):
    """Model wraps JSON in prose → repair path parses, no AIError."""
    import httpx
    import json as _json
    from app.services import lead_ai
    payload = _john_turn()
    calls = {"n": 0}

    class ProseResp:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return {"choices": [{"message": {
                "content": "Here is the result:\n```json\n" + _json.dumps(payload) + "\n```\nHope this helps."}}]}

    class ProseClient:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, *a, **k):
            calls["n"] += 1
            return ProseResp()

    monkeypatch.setattr(httpx, "AsyncClient", ProseClient)
    svc = lead_ai.AIService()
    result, meta = await svc.chat_with_lead([], "hi", "knowledge", {})
    assert result.reply == "Nice to meet you."
    assert calls["n"] == 1  # repaired inline, no retry storm


@pytest.mark.asyncio
async def test_24_empty_content_retries_then_ai_error(monkeypatch):
    """200 + empty content (the JSONDecodeError("") case) → EmptyContent, AIError."""
    import httpx
    from app.services import lead_ai
    calls = {"n": 0}

    class EmptyResp:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return {"choices": [{"message": {"content": None}, "finish_reason": "stop"}]}

    class EmptyClient:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, *a, **k):
            calls["n"] += 1
            return EmptyResp()

    async def _no_sleep(*a, **k):
        return None

    monkeypatch.setattr(httpx, "AsyncClient", EmptyClient)
    monkeypatch.setattr("app.services.lead_ai.asyncio.sleep", _no_sleep)
    svc = lead_ai.AIService()
    import pytest as pt
    with pt.raises(lead_ai.AIError):
        await svc.chat_with_lead([], "hi", "knowledge", {})
    assert calls["n"] == 3  # transient-style: all attempts used


@pytest.mark.asyncio
async def test_25_refusal_breaks_early(monkeypatch):
    """Refusal is deterministic for the input → exactly 1 attempt, AIError."""
    import httpx
    from app.services import lead_ai
    calls = {"n": 0}

    class RefuseResp:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return {"choices": [{"message": {"content": None, "refusal": "blocked"}}]}

    class RefuseClient:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, *a, **k):
            calls["n"] += 1
            return RefuseResp()

    monkeypatch.setattr(httpx, "AsyncClient", RefuseClient)
    svc = lead_ai.AIService()
    import pytest as pt
    with pt.raises(lead_ai.AIError):
        await svc.chat_with_lead([], "hi", "knowledge", {})
    assert calls["n"] == 1


@pytest.mark.asyncio
async def test_26_http_401_breaks_early(monkeypatch):
    """Wrong key (401) → 1 attempt, not 3; details name the status."""
    import httpx
    from app.services import lead_ai
    calls = {"n": 0}

    class DeniedResp:
        status_code = 401
        text = '{"error": {"message": "Incorrect API key"}}'

    class DeniedClient:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, *a, **k):
            calls["n"] += 1
            return DeniedResp()

    monkeypatch.setattr(httpx, "AsyncClient", DeniedClient)
    svc = lead_ai.AIService()
    import pytest as pt
    with pt.raises(lead_ai.AIError):
        await svc.chat_with_lead([], "hi", "knowledge", {})
    assert calls["n"] == 1


def test_27_extract_json_object_cases():
    from app.services.lead_ai import _BadJson, _extract_json_object
    import pytest as pt
    assert _extract_json_object('{"a": 1}') == {"a": 1}
    # braces inside strings don't confuse the scanner
    assert _extract_json_object('x {"a": "}{"} y') == {"a": "}{"}
    with pt.raises(_BadJson):
        _extract_json_object("no braces at all")
    with pt.raises(_BadJson):
        _extract_json_object("[1, 2, 3]")


@pytest.mark.asyncio
async def test_28_http_404_retries_once_with_fallback_model(monkeypatch):
    """Unknown primary model (404) → one retry with openai_fallback_model, then success."""
    import httpx
    import json as _json
    from app.config import get_settings
    from app.services import lead_ai
    fallback = (get_settings().openai_fallback_model or "").strip()
    assert fallback, "fallback model must be configured"
    payload = _john_turn()
    seen_models: list[str] = []

    class FlakyResp:
        def __init__(self, status, body):
            self.status_code = status
            self.text = body
            self.headers = {}

        def json(self):
            return _json.loads(self.text)

    class FlakyClient:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, *a, **k):
            model = k["json"]["model"]
            seen_models.append(model)
            if model != fallback:
                return FlakyResp(404, "")
            return FlakyResp(200, _json.dumps(
                {"choices": [{"message": {"content": _json.dumps(payload)}}]}))

    monkeypatch.setattr(httpx, "AsyncClient", FlakyClient)
    svc = lead_ai.AIService()
    result, meta = await svc.chat_with_lead([], "hi", "knowledge", {})
    assert result.reply == "Nice to meet you."
    assert meta["ai_model"] == fallback
    assert seen_models[0] != fallback and seen_models[-1] == fallback
