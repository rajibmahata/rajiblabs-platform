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
