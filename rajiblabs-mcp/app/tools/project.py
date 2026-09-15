from __future__ import annotations

import logging
from typing import Any

from app.database import get_db
from app.tools import mcp_tool, _oid_str, _clean_secret_keys, _scrub_text
from app.cache import cache_get, cache_set, cache_invalidate
from app.versioning import create_version, record_change
from app.relationships import add_relationship, get_relationships, sync_relationships_from_source

logger = logging.getLogger(__name__)


@mcp_tool(
    name="list_projects",
    description="List all published projects with optional filtering.",
    category="project",
    permission="read",
)
async def list_projects(
    status: str = "published", limit: int = 50, agent_id: str = "anonymous"
) -> dict:
    cache_key = f"list:{status}:{limit}"
    cached = await cache_get("projects", cache_key)
    if cached:
        return {"success": True, "data": cached, "sources": ["cache"], "confidence": 1.0}

    db = get_db()
    query = {}
    if status != "all":
        query["status"] = status

    projects = []
    async for proj in db.projects.find(query).limit(limit):
        proj["_id"] = _oid_str(proj["_id"])
        proj = _clean_secret_keys(proj)
        projects.append(proj)

    result = {"projects": projects, "count": len(projects)}
    await cache_set("projects", cache_key, result)
    return {"success": True, "data": result, "sources": ["projects"], "confidence": 1.0}


@mcp_tool(
    name="get_project",
    description="Get a specific project by ID with full details.",
    category="project",
    permission="read",
)
async def get_project(project_id: str, agent_id: str = "anonymous") -> dict:
    cached = await cache_get("projects", f"get:{project_id}")
    if cached:
        return {"success": True, "data": cached, "sources": ["cache"], "confidence": 1.0}

    db = get_db()
    from bson import ObjectId
    project = await db.projects.find_one({"_id": ObjectId(project_id)})
    if not project:
        return {"success": False, "error": {"code": "NOT_FOUND", "message": "Project not found"}}

    project["_id"] = _oid_str(project["_id"])
    project = _clean_secret_keys(project)

    relationships = await get_relationships("project", project_id)
    project["_relationships"] = relationships

    await cache_set("projects", f"get:{project_id}", project)
    return {"success": True, "data": project, "sources": ["projects"], "confidence": 1.0}


@mcp_tool(
    name="analyze_project",
    description="Analyze a project for quality, completeness, and improvement opportunities.",
    category="project",
    permission="analyze",
)
async def analyze_project(project_id: str, agent_id: str = "anonymous") -> dict:
    db = get_db()
    from bson import ObjectId
    project = await db.projects.find_one({"_id": ObjectId(project_id)})
    if not project:
        return {"success": False, "error": {"code": "NOT_FOUND", "message": "Project not found"}}

    required_fields = ["title", "description", "problem", "solution", "features", "tech_stack", "architecture"]
    optional_fields = ["github_url", "live_url", "video_url", "images", "skills", "domains", "role", "business_value", "challenges", "outcomes"]

    filled_required = sum(1 for f in required_fields if project.get(f))
    filled_optional = sum(1 for f in optional_fields if project.get(f))

    required_score = (filled_required / len(required_fields)) * 70 if required_fields else 0
    optional_score = (filled_optional / len(optional_fields)) * 30 if optional_fields else 0
    score = round(required_score + optional_score, 1)

    missing = [{"field": f, "severity": "high"} for f in required_fields if not project.get(f)]
    missing += [{"field": f, "severity": "medium"} for f in optional_fields if not project.get(f)]

    return {
        "success": True,
        "data": {
            "project_id": project_id,
            "title": project.get("title", ""),
            "score": score,
            "completeness": round(score, 1),
            "required_filled": filled_required,
            "required_total": len(required_fields),
            "optional_filled": filled_optional,
            "optional_total": len(optional_fields),
            "missing_fields": missing,
        },
        "sources": ["projects"],
        "confidence": 0.95,
    }


@mcp_tool(
    name="improve_project",
    description="Generate improvement suggestions for a project based on completeness and quality.",
    category="project",
    permission="propose",
)
async def improve_project(project_id: str, agent_id: str = "anonymous") -> dict:
    db = get_db()
    from bson import ObjectId
    project = await db.projects.find_one({"_id": ObjectId(project_id)})
    if not project:
        return {"success": False, "error": {"code": "NOT_FOUND", "message": "Project not found"}}

    suggestions = []

    if not project.get("problem"):
        suggestions.append({
            "field": "problem",
            "priority": "high",
            "suggestion": "Describe the problem this project solves. Include context about why it matters.",
        })
    if not project.get("solution"):
        suggestions.append({
            "field": "solution",
            "priority": "high",
            "suggestion": "Describe the technical solution. Focus on architecture and key decisions.",
        })
    if not project.get("role"):
        suggestions.append({
            "field": "role",
            "priority": "medium",
            "suggestion": "Specify your role and contributions to this project.",
        })
    if not project.get("business_value"):
        suggestions.append({
            "field": "business_value",
            "priority": "medium",
            "suggestion": "Describe the business impact or value delivered.",
        })
    if not project.get("challenges"):
        suggestions.append({
            "field": "challenges",
            "priority": "low",
            "suggestion": "Document technical challenges overcome during implementation.",
        })
    if not project.get("github_url"):
        suggestions.append({
            "field": "github_url",
            "priority": "low",
            "suggestion": "Add GitHub repository link for code evidence.",
        })
    if not project.get("skills"):
        suggestions.append({
            "field": "skills",
            "priority": "high",
            "suggestion": "Tag this project with relevant skills for better discoverability.",
        })

    return {
        "success": True,
        "data": {
            "project_id": project_id,
            "title": project.get("title", ""),
            "suggestions": suggestions,
            "total_suggestions": len(suggestions),
        },
        "sources": ["projects"],
        "confidence": 0.85,
    }


@mcp_tool(
    name="validate_project",
    description="Validate a project for factual accuracy and completeness.",
    category="project",
    permission="analyze",
)
async def validate_project(project_id: str, agent_id: str = "anonymous") -> dict:
    db = get_db()
    from bson import ObjectId
    project = await db.projects.find_one({"_id": ObjectId(project_id)})
    if not project:
        return {"success": False, "error": {"code": "NOT_FOUND", "message": "Project not found"}}

    issues = []
    warnings = []

    if project.get("skills"):
        for skill_name in project["skills"]:
            skill = await db.skills.find_one({"name": {"$regex": f"^{skill_name}$", "$options": "i"}})
            if not skill:
                warnings.append({"field": "skills", "message": f"Skill '{skill_name}' not in skills database"})

    if project.get("github_url"):
        repo = await db.github_repositories.find_one({"html_url": project["github_url"]})
        if not repo:
            warnings.append({"field": "github_url", "message": "GitHub repository not found in synced repos"})

    score = 100.0
    if issues:
        score -= len(issues) * 15
    if warnings:
        score -= len(warnings) * 5
    score = max(0, score)

    return {
        "success": True,
        "data": {
            "project_id": project_id,
            "valid": len(issues) == 0,
            "score": round(score, 1),
            "issues": issues,
            "warnings": warnings,
        },
        "sources": ["projects", "skills", "github_repositories"],
        "confidence": 0.9,
    }


@mcp_tool(
    name="detect_project_gaps",
    description="Detect gaps and missing information across all projects.",
    category="project",
    permission="analyze",
)
async def detect_project_gaps(agent_id: str = "anonymous") -> dict:
    db = get_db()
    gaps = {"critical": [], "important": [], "minor": []}

    async for proj in db.projects.find({"status": "published"}):
        proj_id = _oid_str(proj["_id"])
        title = proj.get("title", "Unknown")

        if not proj.get("description"):
            gaps["critical"].append({"project": title, "id": proj_id, "field": "description"})
        if not proj.get("problem"):
            gaps["critical"].append({"project": title, "id": proj_id, "field": "problem"})
        if not proj.get("solution"):
            gaps["critical"].append({"project": title, "id": proj_id, "field": "solution"})
        if not proj.get("skills"):
            gaps["important"].append({"project": title, "id": proj_id, "field": "skills"})
        if not proj.get("github_url"):
            gaps["important"].append({"project": title, "id": proj_id, "field": "github_url"})
        if not proj.get("role"):
            gaps["minor"].append({"project": title, "id": proj_id, "field": "role"})
        if not proj.get("images"):
            gaps["minor"].append({"project": title, "id": proj_id, "field": "images"})

    return {
        "success": True,
        "data": {
            "gaps": gaps,
            "total_critical": len(gaps["critical"]),
            "total_important": len(gaps["important"]),
            "total_minor": len(gaps["minor"]),
        },
        "sources": ["projects"],
        "confidence": 0.95,
    }


@mcp_tool(
    name="discover_project_relationships",
    description="Discover and create relationships between a project and skills, repos, domains.",
    category="project",
    permission="analyze",
)
async def discover_project_relationships(project_id: str, agent_id: str = "anonymous") -> dict:
    count = await sync_relationships_from_source("project", project_id)
    relationships = await get_relationships("project", project_id)

    return {
        "success": True,
        "data": {
            "project_id": project_id,
            "new_relationships": count,
            "total_relationships": len(relationships),
            "relationships": [{"type": r["relationship_type"], "target_type": r["target_type"], "target_id": r["target_id"]} for r in relationships],
        },
        "sources": ["content_relationships"],
        "confidence": 0.9,
    }


@mcp_tool(
    name="update_project",
    description="Update a project with new or improved content. Creates a version snapshot before changes.",
    category="project",
    permission="write",
)
async def update_project(
    project_id: str,
    updates: dict,
    reason: str = "",
    agent_id: str = "anonymous",
) -> dict:
    db = get_db()
    from bson import ObjectId
    project = await db.projects.find_one({"_id": ObjectId(project_id)})
    if not project:
        return {"success": False, "error": {"code": "NOT_FOUND", "message": "Project not found"}}

    before_snapshot = {k: v for k, v in project.items() if k not in ("_id",)}

    await create_version(
        entity_type="project",
        entity_id=project_id,
        current_content=before_snapshot,
        agent_id=agent_id,
        reason=reason or "Project update",
    )

    allowed = {"title", "description", "problem", "solution", "features", "tech_stack", "architecture", "role", "business_value", "challenges", "outcomes", "skills", "domains", "github_url", "live_url", "images", "status"}
    safe_updates = {k: v for k, v in updates.items() if k in allowed}

    await db.projects.update_one({"_id": ObjectId(project_id)}, {"$set": safe_updates})

    await record_change("project", project_id, "update", before_snapshot, safe_updates, agent_id, reason)
    await cache_invalidate("projects", "*")

    return {
        "success": True,
        "data": {"project_id": project_id, "updated_fields": list(safe_updates.keys())},
        "sources": ["projects"],
        "changed": True,
        "confidence": 1.0,
    }
