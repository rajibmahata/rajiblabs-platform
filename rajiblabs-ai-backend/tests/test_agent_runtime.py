"""Agent runtime tests — dispatch, scheduler, registration, failure modes."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


# ---------- Agent Function Signatures (sync, no DB) ----------

def test_all_agent_functions_accept_triggered_by():
    """All agent runner functions must accept (triggered_by: str)."""
    import inspect
    from app.services.profile_agent import run_profile_agent
    from app.services.learning_agent import run_daily as run_learning
    from app.services.marketing_agent import run_daily as run_marketing
    from app.agents.daily_agent import run_daily_agent

    for fn in [run_profile_agent, run_learning, run_marketing, run_daily_agent]:
        sig = inspect.signature(fn)
        params = list(sig.parameters.keys())
        assert "triggered_by" in params, f"{fn.__name__} missing triggered_by param"
        assert "db" not in params, f"{fn.__name__} should not require db param"


def test_scheduler_import_failure_does_not_crash():
    """Scheduler source must have try/except around each agent import."""
    import inspect
    from app.workers import scheduler as sched_mod
    src = inspect.getsource(sched_mod.start_scheduler)
    assert "try:" in src, "Scheduler missing try/except for agent imports"
    assert "except" in src, "Scheduler missing except handler"


# ---------- Agent Registration (async, DB required) ----------

@pytest.mark.asyncio
async def test_all_agent_slugs_discoverable():
    """All 4 seeded agents must be discoverable via list_agents."""
    from app.services.agent_config import list_agents
    from app.database import get_db

    try:
        db = get_db()
        await db.command("ping")
    except Exception:
        pytest.skip("Mongo not available")

    agents = await list_agents(db)
    slugs = {a["slug"] for a in agents}
    assert "rajiblabs-concierge" in slugs, "concierge missing"
    assert "rajiblabs-profile" in slugs, "profile missing"
    assert "rajiblabs-learning" in slugs, "learning missing"
    assert "rajiblabs-career" in slugs, "career missing"
    for a in agents:
        assert "slug" in a
        assert "enabled" in a
        assert "agent_type" in a


@pytest.mark.asyncio
async def test_disabled_agent_not_executable():
    """A disabled profile agent must skip execution."""
    from app.services.agent_config import get_agent, PROFILE_SLUG
    from app.services.profile_agent import run_profile_agent
    from app.database import get_db

    try:
        db = get_db()
        await db.command("ping")
    except Exception:
        pytest.skip("Mongo not available")

    original = await db["ai_agents"].find_one({"slug": PROFILE_SLUG})
    if not original:
        pytest.skip("Profile agent not seeded")
    was_enabled = original.get("enabled", True)
    await db["ai_agents"].update_one({"slug": PROFILE_SLUG}, {"$set": {"enabled": False}})
    try:
        cfg = await get_agent(db, PROFILE_SLUG)
        assert cfg["enabled"] is False
        result = await run_profile_agent(triggered_by="test")
        assert result.get("skipped") is True
    finally:
        await db["ai_agents"].update_one({"slug": PROFILE_SLUG}, {"$set": {"enabled": was_enabled}})


# ---------- Scheduler ----------

@pytest.mark.asyncio
async def test_scheduler_registers_all_jobs():
    """Scheduler must register all 4 agent jobs."""
    from app.workers.scheduler import start_scheduler

    sched = start_scheduler()
    assert sched is not None
    job_ids = {job.id for job in sched.get_jobs()}
    assert "daily-agent" in job_ids, "daily-agent not registered"
    assert "profile-agent" in job_ids, "profile-agent not registered"
    assert "marketing-agent" in job_ids, "marketing-agent not registered"
    assert "learning-agent" in job_ids, "learning-agent not registered"


# ---------- Admin Ops Dispatch (single async test to avoid motor loop issues) ----------

@pytest.mark.asyncio
async def test_dispatch_all_agents():
    """All 3 agent dispatches must not return TypeError/ImportError (500)."""
    from app.main import create_app
    from httpx import ASGITransport, AsyncClient
    from app.database import get_db
    from app.config import get_settings

    try:
        db = get_db()
        await db.command("ping")
    except Exception:
        pytest.skip("Mongo not available")

    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        s = get_settings()
        pw = s.admin_initial_password or "Test@1234"
        email = s.admin_email_list[0] if hasattr(s, 'admin_email_list') else "rajibmahata143@gmail.com"
        r = await c.post("/api/admin/login", json={"email": email, "password": pw})
        if r.status_code != 200:
            pytest.skip("Admin login failed")
        token = r.json().get("token") or r.json().get("access_token") or ""
        headers = {"Authorization": f"Bearer {token}"}

        # Test all 3 dispatchable agents
        for slug in ["rajiblabs-profile", "rajiblabs-learning", "rajiblabs-marketing"]:
            await db["ai_agents"].update_one({"slug": slug}, {"$set": {"enabled": True}})
            r = await c.post(f"/api/admin/ops/agents/{slug}/run", headers=headers)
            assert r.status_code != 500 or "dispatch failed" not in r.text, f"Dispatch broken for {slug}: {r.text}"
            assert r.status_code in (200, 409), f"Unexpected status for {slug}: {r.status_code} {r.text}"


# ---------- Agent Run Recording ----------

@pytest.mark.asyncio
async def test_agent_runs_recorded():
    """Profile and learning agents must record runs in their collections."""
    from app.database import get_db

    try:
        db = get_db()
        await db.command("ping")
    except Exception:
        pytest.skip("Mongo not available")

    for coll in ["profile_agent_runs", "learning_agent_runs"]:
        last = await db[coll].find_one(sort=[("started_at", -1)])
        if last:
            assert "status" in last
            assert "started_at" in last
            assert "triggered_by" in last
