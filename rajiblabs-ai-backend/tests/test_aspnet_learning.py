"""ASP.NET Core course validation tests."""
import pytest
from app.database import get_db
from app.services.learning_agent import validate_block_quality, validate_path_coherence


@pytest.mark.asyncio
async def test_aspnet_path_exists():
    """ASP.NET Core learning path must exist with 7 days."""
    db = get_db()
    path = await db["learning_paths"].find_one({"slug": "asp-net-core"})
    assert path is not None, "ASP.NET Core path not found"
    assert path["duration"] == 7, f"Expected 7 days, got {path['duration']}"
    assert path["status"] == "active", f"Path status should be active, got {path['status']}"


@pytest.mark.asyncio
async def test_aspnet_all_7_blocks_published():
    """All 7 days must have published blocks."""
    db = get_db()
    blocks = []
    async for b in db["learning_blocks"].find(
        {"slug": "asp-net-core", "status": "published"}
    ).sort("day_number", 1):
        blocks.append(b)
    assert len(blocks) == 7, f"Expected 7 published blocks, got {len(blocks)}"
    days = [b["day_number"] for b in blocks]
    assert days == [1, 2, 3, 4, 5, 6, 7], f"Missing days: {set(range(1,8)) - set(days)}"


@pytest.mark.asyncio
async def test_aspnet_block_validator_passes():
    """Every published block must pass the quality validator."""
    db = get_db()
    blocks = []
    async for b in db["learning_blocks"].find(
        {"slug": "asp-net-core", "status": "published"}
    ).sort("day_number", 1):
        blocks.append(b)
    prev = None
    for b in blocks:
        passed, issues, improvements = validate_block_quality(b, b["day_number"], b.get("topic", ""), prev)
        assert passed, f"Day {b['day_number']} failed validation: {issues}"
        prev = b


@pytest.mark.asyncio
async def test_aspnet_path_coherence_passes():
    """Path-level coherence must pass."""
    db = get_db()
    path = await db["learning_paths"].find_one({"slug": "asp-net-core"})
    blocks = []
    async for b in db["learning_blocks"].find(
        {"slug": "asp-net-core", "status": "published"}
    ).sort("day_number", 1):
        blocks.append(b)
    path_ok, issues = validate_path_coherence(path, blocks)
    assert path_ok, f"Path coherence failed: {issues}"


@pytest.mark.asyncio
async def test_aspnet_no_duplicate_code():
    """No two published days should have identical code examples."""
    db = get_db()
    code_set = set()
    async for b in db["learning_blocks"].find(
        {"slug": "asp-net-core", "status": "published"}
    ).sort("day_number", 1):
        examples = b.get("examples", [])
        for ex in examples:
            code = ex.get("code", "")
            assert code not in code_set, f"Day {b['day_number']} has duplicate code example"
            code_set.add(code)


@pytest.mark.asyncio
async def test_aspnet_code_relevance():
    """Days 1-3 code must reference ASP.NET Core concepts (not pure C# console)."""
    db = get_db()
    aspnet_keywords = ["dotnet", "mvc", "project", "controller", "ef core", "sqlite",
                       "dbcontext", "migration", "program.cs", "kestrel"]
    for day in [1, 2, 3]:
        b = await db["learning_blocks"].find_one({"slug": "asp-net-core", "day_number": day})
        assert b is not None, f"Day {day} not found"
        concept = (b.get("concept_explanation") or "").lower()
        title = (b.get("title") or "").lower()
        combined = concept + " " + title
        hits = [k for k in aspnet_keywords if k in combined]
        assert len(hits) > 0, f"Day {day} has no ASP.NET Core keywords in concept/title"


@pytest.mark.asyncio
async def test_aspnet_prerequisites_trimmed():
    """Path must have 0-3 prerequisites for beginner level."""
    db = get_db()
    path = await db["learning_paths"].find_one({"slug": "asp-net-core"})
    prereqs = path.get("prerequisites", [])
    assert len(prereqs) <= 3, f"Too many prerequisites: {len(prereqs)} (aim for 0-3)"


@pytest.mark.asyncio
async def test_aspnet_each_day_has_required_fields():
    """Every published block must have all required mentor fields."""
    db = get_db()
    required_fields = [
        "learning_objective", "why_matters", "concept_explanation",
        "examples", "exercise", "homework", "challenge",
        "real_world_example", "simple_explanation", "step_by_step",
        "try_it_yourself", "common_mistakes", "quick_review",
        "questions", "what_you_can_do_now", "next_preview"
    ]
    async for b in db["learning_blocks"].find(
        {"slug": "asp-net-core", "status": "published"}
    ).sort("day_number", 1):
        for field in required_fields:
            val = b.get(field)
            assert val is not None and val != "" and val != [], \
                f"Day {b['day_number']} missing or empty: {field}"


@pytest.mark.asyncio
async def test_aspnet_no_generic_ai_phrases():
    """Concept explanations must not start with generic AI phrases."""
    db = get_db()
    banned_starts = ["Today you will learn", "In today's digital world",
                     "Welcome to", "Let's dive into"]
    async for b in db["learning_blocks"].find(
        {"slug": "asp-net-core", "status": "published"}
    ).sort("day_number", 1):
        ce = b.get("concept_explanation", "")
        for banned in banned_starts:
            assert not ce.startswith(banned), \
                f"Day {b['day_number']} concept starts with banned phrase: '{banned}'"
