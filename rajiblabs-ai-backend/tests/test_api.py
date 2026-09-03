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
