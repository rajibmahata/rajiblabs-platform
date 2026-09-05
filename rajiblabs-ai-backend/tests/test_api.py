"""Deterministic API tests (no OpenAI/GitHub network)."""
import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_health():
    from app.main import create_app
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/health")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] in ("ok", "degraded")
        assert "database" in body and "github" in body and "openai" in body
        assert "token" not in str(body).lower()


@pytest.mark.asyncio
async def test_public_projects_published_only():
    from app.main import create_app
    app = create_app()
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.get("/api/public/projects")
    except Exception:
        pytest.skip("MongoDB not running locally")
        return
    if r.status_code == 500:
        pytest.skip("MongoDB not running locally")
        return
    assert r.status_code == 200
    for p in r.json():
        assert p.get("published", True) is True


def test_github_url_validator():
    from app.schemas import ProjectIn
    import pytest as pt
    with pt.raises(Exception):
        ProjectIn(name="XX", github_url="https://github.com/rajibmahata")
    ok = ProjectIn(name="PestFlow", github_url="https://github.com/rajibmahata/pestflow")
    assert ok.github_url.endswith("/pestflow")
    none_ok = ProjectIn(name="YY", github_url=None)
    assert none_ok.github_url is None


def test_quality_flags_hype():
    from app.schemas import AIContentOut
    from app.services.quality import score_content
    c = AIContentOut(title="T", short_description="s", description="millions of users love it",
                     technology_summary=".NET", seo_title="t", seo_description="d")
    score = score_content(c, "evidence")
    assert score.passed is False and score.flags


def test_lifespan_wired_no_legacy_startup():
    """Gap fix: scheduler lifespan must be wired; deprecated on_event removed."""
    from app.main import create_app
    app = create_app()
    assert app.router.lifespan_context is not None
    assert list(app.router.on_startup) == []


def test_log_truncate_caps_length():
    from app.services.notify import _truncate
    assert _truncate("abc", 5) == "abc"
    long = _truncate("x" * 3000, 2000)
    assert long == "x" * 2000 + "…(truncated)"


@pytest.mark.asyncio
async def test_admin_logs_require_auth():
    """System Logs endpoints reject anonymous callers before touching the DB."""
    from app.main import create_app
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        for path in ("/api/admin/logs", "/api/admin/logs/stats"):
            r = await c.get(path)
            assert r.status_code == 401, path


@pytest.mark.asyncio
async def test_admin_cms_require_auth():
    from app.main import create_app
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        for path in ("/api/admin/dashboard", "/api/admin/projects", "/api/admin/leads"):
            r = await c.get(path)
            assert r.status_code == 401, path


@pytest.mark.asyncio
async def test_legacy_admin_require_auth():
    """Ported .NET-parity routes reject anonymous callers before touching the DB."""
    from app.main import create_app
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        for path in ("/api/admin/resumes", "/api/admin/portfolio", "/api/admin/products",
                     "/api/admin/profile", "/api/admin/content", "/api/admin/github/repos",
                     "/api/admin/github/sync-log"):
            r = await c.get(path)
            assert r.status_code == 401, path


def _norm(path: str) -> str:
    import re
    return re.sub(r"\{[^}]*\}", "{}", path)


def test_legacy_routes_registered():
    """All React-panel legacy paths exist in the OpenAPI spec
    (path-param names normalized — {rid} vs {pid} is irrelevant)."""
    from app.main import create_app
    spec = create_app().openapi()
    paths = {_norm(p) for p in spec["paths"]}
    for p in ("/api/admin/resumes", "/api/admin/resumes/upload",
              "/api/admin/resumes/{}/download", "/api/admin/resumes/{}",
              "/api/admin/resumes/{}/extraction", "/api/admin/resumes/{}/extract",
              "/api/admin/resumes/extraction/{}/decision",
              "/api/admin/portfolio", "/api/admin/portfolio/{}",
              "/api/admin/products", "/api/admin/products/{}",
              "/api/admin/github/repos", "/api/admin/github/sync-log",
              "/api/admin/github/sync", "/api/admin/github/repos/{}",
              "/api/admin/profile", "/api/admin/dashboard",
              "/api/admin/content", "/api/admin/content/{}",
              "/api/portfolio", "/api/portfolio/{}",
              "/api/products", "/api/products/{}",
              "/api/content/{}",
              # legacy auth + public surface used by the React panel
              "/api/admin/login", "/api/admin/logout", "/api/admin/me",
              "/api/resume/current"):
        assert p in paths, p


@pytest.mark.asyncio
async def test_swagger_spec_tagged():
    """Swagger: every operation tagged, docs served outside production."""
    from app.main import create_app
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/openapi.json")
        assert r.status_code == 200
        spec = r.json()
        assert spec["info"]["title"] == "RajibLabs API"
        ops = [d for item in spec["paths"].values() for d in item.values()]
        assert len(ops) >= 40
        assert all(d.get("tags") for d in ops)
        ui = await c.get("/docs")
        assert ui.status_code == 200


# ── Site API (v1) .NET-parity — DB-free checks + live checks that skip
# gracefully when MongoDB is not running (same pattern as existing tests). ──

LIVE_PATHS = ["/api/projects", "/api/activity?limit=3", "/api/profile",
              "/api/learning", "/api/health", "/api/portfolio",
              "/api/products", "/api/content/home_order", "/api/resume/current"]


@pytest.mark.asyncio
async def test_legacy_public_shapes():
    """Every ported public path responds; lists keep .NET camelCase shapes."""
    from app.main import create_app
    app = create_app()
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.get("/api/projects")
    except Exception:
        pytest.skip("MongoDB not running locally")
        return
    if r.status_code == 500:
        pytest.skip("MongoDB not running locally")
        return
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        for path in LIVE_PATHS:
            r = await c.get(path)
            assert r.status_code == 200, path
        projects = (await c.get("/api/projects")).json()
        if projects:
            p = projects[0]
            for key in ("id", "title", "slug", "description", "techStack",
                        "gitHubUrl", "status", "createdAt", "updatedAt"):
                assert key in p, key
        profile = (await c.get("/api/profile")).json()
        for key in ("id", "fullName", "title", "bio", "skills", "socialLinks", "career"):
            assert key in profile, key


@pytest.mark.asyncio
async def test_legacy_validation_no_db():
    """Input validation fires before any DB access (no Mongo needed)."""
    from app.main import create_app
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.post("/api/contact", json={"name": "", "email": "a@b.c", "message": "hi"})
        assert r.status_code == 400
        r = await c.post("/api/subscribe", json={"email": "not-an-email"})
        assert r.status_code == 400
        r = await c.post("/api/admin/login", json={"username": "stranger@x.com", "password": "x"})
        assert r.status_code == 401
        for path in ("/api/admin/me", "/api/admin/dashboard", "/api/admin/portfolio",
                     "/api/admin/products", "/api/admin/profile", "/api/admin/content",
                     "/api/admin/resumes", "/api/admin/github/repos"):
            r = await c.get(path)
            assert r.status_code == 401, path


# ── System Logs: scrub, query builder, retention, cleanup ──

def test_scrub_redacts_secrets():
    from app.services.notify import scrub_text
    assert scrub_text("login failed for password=hunter2 ok") == \
        "login failed for password=*** ok"
    assert "sk-" not in scrub_text("openai key sk-abc123XYZ789 failed")
    assert "***token***" in scrub_text("key sk-abc123XYZ789 failed")
    assert "ghp_" not in scrub_text("token ghp_abcdefgh12345678 here")
    assert scrub_text("auth Bearer abcDEF123._-xyz") == "auth Bearer ***"
    out = scrub_text("connect mongodb://admin:s3cret@host:27017/db now")
    assert "s3cret" not in out and "***@" in out
    clean = "plain failure with no secrets, retry in 5s"
    assert scrub_text(clean) == clean


def test_normalize_level():
    from app.services.notify import normalize_level
    assert normalize_level("info") == "info"
    assert normalize_level("warning") == "warning"
    assert normalize_level("error") == "error"
    assert normalize_level("CRITICAL") == "error"
    assert normalize_level("") == "error"


def test_retention_cutoff_days():
    from datetime import datetime, timezone
    from app.services.notify import retention_cutoff
    now = datetime(2026, 9, 4, 12, 0, tzinfo=timezone.utc)
    assert (now - retention_cutoff(7, now)).days == 7
    assert retention_cutoff(0, now) < now  # clamped to >= 1 day


def test_build_log_query_window_always_applied():
    from datetime import datetime, timezone
    from app.routers.admin_logs import build_log_query
    w = datetime(2026, 8, 28, tzinfo=timezone.utc)
    assert build_log_query(window_start=w) == {"created_at": {"$gte": w}}
    assert "created_at" not in build_log_query()  # no window → no cutoff
    q = build_log_query(level="bogus", window_start=w)
    assert "level" not in q and q["created_at"] == {"$gte": w}


def test_build_log_query_filters():
    from datetime import datetime, timezone
    from app.routers.admin_logs import build_log_query
    w = datetime(2026, 8, 28, tzinfo=timezone.utc)
    frm = datetime(2026, 9, 1, tzinfo=timezone.utc)
    to = datetime(2026, 9, 3, tzinfo=timezone.utc)
    q = build_log_query(q="mongo (timeout)", level="error", source="daily_agent",
                        date_from=frm, date_to=to, window_start=w)
    assert q["level"] == "error" and q["source"] == "daily_agent"
    # date_from wins over the older window cutoff; date_to caps the range
    assert q["created_at"] == {"$gte": frm, "$lte": to}
    ors = q["$or"]
    assert {list(o)[0] for o in ors} == {"message", "source", "logger", "path", "details"}
    msg_rx = next(o["message"]["$regex"] for o in ors if "message" in o)
    assert "\\(" in msg_rx and "(timeout)" not in msg_rx  # escaped, not raw


@pytest.mark.asyncio
async def test_admin_log_detail_requires_auth():
    from app.main import create_app
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/api/admin/logs/507f1f77bcf86cd799439011")
        assert r.status_code == 401


async def _live_db():
    """Real Mongo if reachable, else skip (same pattern as existing tests)."""
    try:
        from app.database import get_db
        db = get_db()
        await db.command("ping")
        return db
    except Exception:
        pytest.skip("MongoDB not running locally")


@pytest.mark.asyncio
async def test_log_filtering_details_retention_live():
    import uuid
    from datetime import timedelta
    from app.database import utcnow
    from app.routers.admin_logs import build_log_query
    from app.services.notify import log_error, purge_old_logs
    db = await _live_db()
    marker = f"e2e-{uuid.uuid4().hex[:8]}"
    await log_error("e2e_source", f"boom {marker}", "traceback line",
                    level="info", logger="e2e.module", path="/api/e2e")
    await db["error_logs"].insert_one({
        "level": "error", "source": "e2e_old", "message": "ancient",
        "details": "", "created_at": utcnow() - timedelta(days=8)})
    try:
        # search finds the fresh entry with its extended fields
        q = build_log_query(q=marker)
        found = [d async for d in db["error_logs"].find(q)]
        assert len(found) == 1
        assert found[0]["logger"] == "e2e.module" and found[0]["path"] == "/api/e2e"
        # window excludes the 8-day-old entry even without other filters
        from app.services.notify import retention_cutoff
        recent = [d async for d in db["error_logs"].find(
            build_log_query(window_start=retention_cutoff(7)))]
        assert all(d["source"] != "e2e_old" for d in recent)
        # scheduled sweep deletes only the expired entry
        deleted = await purge_old_logs(db, days=7)
        assert deleted >= 1
        assert await db["error_logs"].count_documents({"source": "e2e_old"}) == 0
        assert await db["error_logs"].count_documents({"source": "e2e_source"}) == 1
    finally:
        await db["error_logs"].delete_many({"source": {"$in": ["e2e_source", "e2e_old"]}})


@pytest.mark.asyncio
async def test_log_error_scrubs_secrets_live():
    from app.services.notify import log_error
    db = await _live_db()
    await log_error("e2e_scrub", "call failed", "password=hunter2 token sk-abc123XYZ789",
                    level="error")
    try:
        d = await db["error_logs"].find_one({"source": "e2e_scrub"})
        assert d is not None and "hunter2" not in d["details"]
        assert "sk-abc123XYZ789" not in d["details"]
    finally:
        await db["error_logs"].delete_many({"source": "e2e_scrub"})
