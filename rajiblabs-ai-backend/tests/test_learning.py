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


# ---------- validate_block_quality tests ----------

def _good_block(**overrides):
    """Build a high-quality block that passes all quality checks."""
    base = {
        "day_number": 2,
        "topic": "Variables",
        "learning_objective": "Create a variable and print its value to the console",
        "why_matters": "Every program stores data — variables are how you hold a customer name, a price, or a score in your shopping app",
        "real_world_example": "Imagine you are building a small shopping app. A Customer has a name and email. A Product has a name and price. Today you learn how to store these pieces of data.",
        "simple_explanation": "A variable is like a labeled box. You put a value inside and give it a name. Later you can open the box and use the value.",
        "concept_explanation": "In programming a variable stores a value. Think of it as a container with a label. You create it, name it, and use it.",
        "step_by_step": [
            "Create a variable called customerName with your name",
            "Print the variable to see its value",
            "Change the value and print again",
        ],
        "examples": [{"title": "Hello variable", "code": "x = 1\nprint(x)", "explanation": "We create x and print it", "expected_output": "1"}],
        "try_it_yourself": "Change the value from 1 to 42 and run again",
        "common_mistakes": ["Forgetting to assign a value before using it — Python will give a NameError because the box is empty"],
        "exercise": "Create a variable called price, set it to 9.99, and print it",
        "homework": "Create two variables, add them, and print the result",
        "quick_review": ["Variables store values", "You can change a variable value"],
        "what_you_can_do_now": ["Create a variable and print it", "Change a variable value"],
        "questions": ["What is a variable?", "How do you create one?"],
    }
    base.update(overrides)
    return base


def test_quality_passes_on_good_block():
    from app.services.learning_agent import validate_block_quality
    passed, issues, improvements = validate_block_quality(_good_block(), day=2, topic="Python")
    assert passed is True
    assert issues == []


def test_quality_fails_on_abstract_real_world():
    from app.services.learning_agent import validate_block_quality
    block = _good_block(real_world_example="In general, this is typically useful for many things in broad terms")
    passed, issues, improvements = validate_block_quality(block, day=2)
    assert passed is False
    assert any("too short" in i or "abstract" in i for i in issues + improvements)


def test_quality_fails_on_short_real_world():
    from app.services.learning_agent import validate_block_quality
    block = _good_block(real_world_example="Short example")
    passed, issues, improvements = validate_block_quality(block, day=2)
    assert passed is False
    assert any("too short" in i for i in issues)


def test_quality_flags_no_doing_words_in_objective():
    from app.services.learning_agent import validate_block_quality
    block = _good_block(learning_objective="Understanding variables and their importance in programming")
    passed, issues, improvements = validate_block_quality(block, day=2)
    # Should have improvement about doing words
    assert any("DO" in imp for imp in improvements)


def test_quality_flags_code_without_explanation():
    from app.services.learning_agent import validate_block_quality
    block = _good_block(examples=[{"title": "Example", "code": "x = 1\nprint(x)", "explanation": "", "expected_output": "1"}])
    passed, issues, improvements = validate_block_quality(block, day=2)
    assert any("no explanation" in i for i in issues)


def test_quality_flags_short_exercise():
    from app.services.learning_agent import validate_block_quality
    block = _good_block(exercise="Do something")
    passed, issues, improvements = validate_block_quality(block, day=2)
    assert any("too short" in i for i in issues)


def test_quality_flags_vague_try_it():
    from app.services.learning_agent import validate_block_quality
    block = _good_block(try_it_yourself="Try it")
    passed, issues, improvements = validate_block_quality(block, day=2)
    assert any("vague" in imp for imp in improvements)


def test_quality_flags_generic_why_matters():
    from app.services.learning_agent import validate_block_quality
    block = _good_block(why_matters="This is important")
    passed, issues, improvements = validate_block_quality(block, day=2)
    assert any("generic" in imp or "short" in i for imp, i in [(imp, "") for imp in improvements] + [("", i) for i in issues])


def test_quality_flags_vague_abilities():
    from app.services.learning_agent import validate_block_quality
    block = _good_block(what_you_can_do_now=["Understand variables", "Know about types"])
    passed, issues, improvements = validate_block_quality(block, day=2)
    assert any("vague" in imp for imp in improvements)


def test_quality_detects_repetition_from_prev_day():
    from app.services.learning_agent import validate_block_quality
    prev = {"learning_objective": "Create a variable and print its value to the console"}
    block = _good_block(learning_objective="Create a variable and print its value to the console")
    passed, issues, improvements = validate_block_quality(block, day=2, prev_block=prev)
    assert any("overlaps" in imp for imp in improvements)


def test_quality_long_code_in_early_days():
    from app.services.learning_agent import validate_block_quality
    long_code = "x = 1\n" * 100  # >500 chars
    block = _good_block(examples=[{"title": "Long", "code": long_code, "explanation": "Long code", "expected_output": ""}])
    passed, issues, improvements = validate_block_quality(block, day=2)
    assert any("long" in imp for imp in improvements)


# ---------- validate_path_coherence tests ----------

def test_path_coherence_empty_blocks():
    from app.services.learning_agent import validate_path_coherence
    path = {"topic": "Python", "duration": 5, "roadmap": [], "prerequisites": []}
    ok, issues = validate_path_coherence(path, [])
    assert ok is False
    assert any("No blocks" in i for i in issues)


def test_path_coherence_repeated_titles():
    from app.services.learning_agent import validate_path_coherence
    path = {"topic": "Python", "duration": 3, "roadmap": [], "prerequisites": []}
    blocks = [
        {"day_number": 1, "title": "Intro", "status": "published"},
        {"day_number": 2, "title": "Intro", "status": "published"},
        {"day_number": 3, "title": "Functions", "status": "published"},
    ]
    ok, issues = validate_path_coherence(path, blocks)
    assert any("repeats" in i for i in issues)


def test_path_coherence_day1_advanced_concepts():
    from app.services.learning_agent import validate_path_coherence
    path = {"topic": "C#", "duration": 5, "roadmap": [], "prerequisites": []}
    blocks = [
        {"day_number": 1, "title": "Interfaces", "learning_objective": "Understand interfaces and generics", "status": "published"},
    ]
    ok, issues = validate_path_coherence(path, blocks)
    assert any("advanced" in i.lower() for i in issues)


def test_path_coherence_missing_exercises_in_later_days():
    from app.services.learning_agent import validate_path_coherence
    path = {"topic": "Python", "duration": 5, "roadmap": [], "prerequisites": []}
    blocks = [
        {"day_number": 1, "title": "Intro", "status": "published"},
        {"day_number": 2, "title": "Vars", "status": "published"},
        {"day_number": 3, "title": "Functions", "status": "published", "exercise": "Do something"},
        {"day_number": 4, "title": "Classes", "status": "published"},
        {"day_number": 5, "title": "Projects", "status": "published"},
    ]
    ok, issues = validate_path_coherence(path, blocks)
    assert any("without exercise" in i for i in issues)


def test_path_coherence_too_many_prerequisites():
    from app.services.learning_agent import validate_path_coherence
    path = {"topic": "Python", "duration": 5, "roadmap": [], "prerequisites": ["A", "B", "C", "D", "E"]}
    blocks = [
        {"day_number": 1, "title": "Intro", "status": "published"},
        {"day_number": 2, "title": "Vars", "status": "published"},
    ]
    ok, issues = validate_path_coherence(path, blocks)
    assert any("prerequisites" in i.lower() for i in issues)


def test_path_coherence_passes_on_good_path():
    from app.services.learning_agent import validate_path_coherence
    path = {"topic": "Python", "duration": 3, "roadmap": [], "prerequisites": ["Basic computer use"]}
    blocks = [
        {"day_number": 1, "title": "First Steps", "learning_objective": "Create your first program", "status": "published", "exercise": "Run hello world", "examples": [{"code": "print('hello')"}]},
        {"day_number": 2, "title": "Variables", "learning_objective": "Create a variable and use it", "status": "published", "exercise": "Store a number", "examples": [{"code": "x = 1"}]},
        {"day_number": 3, "title": "Functions", "learning_objective": "Write a function that adds two numbers", "status": "published", "exercise": "Write add function", "examples": [{"code": "def add(a,b): return a+b"}]},
    ]
    ok, issues = validate_path_coherence(path, blocks)
    assert ok is True
    assert issues == []

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
