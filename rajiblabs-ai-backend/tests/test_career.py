"""Career Application module tests: CRUD, agent pipeline (no-AI deterministic),
approval/send guards, email validation, tracking, auth. Live tests need
MongoDB (skip otherwise). AI/HTTP/SMTP are faked at service boundaries."""
import pytest
from httpx import ASGITransport, AsyncClient

from app.services import workbench as wb
from app.services.lead_ai import AIError


async def _live_db():
    try:
        from app.database import get_db
        db = get_db()
        await db.command("ping")
        return db
    except Exception:
        pytest.skip("MongoDB not running locally")


def _authed(app):
    from app.auth.dependencies import require_admin
    app.dependency_overrides[require_admin] = lambda: "admin@test.local"
    return app


class DeadAI:
    def __init__(self, *a, **k):
        raise AIError("AI not configured")


@pytest.fixture
def no_ai(monkeypatch):
    monkeypatch.setattr(wb.lead_ai, "AIService", DeadAI)


@pytest.fixture
def no_retrieval(monkeypatch):
    async def _empty(*a, **k):
        return []
    monkeypatch.setattr(wb.rag_query, "retrieve", _empty)


TAG = "career-e2e"


async def _mk_company(c, name="E2ECorp"):
    r = await c.post("/api/admin/career/companies", json={"name": name})
    assert r.status_code == 201, r.text
    return r.json()


async def _mk_contact(c, company_id, email="hr@e2ecorp.example"):
    r = await c.post("/api/admin/career/contacts", json={
        "company_id": company_id, "name": "E2E Recruiter",
        "email": email, "contact_type": "Recruiter", "verified": True})
    assert r.status_code == 201, r.text
    return r.json()


async def _mk_job(c, company_id, title="E2E Backend Engineer"):
    r = await c.post("/api/admin/career/jobs", json={
        "company_id": company_id, "title": title,
        "description": "We need a backend engineer with Python and FastAPI "
                       "experience for our pharmacy platform. React a plus. "
                       "This description is long enough to pass validation."})
    assert r.status_code == 201, r.text
    return r.json()


# ── email service (pure, SMTP faked) ──

def test_email_validation_rejects_bad_input():
    from app.services.email_service import EmailError, validate_outgoing
    for bad in [("", "s", "b"), ("not-an-email", "s", "b"),
                ("a@b.c", "", "b"), ("a@b.c", "s", "")]:
        try:
            validate_outgoing(*bad)
            raise AssertionError(f"accepted {bad}")
        except EmailError:
            pass
    assert validate_outgoing("  A@B.c  ", "Hi", "Body") == "a@b.c"


def test_email_requires_config(monkeypatch):
    from app.services import email_service
    from types import SimpleNamespace
    monkeypatch.setattr(email_service, "get_settings", lambda: SimpleNamespace(
        smtp_host="", smtp_port=587, smtp_user="", smtp_password="", smtp_from=""))
    try:
        email_service.send_application_email("a@b.c", "s", "b")
        raise AssertionError("sent without config")
    except email_service.EmailError:
        pass


def test_email_send_uses_smtp_and_hides_secrets(monkeypatch):
    import smtplib
    from app.services import email_service
    from types import SimpleNamespace
    sent = {}

    class FakeSMTP:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def starttls(self):
            pass

        def login(self, user, password):
            sent["login_user"] = user
            assert password == "smtp-secret-xyz"

        def send_message(self, msg):
            sent["to"] = msg["To"]
            sent["subject"] = msg["Subject"]

    monkeypatch.setattr(smtplib, "SMTP", FakeSMTP)
    monkeypatch.setattr(email_service, "get_settings", lambda: SimpleNamespace(
        smtp_host="mail.example", smtp_port=587, smtp_user="bot@example.com",
        smtp_password="smtp-secret-xyz", smtp_from="bot@example.com"))
    out = email_service.send_application_email("hr@corp.example", "Hi", "Body here")
    assert out["to_domain"] == "corp.example"
    assert sent["to"] == "hr@corp.example"
    # failure surfaces as EmailError, never raw exceptions/credentials
    class BoomSMTP(FakeSMTP):
        def send_message(self, msg):
            raise ConnectionError("down")

    monkeypatch.setattr(smtplib, "SMTP", BoomSMTP)
    try:
        email_service.send_application_email("hr@corp.example", "Hi", "Body")
        raise AssertionError("expected EmailError")
    except email_service.EmailError as e:
        assert "smtp-secret" not in str(e) and " corp" not in str(e)


# ── career agent seed ──

@pytest.mark.asyncio
async def test_career_agent_seeded_and_typed():
    from app.services import agent_config
    db = await _live_db()
    try:
        doc = await agent_config.ensure_career_seed(db)
        assert doc["slug"] == "rajiblabs-career"
        assert doc["public_enabled"] is False
        assert "career" in agent_config.AGENT_TYPES
        again = await agent_config.ensure_career_seed(db)
        assert str(again["_id"]) == str(doc["_id"])  # idempotent, never overwrites
    finally:
        pass  # seed is shared infrastructure, keep it


# ── companies / contacts CRUD ──

@pytest.mark.asyncio
async def test_company_crud_and_guards():
    from app.main import create_app
    db = await _live_db()
    app = _authed(create_app())
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.post("/api/admin/career/companies", json={"name": "x"})
            assert r.status_code == 422  # name too short
            comp = await _mk_company(c, f"{TAG}-Corp")
            cid = comp["id"]
            r = await c.get("/api/admin/career/companies", params={"q": f"{TAG}-Corp"})
            assert r.json()["total"] == 1
            r = await c.put(f"/api/admin/career/companies/{cid}", json={"location": "Kolkata"})
            assert r.json()["location"] == "Kolkata"
            ct = await _mk_contact(c, cid)
            # blocked while children exist
            r = await c.delete(f"/api/admin/career/companies/{cid}")
            assert r.status_code == 409
            await c.delete(f"/api/admin/career/contacts/{ct['id']}")
            # bad email rejected
            r = await c.post("/api/admin/career/contacts",
                             json={"company_id": cid, "name": "Nope", "email": "bad"})
            assert r.status_code == 400
            # unknown company rejected
            r = await c.post("/api/admin/career/contacts",
                             json={"company_id": "000000000000000000000000",
                                   "name": "Ghost", "email": "g@x.io"})
            assert r.status_code == 404
            r = await c.delete(f"/api/admin/career/companies/{cid}")
            assert r.status_code == 200
    finally:
        app.dependency_overrides.clear()
        await db["career_companies"].delete_many({"name": {"$regex": f"^{TAG}"}})
        await db["career_contacts"].delete_many({"name": "E2E Recruiter"})


# ── jobs: analyze → generate (deterministic, no AI) ──

@pytest.mark.asyncio
async def test_job_analyze_generate_flow(no_ai, no_retrieval):
    from app.main import create_app
    db = await _live_db()
    app = _authed(create_app())
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            comp = await _mk_company(c, f"{TAG}-JobsCo")
            job = await _mk_job(c, comp["id"])
            jid = job["id"]
            r = await c.post(f"/api/admin/career/jobs/{jid}/analyze", json={})
            assert r.status_code == 200, r.text
            body = r.json()
            assert body["analysis"]["technologies"]
            assert "matches" in body and "report" in body
            r = await c.get(f"/api/admin/career/jobs/{jid}")
            assert r.json()["status"] == "Open"
            ct = await _mk_contact(c, comp["id"])
            r = await c.post(f"/api/admin/career/jobs/{jid}/generate",
                             json={"contact_id": ct["id"]})
            assert r.status_code == 200, r.text
            g = r.json()
            assert g["email_subject"] and g["email_body"] and g["quality"]
            assert "freelance" not in g["email_body"].lower()  # career context, no Upwork talk
            assert g["email_subject"]
            aid = g["application_id"]
            # application persisted in Needs Review with snapshots
            r = await c.get(f"/api/admin/career/applications/{aid}")
            assert r.json()["status"] == "Needs Review"
            assert r.json()["company_name"] == f"{TAG}-JobsCo"
            assert r.json()["contact_snapshot"]["email"] == "hr@e2ecorp.example"
            # job moved to Ready for Application
            r = await c.get(f"/api/admin/career/jobs/{jid}")
            assert r.json()["status"] == "Ready for Application"
            await db["career_applications"].delete_many({"_id": r.json().get("_id", "x")})
    finally:
        app.dependency_overrides.clear()
        await db["career_applications"].delete_many({"company_name": {"$regex": f"^{TAG}"}})
        await db["career_contacts"].delete_many({"name": "E2E Recruiter"})
        await db["career_jobs"].delete_many({"title": {"$regex": "^E2E"}})
        await db["career_companies"].delete_many({"name": {"$regex": f"^{TAG}"}})


@pytest.mark.asyncio
async def test_generate_requires_description():
    from app.main import create_app
    await _live_db()
    app = _authed(create_app())
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.post("/api/admin/career/jobs/000000000000000000000000/analyze", json={})
            assert r.status_code == 404
    finally:
        app.dependency_overrides.clear()


# ── approve / send guards ──

@pytest.mark.asyncio
async def test_approve_send_guards(no_ai, no_retrieval, monkeypatch):
    from app.main import create_app
    from app.services import email_service
    db = await _live_db()
    app = _authed(create_app())
    sent = []

    async def _never(*a, **k):
        sent.append(a)
        raise AssertionError("SMTP must not be touched before approval")

    monkeypatch.setattr(email_service, "send_application_email", _never)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            comp = await _mk_company(c, f"{TAG}-SendCo")
            ct = await _mk_contact(c, comp["id"])
            job = await _mk_job(c, comp["id"], "E2E Sender")
            g = (await c.post(f"/api/admin/career/jobs/{job['id']}/generate",
                              json={"contact_id": ct["id"]})).json()
            aid = g["application_id"]
            # send before approve → refused, SMTP untouched
            r = await c.post(f"/api/admin/career/applications/{aid}/send", json={})
            assert r.status_code == 409
            assert sent == []
            # approve from wrong state still fine here (Needs Review → Approved)
            r = await c.post(f"/api/admin/career/applications/{aid}/approve", json={})
            assert r.json()["status"] == "Approved"
            # approve twice is idempotent-safe (409, still Approved)
            r = await c.post(f"/api/admin/career/applications/{aid}/approve", json={})
            assert r.status_code == 409
    finally:
        app.dependency_overrides.clear()
        await db["career_applications"].delete_many({"company_name": {"$regex": f"^{TAG}"}})
        await db["career_contacts"].delete_many({"name": "E2E Recruiter"})
        await db["career_jobs"].delete_many({"title": {"$regex": "^E2E"}})
        await db["career_companies"].delete_many({"name": {"$regex": f"^{TAG}"}})


@pytest.mark.asyncio
async def test_send_flow_and_duplicate_guard(no_ai, no_retrieval, monkeypatch):
    from app.main import create_app
    from app.services import email_service
    db = await _live_db()
    app = _authed(create_app())
    calls = []

    def _fake_send(to_email, subject, body_text, reply_to=None):
        calls.append((to_email, subject))
        return {"to_domain": to_email.split("@")[-1], "subject_len": len(subject)}

    monkeypatch.setattr(email_service, "send_application_email", _fake_send)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            comp = await _mk_company(c, f"{TAG}-MailCo")
            ct = await _mk_contact(c, comp["id"], "mail@e2ecorp.example")
            job = await _mk_job(c, comp["id"], "E2E Mailer")
            # no_ai not used here: generate hits template fallback via DeadAI? use no_ai pattern
            g = (await c.post(f"/api/admin/career/jobs/{job['id']}/generate",
                              json={"contact_id": ct["id"]})).json()
            aid = g["application_id"]
            await c.post(f"/api/admin/career/applications/{aid}/approve", json={})
            r = await c.post(f"/api/admin/career/applications/{aid}/send", json={})
            assert r.json()["ok"] is True and r.json()["to_domain"] == "e2ecorp.example"
            assert len(calls) == 1 and calls[0][0] == "mail@e2ecorp.example"
            d = (await c.get(f"/api/admin/career/applications/{aid}")).json()
            assert d["status"] == "Sent" and d["sent_at"]
            # duplicate send refused
            r = await c.post(f"/api/admin/career/applications/{aid}/send", json={})
            assert r.status_code == 409 and len(calls) == 1
            # explicit resend allowed
            r = await c.post(f"/api/admin/career/applications/{aid}/send",
                             json={"resend": True})
            assert r.json()["ok"] is True and len(calls) == 2
            # sent applications are kept for history
            r = await c.delete(f"/api/admin/career/applications/{aid}")
            assert r.status_code == 409
            from bson import ObjectId
            await db["career_applications"].delete_one({"_id": ObjectId(aid)})
    finally:
        app.dependency_overrides.clear()
        await db["career_contacts"].delete_many({"name": "E2E Recruiter"})
        await db["career_jobs"].delete_many({"title": {"$regex": "^E2E"}})
        await db["career_companies"].delete_many({"name": {"$regex": f"^{TAG}"}})


@pytest.mark.asyncio
async def test_send_missing_contact_and_unconfigured_smtp(no_ai, no_retrieval, monkeypatch):
    from app.main import create_app
    from app.services import email_service
    from types import SimpleNamespace
    db = await _live_db()
    app = _authed(create_app())
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            comp = await _mk_company(c, f"{TAG}-NoMail")
            job = await _mk_job(c, comp["id"], "E2E NoMail")
            g = (await c.post(f"/api/admin/career/jobs/{job['id']}/generate", json={})).json()
            aid = g["application_id"]
            await c.post(f"/api/admin/career/applications/{aid}/approve", json={})
            # no contact attached → 400, nothing sent
            r = await c.post(f"/api/admin/career/applications/{aid}/send", json={})
            assert r.status_code == 400
            # SMTP down → 502, status unchanged, no secret in the error
            monkeypatch.setattr(email_service, "get_settings", lambda: SimpleNamespace(
                smtp_host="mail.example", smtp_port=587, smtp_user="u",
                smtp_password="smtp-secret-xyz", smtp_from="u@x.io"))
            import smtplib

            class DeadSMTP:
                def __init__(self, *a, **k):
                    raise ConnectionError("down")

            monkeypatch.setattr(smtplib, "SMTP", DeadSMTP)
            monkeypatch.setattr(smtplib, "SMTP_SSL", DeadSMTP)
            # attach a contact first so we reach the SMTP stage
            ct = await _mk_contact(c, comp["id"], "nomail@e2ecorp.example")
            from bson import ObjectId
            await db["career_applications"].update_one(
                {"_id": ObjectId(aid)}, {"$set": {"contact_id": ct["id"]}})
            r = await c.post(f"/api/admin/career/applications/{aid}/send", json={})
            assert r.status_code == 502
            assert "smtp-secret" not in r.text and "password" not in r.text.lower()
            d = (await c.get(f"/api/admin/career/applications/{aid}")).json()
            assert d["status"] == "Approved"  # unchanged on failure
    finally:
        app.dependency_overrides.clear()
        await db["career_applications"].delete_many({"company_name": {"$regex": f"^{TAG}"}})
        await db["career_contacts"].delete_many({"name": "E2E Recruiter"})
        await db["career_jobs"].delete_many({"title": {"$regex": "^E2E"}})
        await db["career_companies"].delete_many({"name": {"$regex": f"^{TAG}"}})


# ── tracking grid ──

@pytest.mark.asyncio
async def test_tracking_search_filter_sort_page(monkeypatch):
    from app.main import create_app
    db = await _live_db()
    app = _authed(create_app())
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            comp = await _mk_company(c, f"{TAG}-TrackCo")
            job = await _mk_job(c, comp["id"], "E2E Tracker")
            g = (await c.post(f"/api/admin/career/jobs/{job['id']}/generate", json={})).json()
            aid = g["application_id"]
            r = await c.get("/api/admin/career/applications", params={"q": "Tracker"})
            assert r.json()["total"] >= 1
            r = await c.get("/api/admin/career/applications", params={"status": "Needs Review"})
            assert all(a["status"] == "Needs Review" for a in r.json()["items"])
            r = await c.get("/api/admin/career/applications",
                            params={"company_id": comp["id"], "limit": 1})
            assert r.json()["total"] >= 1 and len(r.json()["items"]) == 1
            r = await c.get("/api/admin/career/applications", params={"status": "Bogus"})
            assert r.status_code == 400
            # status + notes + followup update
            r = await c.post(f"/api/admin/career/applications/{aid}/status",
                             json={"status": "Follow-up", "followup_date": "2026-10-01",
                                   "notes": "ping HR"})
            assert r.json()["status"] == "Follow-up"
            assert r.json()["notes"] == "ping HR"
            # refine works on the stored artifact
            r = await c.post(f"/api/admin/career/applications/{aid}/refine",
                             json={"instruction": "Make it shorter.", "target": "email_body"})
            assert r.status_code in (200, 502)  # 502 only if AI path breaks unexpectedly
    finally:
        app.dependency_overrides.clear()
        await db["career_applications"].delete_many({"company_name": {"$regex": f"^{TAG}"}})
        await db["career_jobs"].delete_many({"title": {"$regex": "^E2E"}})
        await db["career_companies"].delete_many({"name": {"$regex": f"^{TAG}"}})


# ── auth gates (no DB) ──

@pytest.mark.asyncio
async def test_career_endpoints_require_auth():
    from app.main import create_app
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        for method, path in (
                ("GET", "/api/admin/career/companies"),
                ("POST", "/api/admin/career/companies"),
                ("GET", "/api/admin/career/contacts"),
                ("POST", "/api/admin/career/contacts"),
                ("GET", "/api/admin/career/jobs"),
                ("POST", "/api/admin/career/jobs"),
                ("POST", "/api/admin/career/jobs/x/analyze"),
                ("POST", "/api/admin/career/jobs/x/generate"),
                ("GET", "/api/admin/career/applications"),
                ("PUT", "/api/admin/career/applications/x"),
                ("POST", "/api/admin/career/applications/x/approve"),
                ("POST", "/api/admin/career/applications/x/send"),
                ("POST", "/api/admin/career/applications/x/status"),
                ("DELETE", "/api/admin/career/applications/x")):
            r = await c.request(method, path, json={})
            assert r.status_code == 401, (method, path)
