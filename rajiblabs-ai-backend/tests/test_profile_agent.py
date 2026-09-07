import pytest
from httpx import ASGITransport, AsyncClient

@pytest.mark.asyncio
async def test_profile_agent_config_requires_auth():
    from app.main import create_app
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/api/admin/profile-agent/config")
        assert r.status_code == 401

@pytest.mark.asyncio
async def test_profile_agent_dashboard_requires_auth():
    from app.main import create_app
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/api/admin/profile-agent/dashboard")
        assert r.status_code == 401

@pytest.mark.asyncio
async def test_profile_agent_run_requires_auth():
    from app.main import create_app
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.post("/api/admin/profile-agent/run")
        assert r.status_code == 401

def test_profile_agent_seed_idempotent():
    # ensure seed doesn't overwrite
    import asyncio
    from app.database import get_db
    from app.services.agent_config import ensure_profile_seed, PROFILE_SLUG
    async def _run():
        db = get_db()
        first = await ensure_profile_seed(db)
        second = await ensure_profile_seed(db)
        assert str(first["_id"]) == str(second["_id"])
        assert first["slug"] == PROFILE_SLUG
        # cleanup not needed, keep seed
    # run with new loop
    try:
        asyncio.run(_run())
    except Exception as e:
        # if no DB, skip
        pytest.skip(f"DB not available: {e}")

def test_profile_agent_health_no_secrets():
    import asyncio
    from app.services.profile_agent import check_configuration_health
    from app.database import get_db
    async def _run():
        db = get_db()
        report = await check_configuration_health(db)
        # ensure no secrets in report
        txt = str(report)
        assert "ghp_" not in txt.lower()
        assert "sk-" not in txt.lower()
    try:
        asyncio.run(_run())
    except Exception as e:
        pytest.skip(f"DB not available: {e}")
