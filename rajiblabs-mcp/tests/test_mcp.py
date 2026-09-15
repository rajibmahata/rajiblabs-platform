"""MCP tests — unit tests for all MCP tools."""

import pytest


def test_mcp_tool_decorator():
    """Verify MCP tool decorator registers metadata."""
    from app.tools import mcp_tool

    @mcp_tool("test_tool", "A test tool", "content", permission="public")
    async def test_tool():
        return {"ok": True}

    assert test_tool._mcp_tool_name == "test_tool"
    assert test_tool._mcp_description == "A test tool"
    assert test_tool._mcp_category == "content"
    assert test_tool._mcp_permission == "public"


def test_oid_str():
    """Verify MongoDB _id to string conversion."""
    from app.tools import _oid_str
    from bson import ObjectId

    oid = ObjectId()
    result = _oid_str({"_id": oid, "name": "test"})
    assert result["id"] == str(oid)
    assert "_id" not in result
    assert result["name"] == "test"


def test_clean_secret_keys():
    """Verify secret keys are removed from output."""
    from app.tools import _clean_secret_keys

    data = {
        "name": "test",
        "password": "secret123",
        "api_key": "key123",
        "nested": {"token": "abc", "value": "safe"},
        "list": [{"secret": "x"}, {"safe": "y"}],
    }
    cleaned = _clean_secret_keys(data)
    assert cleaned["name"] == "test"
    assert "password" not in cleaned
    assert "api_key" not in cleaned
    assert "token" not in cleaned["nested"]
    assert cleaned["nested"]["value"] == "safe"
    assert "secret" not in cleaned["list"][0]
    assert cleaned["list"][1]["safe"] == "y"


def test_normalize_skill_category():
    """Verify skill category normalization."""
    from app.tools import _normalize_skill_category

    assert _normalize_skill_category("backend") == "Backend"
    assert _normalize_skill_category("ai/ml") == "AI / ML"
    assert _normalize_skill_category("databases") == "Databases"
    assert _normalize_skill_category("cloud") == "Cloud"
    assert _normalize_skill_category("custom") == "Custom"


def test_known_skills_has_entries():
    """Verify KNOWN_SKILLS database is populated."""
    from app.tools import KNOWN_SKILLS

    assert len(KNOWN_SKILLS) > 20
    assert "python" in KNOWN_SKILLS
    assert ".net" in KNOWN_SKILLS
    assert "azure" in KNOWN_SKILLS
    assert "react" in KNOWN_SKILLS
    assert "mongodb" in KNOWN_SKILLS


def test_config_loads():
    """Verify MCP settings load from environment."""
    from app.config import settings

    assert settings.app_name == "rajiblabs-mcp"
    assert settings.mcp_port == 8100


def test_models_validate():
    """Verify Pydantic models validate correctly."""
    from app.models import (
        ToolDefinition, ToolCategory, ToolPermission,
        SkillEvidence, PortfolioRanking, SEOMetadata, ContentHealth,
    )

    tool = ToolDefinition(
        name="test", description="test tool",
        category=ToolCategory.PROFILE)
    assert tool.name == "test"
    assert tool.permission == ToolPermission.AGENT

    skill = SkillEvidence(skill="Python", category="Backend", confidence=0.9)
    assert skill.confidence == 0.9

    ranking = PortfolioRanking(project_id="123", technical_depth=0.8)
    assert ranking.technical_depth == 0.8

    seo = SEOMetadata(title="Test Page", description="A test page")
    assert seo.title == "Test Page"

    health = ContentHealth(entity_type="project", entity_id="123")
    assert health.completeness == 0.0


# ── Live tests (require MongoDB) ──

async def _live_db():
    try:
        from app.database import get_db
        db = get_db()
        await db.command("ping")
        return db
    except Exception:
        pytest.skip("MongoDB not running locally")


@pytest.mark.asyncio
async def test_profile_get_live():
    """Test profile retrieval from database."""
    from app.tools.profile import get_profile
    db = await _live_db()
    result = await get_profile()
    # May return error if no profile exists, but shouldn't crash
    assert isinstance(result, dict)


@pytest.mark.asyncio
async def test_profile_analyze_live():
    """Test profile analysis."""
    from app.tools.profile import analyze_profile
    db = await _live_db()
    result = await analyze_profile()
    assert isinstance(result, dict)
    assert "completeness" in result


@pytest.mark.asyncio
async def test_projects_list_live():
    """Test project listing."""
    from app.tools.project import get_projects
    db = await _live_db()
    result = await get_projects()
    assert isinstance(result, dict)
    assert "projects" in result
    assert "count" in result


@pytest.mark.asyncio
async def test_skills_list_live():
    """Test skill listing."""
    from app.tools.skill import get_skills
    db = await _live_db()
    result = await get_skills()
    assert isinstance(result, dict)
    assert "skills" in result


@pytest.mark.asyncio
async def test_github_repos_live():
    """Test GitHub repository listing."""
    from app.tools.github import get_repositories
    db = await _live_db()
    result = await get_repositories()
    assert isinstance(result, dict)
    assert "repositories" in result


@pytest.mark.asyncio
async def test_knowledge_search_live():
    """Test knowledge search."""
    from app.tools.knowledge import search_knowledge
    db = await _live_db()
    result = await search_knowledge(query="test")
    assert isinstance(result, dict)
    assert "results" in result


@pytest.mark.asyncio
async def test_content_health_live():
    """Test content health calculation."""
    from app.tools.content import get_content_health
    db = await _live_db()
    result = await get_content_health()
    assert isinstance(result, dict)
    assert "profile" in result


@pytest.mark.asyncio
async def test_seo_analyze_live():
    """Test SEO analysis."""
    from app.tools.seo import analyze_seo
    db = await _live_db()
    result = await analyze_seo()
    assert isinstance(result, dict)
    assert "pages_analyzed" in result


@pytest.mark.asyncio
async def test_portfolio_get_live():
    """Test portfolio retrieval."""
    from app.tools.project import get_portfolio
    db = await _live_db()
    result = await get_portfolio()
    assert isinstance(result, dict)
    assert "portfolio" in result


@pytest.mark.asyncio
async def test_skills_extract_live():
    """Test skill extraction from all sources."""
    from app.tools.skill import extract_skills
    db = await _live_db()
    result = await extract_skills()
    assert isinstance(result, dict)
    assert "total_extracted" in result
    assert "sources_used" in result


@pytest.mark.asyncio
async def test_organize_projects_live():
    """Test project organization."""
    from app.tools.project import organize_projects
    db = await _live_db()
    result = await organize_projects()
    assert isinstance(result, dict)
    assert "categories" in result


@pytest.mark.asyncio
async def test_rank_projects_live():
    """Test project ranking."""
    from app.tools.project import rank_projects
    db = await _live_db()
    result = await rank_projects()
    assert isinstance(result, dict)
    assert "rankings" in result
