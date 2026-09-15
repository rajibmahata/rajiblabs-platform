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


# ── Additional unit tests ──

def test_mcp_tool_registry_count():
    """Verify all expected tool modules can be imported."""
    import app.tools.profile
    import app.tools.project
    import app.tools.skill
    import app.tools.github
    import app.tools.knowledge
    import app.tools.seo
    import app.tools.content

    import inspect
    count = 0
    for module in [app.tools.profile, app.tools.project, app.tools.skill,
                   app.tools.github, app.tools.knowledge, app.tools.seo,
                   app.tools.content]:
        for name, obj in inspect.getmembers(module, inspect.iscoroutinefunction):
            if hasattr(obj, "_mcp_tool_name"):
                count += 1
    assert count >= 30, f"Expected at least 30 tools, got {count}"


def test_tool_categories():
    """Verify tools are assigned to correct categories."""
    import app.tools.profile
    import app.tools.project
    import app.tools.skill
    import app.tools.github
    import app.tools.knowledge
    import app.tools.seo
    import app.tools.content

    import inspect
    categories = set()
    for module in [app.tools.profile, app.tools.project, app.tools.skill,
                   app.tools.github, app.tools.knowledge, app.tools.seo,
                   app.tools.content]:
        for name, obj in inspect.getmembers(module, inspect.iscoroutinefunction):
            if hasattr(obj, "_mcp_tool_name"):
                categories.add(obj._mcp_category)

    expected = {"profile", "project", "skill", "github", "knowledge", "seo", "content"}
    assert expected.issubset(categories), f"Missing categories: {expected - categories}"


def test_tool_permissions():
    """Verify tools have proper permission levels."""
    import app.tools.profile
    import app.tools.project
    import app.tools.skill
    import app.tools.github
    import app.tools.knowledge
    import app.tools.seo
    import app.tools.content

    import inspect
    for module in [app.tools.profile, app.tools.project, app.tools.skill,
                   app.tools.github, app.tools.knowledge, app.tools.seo,
                   app.tools.content]:
        for name, obj in inspect.getmembers(module, inspect.iscoroutinefunction):
            if hasattr(obj, "_mcp_tool_name"):
                perm = obj._mcp_permission
                assert perm in ("public", "agent", "admin"), \
                    f"Tool {obj._mcp_tool_name} has invalid permission: {perm}"


def test_admin_tools_require_admin():
    """Verify sensitive tools are marked as admin-only."""
    import app.tools.github
    import app.tools.knowledge
    import app.tools.content

    # sync_repository should be admin
    assert app.tools.github.sync_repository._mcp_permission == "admin"
    # index_knowledge should be admin
    assert app.tools.knowledge.index_knowledge._mcp_permission == "admin"
    # rollback_content should be admin
    assert app.tools.content.rollback_content._mcp_permission == "admin"


def test_public_tools_are_public():
    """Verify read-only tools are marked as public."""
    import app.tools.profile
    import app.tools.project
    import app.tools.skill
    import app.tools.github
    import app.tools.knowledge

    assert app.tools.profile.get_profile._mcp_permission == "public"
    assert app.tools.project.get_projects._mcp_permission == "public"
    assert app.tools.project.get_portfolio._mcp_permission == "public"
    assert app.tools.skill.get_skills._mcp_permission == "public"
    assert app.tools.github.get_repositories._mcp_permission == "public"
    assert app.tools.knowledge.search_knowledge._mcp_permission == "public"


def test_auth_dev_mode():
    """Verify auth allows dev mode when no keys configured."""
    import os
    os.environ["MCP_APP_ENV"] = "development"
    os.environ["MCP_MCP_API_KEY"] = ""
    os.environ["MCP_ADMIN_API_KEY"] = ""

    from app.config import MCPSettings
    settings = MCPSettings()
    assert settings.app_env == "development"
    assert settings.mcp_api_key == ""

    # Clean up
    os.environ.pop("MCP_APP_ENV", None)
    os.environ.pop("MCP_MCP_API_KEY", None)
    os.environ.pop("MCP_ADMIN_API_KEY", None)


def test_skill_evidence_model():
    """Verify SkillEvidence model validates correctly."""
    from app.models import SkillEvidence

    skill = SkillEvidence(
        skill="Python",
        category="Backend",
        confidence=0.95,
        evidence=["resume", "project:MyApp"],
        related_projects=["MyApp"],
        related_repositories=["my-app"],
    )
    assert skill.skill == "Python"
    assert skill.confidence == 0.95
    assert len(skill.evidence) == 2


def test_content_version_model():
    """Verify ContentVersion model validates correctly."""
    from app.models import ContentVersion

    version = ContentVersion(
        entity_type="project",
        entity_id="123abc",
        version=2,
        previous_content={"title": "Old Title"},
        new_content={"title": "New Title"},
        reason="Updated title",
        agent="profile_manager",
        mcp_tool="improve_project",
    )
    assert version.version == 2
    assert version.reason == "Updated title"


def test_portfolio_ranking_model():
    """Verify PortfolioRanking model validates correctly."""
    from app.models import PortfolioRanking

    ranking = PortfolioRanking(
        project_id="abc123",
        technical_depth=0.85,
        business_value=0.7,
        ai_capability=0.9,
        total_score=0.82,
    )
    assert ranking.technical_depth == 0.85
    assert ranking.total_score == 0.82


def test_seo_metadata_model():
    """Verify SEOMetadata model validates correctly."""
    from app.models import SEOMetadata

    meta = SEOMetadata(
        title="My Project | RajibLabs",
        description="A brief description",
        keywords=["Python", "FastAPI"],
        schema_type="SoftwareApplication",
    )
    assert meta.title == "My Project | RajibLabs"
    assert len(meta.keywords) == 2


def test_content_health_model():
    """Verify ContentHealth model validates correctly."""
    from app.models import ContentHealth

    health = ContentHealth(
        entity_type="project",
        entity_id="xyz",
        completeness=0.85,
        freshness=0.9,
        overall_score=0.87,
        issues=["Missing images"],
        recommendations=["Add screenshots"],
    )
    assert health.completeness == 0.85
    assert len(health.issues) == 1


# ── Live tests for additional tools ──

@pytest.mark.asyncio
async def test_profile_validate_live():
    """Test profile validation."""
    from app.tools.profile import validate_profile
    db = await _live_db()
    result = await validate_profile()
    assert isinstance(result, dict)
    assert "valid" in result


@pytest.mark.asyncio
async def test_profile_optimize_live():
    """Test profile optimization suggestions."""
    from app.tools.profile import optimize_profile
    db = await _live_db()
    result = await optimize_profile()
    assert isinstance(result, dict)
    assert "optimizations" in result


@pytest.mark.asyncio
async def test_profile_positioning_live():
    """Test professional positioning."""
    from app.tools.profile import get_professional_positioning
    db = await _live_db()
    result = await get_professional_positioning()
    assert isinstance(result, dict)
    assert "positioning_claims" in result


@pytest.mark.asyncio
async def test_knowledge_validate_live():
    """Test knowledge validation."""
    from app.tools.knowledge import validate_knowledge
    db = await _live_db()
    result = await validate_knowledge()
    assert isinstance(result, dict)
    assert "total_entries" in result


@pytest.mark.asyncio
async def test_knowledge_stale_live():
    """Test stale knowledge detection."""
    from app.tools.knowledge import detect_stale_knowledge
    db = await _live_db()
    result = await detect_stale_knowledge()
    assert isinstance(result, dict)
    assert "stale_count" in result


@pytest.mark.asyncio
async def test_content_freshness_live():
    """Test content freshness analysis."""
    from app.tools.content import get_content_freshness
    db = await _live_db()
    result = await get_content_freshness()
    assert isinstance(result, dict)
    assert "fresh" in result
    assert "aging" in result
    assert "stale" in result


@pytest.mark.asyncio
async def test_seo_missing_metadata_live():
    """Test SEO missing metadata detection."""
    from app.tools.seo import find_missing_metadata
    db = await _live_db()
    result = await find_missing_metadata()
    assert isinstance(result, dict)
    assert "count" in result


@pytest.mark.asyncio
async def test_seo_content_quality_live():
    """Test SEO content quality analysis."""
    from app.tools.seo import analyze_content_quality
    db = await _live_db()
    result = await analyze_content_quality()
    assert isinstance(result, dict)
    assert "average_quality_score" in result


@pytest.mark.asyncio
async def test_portfolio_analyze_live():
    """Test portfolio analysis."""
    from app.tools.project import analyze_portfolio
    db = await _live_db()
    result = await analyze_portfolio()
    assert isinstance(result, dict)
    assert "total_portfolio_projects" in result
