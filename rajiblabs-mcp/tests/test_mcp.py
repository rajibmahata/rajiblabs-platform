"""RajibLabs MCP — Comprehensive test suite.

Tests tool registry, permissions, all tool groups, versioning, relationships, cache, and auth.
"""

from __future__ import annotations

import pytest
import pytest_asyncio
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from bson import ObjectId

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.tools import TOOL_REGISTRY, mcp_tool, _oid_str, _clean_secret_keys, _scrub_text, _normalize_skill_category, KNOWN_SKILLS
from app.permissions import (
    Permission, ROLE_PERMISSIONS, TOOL_PERMISSIONS,
    has_permission, get_role_permissions,
)
from app.versioning import (
    create_version, rollback_to_version, get_version_history,
    record_change, get_change_history, _content_hash,
)
from app.relationships import (
    add_relationship, get_relationships, remove_relationship,
    get_content_graph, sync_relationships_from_source,
)
from app.audit import audit_log, get_audit_logs, get_tool_usage_stats
from app.config import settings

# Import all tool modules to register tools
from app.tools import profile, resume, project, portfolio, product, skill, github, knowledge, content, seo


# ─── Tool Registry Tests ─────────────────────────────────────────────

class TestToolRegistry:
    def test_tools_registered(self):
        assert len(TOOL_REGISTRY) > 0

    def test_all_categories(self):
        expected = {"profile", "resume", "project", "portfolio", "product", "skill", "github", "knowledge", "content", "seo"}
        actual = {info["category"] for info in TOOL_REGISTRY.values()}
        assert expected.issubset(actual)

    def test_all_have_permissions(self):
        for name, info in TOOL_REGISTRY.items():
            assert "permission" in info, f"{name} missing permission"
            assert info["permission"] in [p.value for p in Permission]

    def test_tool_count(self):
        assert len(TOOL_REGISTRY) >= 70

    def test_profile_tools_exist(self):
        profile_tools = [n for n, i in TOOL_REGISTRY.items() if i["category"] == "profile"]
        assert "get_profile" in profile_tools
        assert "analyze_profile" in profile_tools
        assert "validate_profile" in profile_tools
        assert "optimize_profile" in profile_tools
        assert "get_professional_positioning" in profile_tools

    def test_resume_tools_exist(self):
        resume_tools = [n for n, i in TOOL_REGISTRY.items() if i["category"] == "resume"]
        assert "list_resumes" in resume_tools
        assert "get_resume" in resume_tools
        assert "analyze_resume" in resume_tools
        assert "extract_resume_skills" in resume_tools

    def test_project_tools_exist(self):
        project_tools = [n for n, i in TOOL_REGISTRY.items() if i["category"] == "project"]
        assert "list_projects" in project_tools
        assert "get_project" in project_tools
        assert "analyze_project" in project_tools
        assert "improve_project" in project_tools
        assert "update_project" in project_tools

    def test_portfolio_tools_exist(self):
        portfolio_tools = [n for n, i in TOOL_REGISTRY.items() if i["category"] == "portfolio"]
        assert "get_portfolio" in portfolio_tools
        assert "analyze_portfolio" in portfolio_tools
        assert "rank_projects" in portfolio_tools

    def test_product_tools_exist(self):
        product_tools = [n for n, i in TOOL_REGISTRY.items() if i["category"] == "product"]
        assert "list_products" in product_tools
        assert "get_product" in product_tools

    def test_skill_tools_exist(self):
        skill_tools = [n for n, i in TOOL_REGISTRY.items() if i["category"] == "skill"]
        assert "discover_skills" in skill_tools
        assert "validate_skill" in skill_tools
        assert "normalize_skill" in skill_tools

    def test_github_tools_exist(self):
        github_tools = [n for n, i in TOOL_REGISTRY.items() if i["category"] == "github"]
        assert "list_repositories" in github_tools
        assert "analyze_repository" in github_tools

    def test_knowledge_tools_exist(self):
        knowledge_tools = [n for n, i in TOOL_REGISTRY.items() if i["category"] == "knowledge"]
        assert "search_knowledge" in knowledge_tools
        assert "validate_knowledge" in knowledge_tools

    def test_content_tools_exist(self):
        content_tools = [n for n, i in TOOL_REGISTRY.items() if i["category"] == "content"]
        assert "analyze_content" in content_tools
        assert "validate_content" in content_tools
        assert "detect_conflicts" in content_tools

    def test_seo_tools_exist(self):
        seo_tools = [n for n, i in TOOL_REGISTRY.items() if i["category"] == "seo"]
        assert "analyze_seo" in seo_tools
        assert "validate_metadata" in seo_tools


# ─── Permission Tests ────────────────────────────────────────────────

class TestPermissions:
    def test_all_roles_defined(self):
        assert "public_agent" in ROLE_PERMISSIONS
        assert "profile_manager" in ROLE_PERMISSIONS
        assert "admin" in ROLE_PERMISSIONS

    def test_public_read_only(self):
        perms = ROLE_PERMISSIONS["public_agent"]
        assert Permission.READ in perms
        assert Permission.WRITE not in perms
        assert Permission.DELETE not in perms

    def test_admin_full_access(self):
        perms = ROLE_PERMISSIONS["admin"]
        assert Permission.READ in perms
        assert Permission.ANALYZE in perms
        assert Permission.WRITE in perms
        assert Permission.PUBLISH in perms
        assert Permission.DELETE in perms

    def test_profile_manager_can_write(self):
        perms = ROLE_PERMISSIONS["profile_manager"]
        assert Permission.WRITE in perms
        assert Permission.PUBLISH in perms

    def test_has_permission_admin(self):
        assert has_permission("admin", "update_project")
        assert has_permission("admin", "rollback_content")
        assert has_permission("admin", "sync_repository")

    def test_has_permission_public_agent(self):
        assert has_permission("public_agent", "get_profile")
        assert has_permission("public_agent", "list_projects")
        assert not has_permission("public_agent", "update_project")

    def test_has_permission_profile_manager(self):
        assert has_permission("profile_manager", "update_profile")
        assert has_permission("profile_manager", "get_profile")
        assert not has_permission("profile_manager", "rollback_content")

    def test_tool_permissions_all_tools(self):
        for tool_name in TOOL_REGISTRY:
            assert tool_name in TOOL_PERMISSIONS, f"{tool_name} not in TOOL_PERMISSIONS"


# ─── Helper Tests ────────────────────────────────────────────────────

class TestHelpers:
    def test_oid_strObjectId(self):
        oid = ObjectId()
        assert _oid_str(oid) == str(oid)

    def test_oid_str_string(self):
        assert _oid_str("abc123") == "abc123"

    def test_oid_str_none(self):
        assert _oid_str(None) is None

    def test_clean_secret_keys(self):
        data = {"name": "Rajib", "password": "secret123", "api_key": "key123", "title": "Dev"}
        cleaned = _clean_secret_keys(data)
        assert cleaned["name"] == "Rajib"
        assert cleaned["password"] == "***"
        assert cleaned["api_key"] == "***"
        assert cleaned["title"] == "Dev"

    def test_scrub_text(self):
        text = "password=secret123 api_key=mykey"
        scrubbed = _scrub_text(text)
        assert "secret123" not in scrubbed
        assert "mykey" not in scrubbed

    def test_normalize_skill_category(self):
        assert _normalize_skill_category("frontend") == "frontend"
        assert _normalize_skill_category("Front-End") == "frontend"
        assert _normalize_skill_category("fullstack") == "fullstack"
        assert _normalize_skill_category("devops") == "devops"
        assert _normalize_skill_category("unknown") == "other"

    def test_known_skills_populated(self):
        assert len(KNOWN_SKILLS) > 50
        assert "python" in KNOWN_SKILLS
        assert "react" in KNOWN_SKILLS
        assert "docker" in KNOWN_SKILLS


# ─── Versioning Tests ────────────────────────────────────────────────

class TestVersioning:
    def test_content_hash_deterministic(self):
        data = {"key": "value", "number": 42}
        h1 = _content_hash(data)
        h2 = _content_hash(data)
        assert h1 == h2

    def test_content_hash_different(self):
        h1 = _content_hash({"a": 1})
        h2 = _content_hash({"b": 2})
        assert h1 != h2


# ─── MCP Tool Decorator Tests ───────────────────────────────────────

class TestMCPToolDecorator:
    def test_decorator_registers_tool(self):
        @mcp_tool(
            name="test_tool_999",
            description="Test tool",
            category="test",
            permission="read",
        )
        async def test_fn(agent_id: str = "anonymous"):
            return {"success": True, "data": {}}

        assert "test_tool_999" in TOOL_REGISTRY
        assert TOOL_REGISTRY["test_tool_999"]["description"] == "Test tool"
        assert TOOL_REGISTRY["test_tool_999"]["category"] == "test"
        assert TOOL_REGISTRY["test_tool_999"]["permission"] == "read"

    def test_decorator_sets_metadata(self):
        @mcp_tool(
            name="test_tool_998",
            description="Test tool 2",
            category="test",
            permission="write",
            timeout=60.0,
            idempotent=False,
        )
        async def test_fn(agent_id: str = "anonymous"):
            return {"success": True, "data": {}}

        assert test_fn._mcp_tool_name == "test_tool_998"
        assert test_fn._mcp_tool_timeout == 60.0
        assert test_fn._mcp_tool_idempotent is False


# ─── Config Tests ────────────────────────────────────────────────────

class TestConfig:
    def test_settings_load(self):
        assert settings.MCP_PORT == 8100
        assert settings.CACHE_TTL_SECONDS == 300
        assert settings.MONGO_DB_NAME == "rajiblabs"
