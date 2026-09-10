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


def test_status_synonyms_normalize_to_canonical():
    from app.services.learning_agent import normalize_path_status
    assert normalize_path_status("live") == "active"
    assert normalize_path_status("published") == "active"
    assert normalize_path_status("LIVE") == "active"
    assert normalize_path_status("draft") == "planned"
    assert normalize_path_status("active") == "active"
    assert normalize_path_status("completed") == "completed"
    import pytest as _pt
    with _pt.raises(ValueError):
        normalize_path_status("bogus")


def test_public_visibility_matrix_pure():
    from app.services.learning_agent import is_path_visible
    for visible in ("active", "completed", "live", "published"):
        assert is_path_visible({"status": visible}) is True, visible
    for hidden in ("planned", "draft", "paused", "archived", None):
        assert is_path_visible({"status": hidden}) is False, hidden
    assert is_path_visible(None) is False
    assert is_path_visible({}) is False

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
            # Draft (planned) path stays fully hidden: detail + blocks 404
            assert (await c.get(f"/api/learning/paths/{slug}")).status_code == 404
            assert (await c.get(f"/api/learning/paths/{slug}/blocks")).status_code == 404
            # Cleanup
            db = get_db()
            await db["learning_paths"].delete_many({"slug": slug})
            await db["learning_blocks"].delete_many({"slug": slug})


@pytest.mark.asyncio
async def test_live_path_visibility_flow():
    """Admin → Live → public list/detail/blocks; draft/archived stay hidden."""
    from unittest.mock import AsyncMock, patch
    from app.main import create_app
    from app.database import get_db
    app = create_app()
    try:
        db = get_db()
        await db.command("ping")
    except Exception:
        pytest.skip("Mongo not available")

    async def mock_roadmap(topic, duration, goal="", level=""):
        return {"roadmap": [{"day": i+1, "title": f"Day {i+1}", "objective": f"Obj {i+1}", "why_matters": f"Why {i+1}"} for i in range(duration)], "prerequisites": ["Basic computer use"]}

    slug = "testlearnvisibility"
    with patch("app.services.learning_agent._generate_roadmap", new=AsyncMock(side_effect=mock_roadmap)):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            from app.config import get_settings
            s = get_settings()
            pw = s.admin_initial_password or "Test@1234"
            email = s.admin_email_list[0] if hasattr(s, 'admin_email_list') else "rajibmahata143@gmail.com"
            r = await c.post("/api/admin/login", json={"email": email, "password": pw})
            if r.status_code != 200:
                pytest.skip("Admin login failed")
            token = r.json().get("token") or r.json().get("access_token") or ""
            headers = {"Authorization": f"Bearer {token}"}
            try:
                r = await c.post("/api/admin/learning/paths", json={"topic": "TestLearnVisibility", "duration": 3, "goal": "Visibility goal", "level": "beginner"}, headers=headers)
                assert r.status_code == 200, r.text
                # 1. freshly created = planned → invisible everywhere public
                assert r.json().get("status") == "planned"
                assert all(p.get("slug") != slug for p in (await c.get("/api/learning/paths")).json())
                assert (await c.get(f"/api/learning/paths/{slug}")).status_code == 404
                assert (await c.get(f"/api/learning/paths/{slug}/blocks")).status_code == 404
                # 2. admin marks LIVE (synonym) → stored canonical, publicly visible
                r = await c.patch(f"/api/admin/learning/paths/{slug}", json={"status": "live"}, headers=headers)
                assert r.status_code == 200, r.text
                assert r.json().get("status") == "active"
                assert any(p.get("slug") == slug for p in (await c.get("/api/learning/paths")).json())
                r = await c.get(f"/api/learning/paths/{slug}")
                assert r.status_code == 200 and r.json().get("goal") == "Visibility goal"
                # blocks still empty — nothing published yet
                r = await c.get(f"/api/learning/paths/{slug}/blocks")
                assert r.status_code == 200 and r.json() == []
                assert (await c.get(f"/api/learning/paths/{slug}/blocks/1")).status_code == 404
                # 3. publish day 1 only → day 1 visible, day 2 still 404
                db = get_db()
                path = await db["learning_paths"].find_one({"slug": slug})
                await db["learning_blocks"].update_one(
                    {"path_id": path["_id"], "day_number": 1},
                    {"$set": {"status": "published", "concept_explanation": "Published concept",
                              "exercise": "Published exercise", "homework": "Published homework"}})
                r = await c.get(f"/api/learning/paths/{slug}/blocks")
                assert r.status_code == 200 and len(r.json()) == 1
                r = await c.get(f"/api/learning/paths/{slug}/blocks/1")
                assert r.status_code == 200 and r.json().get("exercise") == "Published exercise"
                assert (await c.get(f"/api/learning/paths/{slug}/blocks/2")).status_code == 404
                # 4. archived → hidden again everywhere public
                r = await c.patch(f"/api/admin/learning/paths/{slug}", json={"status": "archived"}, headers=headers)
                assert r.status_code == 200
                assert all(p.get("slug") != slug for p in (await c.get("/api/learning/paths")).json())
                assert (await c.get(f"/api/learning/paths/{slug}")).status_code == 404
                assert (await c.get(f"/api/learning/paths/{slug}/blocks")).status_code == 404
                assert (await c.get(f"/api/learning/paths/{slug}/blocks/1")).status_code == 404
            finally:
                db = get_db()
                await db["learning_paths"].delete_many({"slug": slug})
                await db["learning_blocks"].delete_many({"slug": slug})
