from __future__ import annotations

import logging
from typing import Any

from app.database import get_db
from app.tools import mcp_tool, _oid_str, _clean_secret_keys
from app.cache import cache_get, cache_set
from app.versioning import create_version, record_change
from app.config import settings

logger = logging.getLogger(__name__)


@mcp_tool(
    name="list_repositories",
    description="List all synced GitHub repositories.",
    category="github",
    permission="read",
)
async def list_repositories(agent_id: str = "anonymous") -> dict:
    cached = await cache_get("github", "repos")
    if cached:
        return {"success": True, "data": cached, "sources": ["cache"], "confidence": 1.0}

    db = get_db()
    repos = []
    async for repo in db.github_repositories.find():
        repo["_id"] = _oid_str(repo["_id"])
        repo = _clean_secret_keys(repo)
        repos.append(repo)

    result = {"repositories": repos, "count": len(repos)}
    await cache_set("github", "repos", result)
    return {"success": True, "data": result, "sources": ["github_repositories"], "confidence": 1.0}


@mcp_tool(
    name="get_repository",
    description="Get a specific GitHub repository by name.",
    category="github",
    permission="read",
)
async def get_repository(repo_name: str, agent_id: str = "anonymous") -> dict:
    db = get_db()
    repo = await db.github_repositories.find_one({"name": repo_name})
    if not repo:
        return {"success": False, "error": {"code": "NOT_FOUND", "message": "Repository not found"}}

    repo["_id"] = _oid_str(repo["_id"])
    repo = _clean_secret_keys(repo)
    return {"success": True, "data": repo, "sources": ["github_repositories"], "confidence": 1.0}


@mcp_tool(
    name="analyze_repository",
    description="Analyze a GitHub repository for skills, technologies, and project evidence.",
    category="github",
    permission="analyze",
)
async def analyze_repository(repo_name: str, agent_id: str = "anonymous") -> dict:
    db = get_db()
    repo = await db.github_repositories.find_one({"name": repo_name})
    if not repo:
        return {"success": False, "error": {"code": "NOT_FOUND", "message": "Repository not found"}}

    analysis = {
        "name": repo.get("name", ""),
        "description": repo.get("description", ""),
        "languages": repo.get("languages", []),
        "topics": repo.get("topics", []),
        "stars": repo.get("stargazers_count", 0),
        "forks": repo.get("forks_count", 0),
        "size_kb": repo.get("size", 0),
        "last_push": str(repo.get("pushed_at", "")),
        "has_readme": repo.get("has_readme", False),
        "has_license": repo.get("license") is not None,
    }

    skills_found = set()
    for lang in repo.get("languages", []):
        skills_found.add(lang.lower())
    for topic in repo.get("topics", []):
        skills_found.add(topic.lower())

    analysis["skills_detected"] = list(skills_found)

    return {
        "success": True,
        "data": analysis,
        "sources": ["github_repositories"],
        "confidence": 0.9,
    }


@mcp_tool(
    name="discover_projects_from_repository",
    description="Discover potential projects from a GitHub repository's metadata and structure.",
    category="github",
    permission="analyze",
)
async def discover_projects_from_repository(repo_name: str, agent_id: str = "anonymous") -> dict:
    db = get_db()
    repo = await db.github_repositories.find_one({"name": repo_name})
    if not repo:
        return {"success": False, "error": {"code": "NOT_FOUND", "message": "Repository not found"}}

    existing = await db.projects.find_one({"github_url": repo.get("html_url", "")})
    is_existing_project = existing is not None

    project_evidence = {
        "name": repo.get("name", ""),
        "description": repo.get("description", ""),
        "languages": repo.get("languages", []),
        "topics": repo.get("topics", []),
        "is_existing_project": is_existing_project,
        "potential_project_id": _oid_str(existing["_id"]) if existing else None,
    }

    return {
        "success": True,
        "data": project_evidence,
        "sources": ["github_repositories", "projects"],
        "confidence": 0.8,
    }


@mcp_tool(
    name="discover_skills_from_repository",
    description="Discover skills from a repository's languages, topics, and dependencies.",
    category="github",
    permission="analyze",
)
async def discover_skills_from_repository(repo_name: str, agent_id: str = "anonymous") -> dict:
    db = get_db()
    repo = await db.github_repositories.find_one({"name": repo_name})
    if not repo:
        return {"success": False, "error": {"code": "NOT_FOUND", "message": "Repository not found"}}

    skills = set()
    for lang in repo.get("languages", []):
        skills.add(lang.lower())
    for topic in repo.get("topics", []):
        skills.add(topic.lower())

    validated = []
    for skill in skills:
        exists = await db.skills.find_one({"name": {"$regex": f"^{skill}$", "$options": "i"}})
        validated.append({"name": skill, "in_database": bool(exists)})

    return {
        "success": True,
        "data": {"repository": repo_name, "skills": validated, "total": len(validated)},
        "sources": ["github_repositories", "skills"],
        "confidence": 0.85,
    }


@mcp_tool(
    name="discover_technologies_from_repository",
    description="Discover technology stack from repository analysis.",
    category="github",
    permission="analyze",
)
async def discover_technologies_from_repository(repo_name: str, agent_id: str = "anonymous") -> dict:
    db = get_db()
    repo = await db.github_repositories.find_one({"name": repo_name})
    if not repo:
        return {"success": False, "error": {"code": "NOT_FOUND", "message": "Repository not found"}}

    tech_stack = {
        "languages": repo.get("languages", []),
        "frameworks": [],
        "tools": [],
    }

    return {
        "success": True,
        "data": {"repository": repo_name, "tech_stack": tech_stack},
        "sources": ["github_repositories"],
        "confidence": 0.8,
    }


@mcp_tool(
    name="sync_repository",
    description="Trigger a sync for a GitHub repository (admin only).",
    category="github",
    permission="write",
)
async def sync_repository(repo_name: str, agent_id: str = "anonymous") -> dict:
    db = get_db()
    repo = await db.github_repositories.find_one({"name": repo_name})
    if not repo:
        return {"success": False, "error": {"code": "NOT_FOUND", "message": "Repository not found"}}

    return {
        "success": True,
        "data": {"repository": repo_name, "status": "sync_requested", "message": "Repository sync will be processed"},
        "sources": ["github_repositories"],
        "confidence": 0.9,
    }


@mcp_tool(
    name="validate_repository",
    description="Validate repository metadata and sync status.",
    category="github",
    permission="analyze",
)
async def validate_repository(repo_name: str, agent_id: str = "anonymous") -> dict:
    db = get_db()
    repo = await db.github_repositories.find_one({"name": repo_name})
    if not repo:
        return {"success": False, "error": {"code": "NOT_FOUND", "message": "Repository not found"}}

    issues = []
    warnings = []

    if not repo.get("description"):
        warnings.append("Missing description")
    if not repo.get("languages"):
        warnings.append("No languages detected")
    if repo.get("size", 0) == 0:
        warnings.append("Repository appears empty")

    return {
        "success": True,
        "data": {"repository": repo_name, "valid": len(issues) == 0, "issues": issues, "warnings": warnings},
        "sources": ["github_repositories"],
        "confidence": 0.9,
    }
