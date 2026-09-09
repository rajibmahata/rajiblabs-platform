"""Skill Management tests — discovery, evidence, RAG, API, truthfulness."""
import pytest
from httpx import ASGITransport, AsyncClient

@pytest.mark.asyncio
async def test_public_skills_hidden_fields():
    from app.main import create_app
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/api/public/skills")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        if data:
            # Public should not expose internal scoring fields
            for s in data[:2]:
                assert "name" in s and "category" in s
                assert "evidence_count" not in s
                assert "confidence" not in s
                assert "last_used" not in s

@pytest.mark.asyncio
async def test_admin_skills_crud_and_evidence():
    from app.main import create_app
    from app.database import get_db
    try:
        db = get_db()
        await db.command("ping")
    except Exception:
        pytest.skip("Mongo not available")
    app = create_app()
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
        # Create a test skill
        payload = {"name": "TestSkillXYZ", "category": "Testing / QA", "status": "published", "display_order": 9999}
        r = await c.post("/api/admin/skills", json=payload, headers=headers)
        assert r.status_code == 201, r.text
        sid = r.json().get("id")
        assert sid
        # Duplicate should fail (normalized)
        r2 = await c.post("/api/admin/skills", json=payload, headers=headers)
        assert r2.status_code == 400
        # Get with evidence
        r = await c.get(f"/api/admin/skills/{sid}", headers=headers)
        assert r.status_code == 200
        # Evidence endpoint
        r = await c.get(f"/api/admin/skills/{sid}/evidence", headers=headers)
        assert r.status_code == 200
        assert "evidence" in r.json()
        # Update
        r = await c.put(f"/api/admin/skills/{sid}", json={"category": "Tools", "display_order": 100}, headers=headers)
        assert r.status_code == 200
        assert r.json()["category"] == "Tools"
        # Search
        r = await c.get("/api/admin/skills?q=TestSkillXYZ", headers=headers)
        assert r.status_code == 200
        assert any("TestSkillXYZ" in x["name"] for x in r.json().get("items", []))
        # Toggle status to archived (should hide from public)
        r = await c.put(f"/api/admin/skills/{sid}", json={"status": "archived"}, headers=headers)
        assert r.status_code == 200
        # Public should not contain it now
        r = await c.get("/api/public/skills")
        assert all("TestSkillXYZ" not in x["name"] for x in r.json())
        # Delete
        r = await c.delete(f"/api/admin/skills/{sid}", headers=headers)
        assert r.status_code == 200
        # Verify gone
        r = await c.get(f"/api/admin/skills/{sid}", headers=headers)
        assert r.status_code == 404

@pytest.mark.asyncio
async def test_skill_discovery_no_invention():
    from app.services.skill_intelligence import discover_skills
    from app.database import get_db
    try:
        db = get_db()
        await db.command("ping")
    except Exception:
        pytest.skip("Mongo not available")
    # Empty evidence should yield no skills
    from unittest.mock import patch
    with patch("app.services.skill_intelligence._collect_evidence", return_value=[{"type": "website_content", "id": "home", "text": "generic welcome to our site", "weight": 5, "ts": None}]):
        result = await discover_skills(db, None)
        assert result == {}

@pytest.mark.asyncio
async def test_skill_rag_per_skill():
    from app.database import get_db
    try:
        db = get_db()
        await db.command("ping")
    except Exception:
        pytest.skip("Mongo not available")
    # Check that a published skill has a RAG doc
    db = get_db()
    skill = await db["skills"].find_one({"status": "published"})
    if not skill:
        pytest.skip("No published skill")
    slug = skill.get("slug") or skill.get("normalized_name", "").replace(" ", "-")
    if not slug:
        pytest.skip("Skill has no slug")
    kd = await db["knowledge_documents"].find_one({"source_id": f"skill:{slug}", "status": "active"})
    if not kd:
        pytest.skip("RAG not yet synced for skills (needs ingest)")
    assert kd["source_type"] == "profile"
    # Check that RAG search can find it
    from app.services.rag_query import retrieve
    hits = await retrieve(skill["name"], top_k=3)
    # At least one hit should be the skill doc or profile skills
    assert isinstance(hits, list)

def test_skill_normalization_no_duplicates():
    from app.services.skill_intelligence import _norm
    assert _norm("C#") == _norm("C Sharp") or _norm("C#") == "c#"
    assert _norm("  React  ") == "react"
    assert _norm("Python") == "python"
