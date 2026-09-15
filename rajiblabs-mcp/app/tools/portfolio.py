from __future__ import annotations

import logging
from typing import Any

from app.database import get_db
from app.tools import mcp_tool, _oid_str, _clean_secret_keys
from app.cache import cache_get, cache_set
from app.versioning import create_version, record_change
from app.relationships import add_relationship, get_relationships

logger = logging.getLogger(__name__)


@mcp_tool(
    name="get_portfolio",
    description="Get portfolio projects with ranking and featured status.",
    category="portfolio",
    permission="read",
)
async def get_portfolio(limit: int = 10, agent_id: str = "anonymous") -> dict:
    cached = await cache_get("portfolio", f"list:{limit}")
    if cached:
        return {"success": True, "data": cached, "sources": ["cache"], "confidence": 1.0}

    db = get_db()
    projects = []
    async for proj in db.projects.find({"status": "published"}).limit(limit):
        proj["_id"] = _oid_str(proj["_id"])
        proj = _clean_secret_keys(proj)
        projects.append(proj)

    result = {"projects": projects, "count": len(projects)}
    await cache_set("portfolio", f"list:{limit}", result)
    return {"success": True, "data": result, "sources": ["projects"], "confidence": 1.0}


@mcp_tool(
    name="analyze_portfolio",
    description="Analyze portfolio health: completeness, evidence quality, skill coverage.",
    category="portfolio",
    permission="analyze",
)
async def analyze_portfolio(agent_id: str = "anonymous") -> dict:
    db = get_db()
    projects = []
    async for proj in db.projects.find({"status": "published"}):
        proj["_id"] = _oid_str(proj["_id"])
        projects.append(proj)

    total = len(projects)
    if total == 0:
        return {"success": True, "data": {"score": 0, "issues": ["No published projects"]}, "sources": ["projects"], "confidence": 1.0}

    scores = []
    issues = []
    for proj in projects:
        fields = ["title", "description", "problem", "solution", "features", "tech_stack", "github_url", "skills", "images"]
        filled = sum(1 for f in fields if proj.get(f))
        score = (filled / len(fields)) * 100
        scores.append(score)
        if score < 50:
            issues.append({"project": proj.get("title", ""), "score": round(score, 1)})

    avg_score = sum(scores) / len(scores) if scores else 0

    return {
        "success": True,
        "data": {
            "total_projects": total,
            "average_score": round(avg_score, 1),
            "low_quality_projects": issues,
            "quality_distribution": {
                "excellent": sum(1 for s in scores if s >= 80),
                "good": sum(1 for s in scores if 60 <= s < 80),
                "needs_work": sum(1 for s in scores if 40 <= s < 60),
                "poor": sum(1 for s in scores if s < 40),
            },
        },
        "sources": ["projects"],
        "confidence": 0.9,
    }


@mcp_tool(
    name="rank_projects",
    description="Rank projects by business value, technical complexity, evidence quality, and recency.",
    category="portfolio",
    permission="analyze",
)
async def rank_projects(limit: int = 10, agent_id: str = "anonymous") -> dict:
    db = get_db()
    projects = []
    async for proj in db.projects.find({"status": "published"}):
        proj["_id"] = _oid_str(proj["_id"])
        projects.append(proj)

    def rank_score(p: dict) -> float:
        score = 0.0
        if p.get("business_value"):
            score += 25
        if p.get("tech_stack"):
            score += min(25, len(p["tech_stack"]) * 5)
        if p.get("github_url"):
            score += 15
        if p.get("images"):
            score += 10
        if p.get("skills"):
            score += min(15, len(p["skills"]) * 3)
        if p.get("description") and len(p["description"]) > 100:
            score += 10
        return score

    ranked = sorted(projects, key=rank_score, reverse=True)[:limit]
    result = [
        {"rank": i + 1, "project_id": p["_id"], "title": p.get("title", ""), "score": round(rank_score(p), 1)}
        for i, p in enumerate(ranked)
    ]

    return {"success": True, "data": {"rankings": result}, "sources": ["projects"], "confidence": 0.85}


@mcp_tool(
    name="select_featured_projects",
    description="Select the best projects to feature based on evidence quality and completeness.",
    category="portfolio",
    permission="analyze",
)
async def select_featured_projects(count: int = 3, agent_id: str = "anonymous") -> dict:
    db = get_db()
    projects = []
    async for proj in db.projects.find({"status": "published"}):
        proj["_id"] = _oid_str(proj["_id"])
        projects.append(proj)

    def feature_score(p: dict) -> float:
        score = 0.0
        if p.get("images"):
            score += 20
        if p.get("github_url"):
            score += 15
        if p.get("live_url"):
            score += 15
        if p.get("problem") and p.get("solution"):
            score += 20
        if p.get("business_value"):
            score += 15
        if p.get("skills"):
            score += 10
        if p.get("description") and len(p["description"]) > 200:
            score += 5
        return score

    featured = sorted(projects, key=feature_score, reverse=True)[:count]
    result = [
        {"project_id": p["_id"], "title": p.get("title", ""), "score": round(feature_score(p), 1)}
        for p in featured
    ]

    return {"success": True, "data": {"featured": result}, "sources": ["projects"], "confidence": 0.85}


@mcp_tool(
    name="improve_portfolio",
    description="Suggest improvements for the overall portfolio.",
    category="portfolio",
    permission="propose",
)
async def improve_portfolio(agent_id: str = "anonymous") -> dict:
    db = get_db()
    projects = []
    async for proj in db.projects.find({"status": "published"}):
        proj["_id"] = _oid_str(proj["_id"])
        projects.append(proj)

    suggestions = []

    if len(projects) < 5:
        suggestions.append({"priority": "high", "suggestion": f"Portfolio has only {len(projects)} projects. Aim for 5-10 strong projects."})

    no_images = [p.get("title", "") for p in projects if not p.get("images")]
    if no_images:
        suggestions.append({"priority": "medium", "suggestion": f"Add images to: {', '.join(no_images[:5])}"})

    no_github = [p.get("title", "") for p in projects if not p.get("github_url")]
    if no_github:
        suggestions.append({"priority": "low", "suggestion": f"Add GitHub links to: {', '.join(no_github[:5])}"})

    return {"success": True, "data": {"suggestions": suggestions, "project_count": len(projects)}, "sources": ["projects"], "confidence": 0.85}


@mcp_tool(
    name="validate_portfolio",
    description="Validate portfolio consistency and evidence quality.",
    category="portfolio",
    permission="analyze",
)
async def validate_portfolio(agent_id: str = "anonymous") -> dict:
    db = get_db()
    projects = []
    async for proj in db.projects.find({"status": "published"}):
        projects.append(proj)

    issues = []
    for proj in projects:
        if proj.get("skills"):
            for skill in proj["skills"]:
                exists = await db.skills.find_one({"name": {"$regex": f"^{skill}$", "$options": "i"}})
                if not exists:
                    issues.append({"project": proj.get("title", ""), "issue": f"Skill '{skill}' not in database"})

    return {
        "success": True,
        "data": {"valid": len(issues) == 0, "issues": issues, "project_count": len(projects)},
        "sources": ["projects", "skills"],
        "confidence": 0.9,
    }


@mcp_tool(
    name="update_portfolio",
    description="Update portfolio ordering and featured status.",
    category="portfolio",
    permission="write",
)
async def update_portfolio(
    project_ids: list[str],
    featured_ids: list[str] | None = None,
    agent_id: str = "anonymous",
) -> dict:
    db = get_db()
    from bson import ObjectId

    await db.projects.update_many(
        {"_id": {"$in": [ObjectId(pid) for pid in project_ids]}},
        {"$set": {"portfolio_order": {pid: i for i, pid in enumerate(project_ids)}}},
    )

    if featured_ids:
        await db.projects.update_many({}, {"$set": {"featured": False}})
        await db.projects.update_many(
            {"_id": {"$in": [ObjectId(fid) for fid in featured_ids]}},
            {"$set": {"featured": True}},
        )

    return {
        "success": True,
        "data": {"updated": len(project_ids), "featured": len(featured_ids or [])},
        "sources": ["projects"],
        "changed": True,
        "confidence": 1.0,
    }
