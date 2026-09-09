"""Learning Management tests — autonomous, hash-guarded, RAG-aware."""
import pytest
from httpx import ASGITransport, AsyncClient

@pytest.mark.asyncio
async def test_learning_requires_auth():
    from app.main import create_app
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/api/admin/learning/paths")
        assert r.status_code == 401
        r = await c.post("/api/admin/learning/paths", json={"topic": "C#", "duration": 5})
        assert r.status_code == 401

@pytest.mark.asyncio
async def test_public_learning_open():
    from app.main import create_app
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/api/learning/paths")
        assert r.status_code == 200
        r = await c.get("/api/learning/active")
        assert r.status_code == 200
        r = await c.get("/api/learning/topics")
        assert r.status_code == 200

def test_roadmap_hash_stable():
    from app.services.learning_agent import _hash
    assert _hash("C#", "10", "goal") == _hash("C#", "10", "goal")
    assert _hash("C#", "10", "goal") != _hash("C#", "11", "goal")

@pytest.mark.asyncio
async def test_learning_path_create_and_blocks():
    from unittest.mock import AsyncMock, patch
    from app.main import create_app
    from app.database import get_db
    app = create_app()
    # Need auth — try to get admin token via direct DB seed
    try:
        db = get_db()
        await db.command("ping")
    except Exception:
        pytest.skip("Mongo not available")
    # Mock roadmap to avoid LLM
    async def mock_roadmap(topic, duration, goal="", level=""):
        return {"roadmap": [{"day": i+1, "title": f"Day {i+1}", "objective": f"Obj {i+1}", "why_matters": f"Why {i+1}"} for i in range(duration)], "prerequisites": []}
    with patch("app.services.learning_agent._generate_roadmap", new=AsyncMock(side_effect=mock_roadmap)):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            # Login as admin (use seed)
            from app.config import get_settings
            s = get_settings()
            pw = s.admin_initial_password or "Test@1234"
            email = s.admin_email_list[0] if hasattr(s, 'admin_email_list') else "rajibmahata143@gmail.com"
            r = await c.post("/api/admin/login", json={"email": email, "password": pw})
            if r.status_code != 200:
                pytest.skip("Admin login failed")
            token = r.json().get("token") or r.json().get("access_token") or ""
            headers = {"Authorization": f"Bearer {token}"}
            # Create path
            r = await c.post("/api/admin/learning/paths", json={"topic": "TestLearnPython", "duration": 3, "goal": "Test", "level": "beginner"}, headers=headers)
            assert r.status_code == 200, r.text
            slug = r.json().get("slug")
            assert slug == "testlearnpython"
            # List blocks
            r = await c.get(f"/api/admin/learning/paths/{slug}/blocks", headers=headers)
            assert r.status_code == 200
            blocks = r.json()
            assert len(blocks) == 3
            assert blocks[0]["day_number"] == 1
            # Public should see 0 published initially (all planned)
            r = await c.get(f"/api/learning/paths/{slug}/blocks")
            assert r.status_code == 200
            assert len(r.json()) == 0
            # Cleanup
            db = get_db()
            await db["learning_paths"].delete_many({"slug": slug})
            await db["learning_blocks"].delete_many({"slug": slug})
