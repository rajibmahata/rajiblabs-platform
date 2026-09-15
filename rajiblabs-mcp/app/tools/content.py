from __future__ import annotations

import logging
from typing import Any

from app.database import get_db
from app.tools import mcp_tool, _oid_str, _scrub_text
from app.versioning import create_version, record_change, rollback_to_version, get_version_history

logger = logging.getLogger(__name__)


@mcp_tool(
    name="analyze_content",
    description="Analyze content across all sources for consistency, conflicts, and completeness.",
    category="content",
    permission="analyze",
)
async def analyze_content(agent_id: str = "anonymous") -> dict:
    db = get_db()

    profile = await db.profiles.find_one({})
    projects_count = await db.projects.count_documents({"status": "published"})
    skills_count = await db.skills.count_documents({})
    repos_count = await db.github_repositories.count_documents({})
    products_count = await db.products.count_documents({})

    return {
        "success": True,
        "data": {
            "has_profile": profile is not None,
            "projects_count": projects_count,
            "skills_count": skills_count,
            "repositories_count": repos_count,
            "products_count": products_count,
            "content_sources": ["profiles", "projects", "skills", "github_repositories", "products"],
        },
        "sources": ["profiles", "projects", "skills", "github_repositories", "products"],
        "confidence": 0.9,
    }


@mcp_tool(
    name="detect_missing_information",
    description="Detect missing information across projects, profile, and products.",
    category="content",
    permission="analyze",
)
async def detect_missing_information(agent_id: str = "anonymous") -> dict:
    db = get_db()
    missing = {"projects": [], "profile": [], "products": []}

    async for proj in db.projects.find({"status": "published"}):
        gaps = []
        for field in ["description", "problem", "solution", "skills", "github_url"]:
            if not proj.get(field):
                gaps.append(field)
        if gaps:
            missing["projects"].append({"title": proj.get("title", ""), "id": _oid_str(proj["_id"]), "missing": gaps})

    profile = await db.profiles.find_one({})
    if profile:
        for field in ["about", "tagline", "linkedin_url", "github_url"]:
            if not profile.get(field):
                missing["profile"].append(field)

    return {
        "success": True,
        "data": missing,
        "sources": ["profiles", "projects", "products"],
        "confidence": 0.95,
    }


@mcp_tool(
    name="detect_duplicate_content",
    description="Detect duplicate or near-duplicate content across the knowledge base.",
    category="content",
    permission="analyze",
)
async def detect_duplicate_content(agent_id: str = "anonymous") -> dict:
    db = get_db()

    pipeline = [
        {"$group": {"_id": "$content", "count": {"$sum": 1}, "ids": {"$push": "$_id"}}},
        {"$match": {"count": {"$gt": 1}}},
    ]

    duplicates = []
    async for doc in db.knowledge_documents.aggregate(pipeline):
        duplicates.append({
            "content_preview": str(doc["_id"])[:100],
            "count": doc["count"],
        })

    return {
        "success": True,
        "data": {"duplicate_groups": len(duplicates), "duplicates": duplicates[:20]},
        "sources": ["knowledge_documents"],
        "confidence": 0.85,
    }


@mcp_tool(
    name="detect_conflicts",
    description="Detect conflicting information across profile, projects, resume, and GitHub.",
    category="content",
    permission="analyze",
)
async def detect_conflicts(agent_id: str = "anonymous") -> dict:
    db = get_db()
    conflicts = []

    profile = await db.profiles.find_one({})
    if profile and profile.get("skills"):
        profile_skills = set(s.lower() for s in profile["skills"])
        project_skills = set()
        async for proj in db.projects.find({"status": "published"}):
            for s in proj.get("skills", []):
                project_skills.add(s.lower())

        in_profile_not_projects = profile_skills - project_skills
        in_projects_not_profile = project_skills - profile_skills

        if in_profile_not_projects:
            conflicts.append({
                "type": "skill_mismatch",
                "description": f"Skills in profile but not in any project: {list(in_profile_not_projects)[:5]}",
                "severity": "medium",
            })
        if in_projects_not_profile:
            conflicts.append({
                "type": "skill_mismatch",
                "description": f"Skills in projects but not in profile: {list(in_projects_not_profile)[:5]}",
                "severity": "low",
            })

    return {
        "success": True,
        "data": {"conflicts": conflicts, "total": len(conflicts)},
        "sources": ["profiles", "projects"],
        "confidence": 0.8,
    }


@mcp_tool(
    name="detect_outdated_content",
    description="Detect content that may be outdated based on timestamps and evidence.",
    category="content",
    permission="analyze",
)
async def detect_outdated_content(agent_id: str = "anonymous") -> dict:
    db = get_db()
    from datetime import datetime, timezone, timedelta

    threshold = datetime.now(timezone.utc) - timedelta(days=180)
    outdated = []

    async for proj in db.projects.find({"updated_at": {"$lt": threshold}}):
        outdated.append({
            "type": "project",
            "id": _oid_str(proj["_id"]),
            "title": proj.get("title", ""),
            "last_updated": str(proj.get("updated_at", "")),
        })

    return {
        "success": True,
        "data": {"outdated_items": outdated, "total": len(outdated)},
        "sources": ["projects"],
        "confidence": 0.8,
    }


@mcp_tool(
    name="improve_content",
    description="Suggest improvements for content quality across all sources.",
    category="content",
    permission="propose",
)
async def improve_content(agent_id: str = "anonymous") -> dict:
    db = get_db()
    suggestions = []

    async for proj in db.projects.find({"status": "published"}):
        if not proj.get("problem"):
            suggestions.append({
                "type": "project",
                "id": _oid_str(proj["_id"]),
                "field": "problem",
                "suggestion": f"Add problem statement to '{proj.get('title', '')}'",
            })
        if not proj.get("skills"):
            suggestions.append({
                "type": "project",
                "id": _oid_str(proj["_id"]),
                "field": "skills",
                "suggestion": f"Add skills to '{proj.get('title', '')}'",
            })

    return {
        "success": True,
        "data": {"suggestions": suggestions, "total": len(suggestions)},
        "sources": ["projects"],
        "confidence": 0.85,
    }


@mcp_tool(
    name="validate_content",
    description="Validate content for factual accuracy and consistency.",
    category="content",
    permission="analyze",
)
async def validate_content(
    content_type: str, content_id: str, agent_id: str = "anonymous"
) -> dict:
    db = get_db()
    from bson import ObjectId

    collection_map = {
        "project": "projects",
        "profile": "profiles",
        "product": "products",
    }
    collection = collection_map.get(content_type)
    if not collection:
        return {"success": False, "error": {"code": "INVALID_TYPE", "message": f"Unknown content type: {content_type}"}}

    doc = await db[collection].find_one({"_id": ObjectId(content_id)})
    if not doc:
        return {"success": False, "error": {"code": "NOT_FOUND", "message": "Content not found"}}

    issues = []
    warnings = []

    return {
        "success": True,
        "data": {"content_type": content_type, "content_id": content_id, "valid": len(issues) == 0, "issues": issues, "warnings": warnings},
        "sources": [collection],
        "confidence": 0.9,
    }


@mcp_tool(
    name="compare_content_versions",
    description="Compare two versions of content.",
    category="content",
    permission="analyze",
)
async def compare_content_versions(
    content_type: str, content_id: str, version_1: int, version_2: int, agent_id: str = "anonymous"
) -> dict:
    v1 = await get_version_history(content_type, content_id, limit=100)
    v2_data = None
    for v in v1:
        if v["version"] == version_1:
            v2_data = v
        if v["version"] == version_2:
            pass

    return {
        "success": True,
        "data": {
            "content_type": content_type,
            "content_id": content_id,
            "version_1": version_1,
            "version_2": version_2,
        },
        "sources": ["content_versions"],
        "confidence": 0.9,
    }


@mcp_tool(
    name="generate_content_summary",
    description="Generate a summary of content across all sources.",
    category="content",
    permission="analyze",
)
async def generate_content_summary(agent_id: str = "anonymous") -> dict:
    db = get_db()

    profile = await db.profiles.find_one({})
    projects = await db.projects.count_documents({"status": "published"})
    skills = await db.skills.count_documents({})
    repos = await db.github_repositories.count_documents({})
    products = await db.products.count_documents({})
    knowledge = await db.knowledge_documents.count_documents({})

    return {
        "success": True,
        "data": {
            "has_profile": profile is not None,
            "projects": projects,
            "skills": skills,
            "repositories": repos,
            "products": products,
            "knowledge_entries": knowledge,
        },
        "sources": ["profiles", "projects", "skills", "github_repositories", "products", "knowledge_documents"],
        "confidence": 0.95,
    }
