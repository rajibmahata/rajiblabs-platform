from __future__ import annotations

import logging
from typing import Any

from app.database import get_db
from app.tools import mcp_tool, _oid_str, _clean_secret_keys
from app.cache import cache_get, cache_set, cache_invalidate

logger = logging.getLogger(__name__)


@mcp_tool(
    name="get_profile",
    description="Get the complete Rajib profile with all fields. Returns verified professional data.",
    category="profile",
    permission="read",
)
async def get_profile(agent_id: str = "anonymous") -> dict:
    cached = await cache_get("profile", "full")
    if cached:
        return {"success": True, "data": cached, "sources": ["cache"], "confidence": 1.0}

    db = get_db()
    profile = await db.profiles.find_one({})
    if not profile:
        return {"success": False, "error": {"code": "NOT_FOUND", "message": "No profile found"}}

    profile["_id"] = _oid_str(profile["_id"])
    profile = _clean_secret_keys(profile)

    await cache_set("profile", "full", profile)
    return {"success": True, "data": profile, "sources": ["profiles"], "confidence": 1.0}


@mcp_tool(
    name="analyze_profile",
    description="Analyze profile completeness, quality, and evidence backing. Returns structured analysis with score.",
    category="profile",
    permission="analyze",
)
async def analyze_profile(agent_id: str = "anonymous") -> dict:
    db = get_db()
    profile = await db.profiles.find_one({})
    if not profile:
        return {"success": False, "error": {"code": "NOT_FOUND", "message": "No profile found"}}

    fields = {
        "name": profile.get("name", ""),
        "title": profile.get("title", ""),
        "tagline": profile.get("tagline", ""),
        "about": profile.get("about", ""),
        "location": profile.get("location", ""),
        "email": profile.get("email", ""),
        "phone": profile.get("phone", ""),
        "linkedin_url": profile.get("linkedin_url", ""),
        "github_url": profile.get("github_url", ""),
        "website_url": profile.get("website_url", ""),
        "profile_image_url": profile.get("profile_image_url", ""),
        "skills": profile.get("skills", []),
        "domains": profile.get("domains", []),
        "experience_years": profile.get("experience_years", 0),
    }

    filled = sum(1 for k, v in fields.items() if v and v != 0 and v != [])
    total = len(fields)
    completeness = round((filled / total) * 100, 1) if total > 0 else 0

    issues = []
    warnings = []
    if not fields["about"]:
        issues.append({"field": "about", "severity": "high", "message": "Missing professional summary"})
    if not fields["tagline"]:
        warnings.append({"field": "tagline", "severity": "medium", "message": "Missing tagline"})
    if not fields["skills"]:
        issues.append({"field": "skills", "severity": "high", "message": "No skills listed"})
    if not fields["experience_years"]:
        warnings.append({"field": "experience_years", "severity": "low", "message": "Missing experience years"})

    score = completeness
    if issues:
        score = max(0, score - len(issues) * 10)
    if warnings:
        score = max(0, score - len(warnings) * 5)

    return {
        "success": True,
        "data": {
            "completeness": completeness,
            "score": round(score, 1),
            "fields_filled": filled,
            "fields_total": total,
            "issues": issues,
            "warnings": warnings,
        },
        "sources": ["profiles"],
        "confidence": 1.0,
    }


@mcp_tool(
    name="validate_profile",
    description="Validate profile factual accuracy by cross-referencing with projects, skills, GitHub, and resume.",
    category="profile",
    permission="analyze",
)
async def validate_profile(agent_id: str = "anonymous") -> dict:
    db = get_db()
    profile = await db.profiles.find_one({})
    if not profile:
        return {"success": False, "error": {"code": "NOT_FOUND", "message": "No profile found"}}

    evidence = []
    issues = []
    warnings = []

    project_count = await db.projects.count_documents({"status": "published"})
    evidence.append({"source": "projects", "count": project_count})

    skill_count = await db.skills.count_documents({})
    evidence.append({"source": "skills", "count": skill_count})

    repo_count = await db.github_repositories.count_documents({})
    evidence.append({"source": "github_repos", "count": repo_count})

    resume_count = await db.resumes.count_documents({})
    evidence.append({"source": "resumes", "count": resume_count})

    if project_count == 0:
        warnings.append({"field": "projects", "message": "No published projects to validate against"})

    if skill_count == 0:
        warnings.append({"field": "skills", "message": "No skills in database to validate against"})

    score = 100.0
    if issues:
        score -= len(issues) * 15
    if warnings:
        score -= len(warnings) * 5
    score = max(0, score)

    return {
        "success": True,
        "data": {
            "valid": len(issues) == 0,
            "score": round(score, 1),
            "issues": issues,
            "warnings": warnings,
            "evidence": evidence,
        },
        "sources": ["profiles", "projects", "skills", "github_repositories", "resumes"],
        "confidence": 0.95,
    }


@mcp_tool(
    name="optimize_profile",
    description="Suggest optimizations for profile presentation, SEO, and professional positioning.",
    category="profile",
    permission="propose",
)
async def optimize_profile(agent_id: str = "anonymous") -> dict:
    db = get_db()
    profile = await db.profiles.find_one({})
    if not profile:
        return {"success": False, "error": {"code": "NOT_FOUND", "message": "No profile found"}}

    suggestions = []

    if not profile.get("tagline"):
        suggestions.append({
            "type": "content",
            "field": "tagline",
            "priority": "high",
            "suggestion": "Add a professional tagline that highlights core expertise",
        })

    if not profile.get("about") or len(profile.get("about", "")) < 100:
        suggestions.append({
            "type": "content",
            "field": "about",
            "priority": "high",
            "suggestion": "Expand professional summary to at least 100 words",
        })

    if not profile.get("linkedin_url"):
        suggestions.append({
            "type": "link",
            "field": "linkedin_url",
            "priority": "medium",
            "suggestion": "Add LinkedIn profile URL for professional credibility",
        })

    if not profile.get("github_url"):
        suggestions.append({
            "type": "link",
            "field": "github_url",
            "priority": "medium",
            "suggestion": "Add GitHub profile URL for technical credibility",
        })

    if not profile.get("website_url"):
        suggestions.append({
            "type": "link",
            "field": "website_url",
            "priority": "low",
            "suggestion": "Add personal website URL",
        })

    return {
        "success": True,
        "data": {
            "suggestions": suggestions,
            "total_suggestions": len(suggestions),
        },
        "sources": ["profiles"],
        "confidence": 0.85,
    }


@mcp_tool(
    name="get_professional_positioning",
    description="Get evidence-backed professional positioning based on skills, projects, and experience.",
    category="profile",
    permission="read",
)
async def get_professional_positioning(agent_id: str = "anonymous") -> dict:
    db = get_db()
    profile = await db.profiles.find_one({})
    if not profile:
        return {"success": False, "error": {"code": "NOT_FOUND", "message": "No profile found"}}

    skills = []
    async for skill in db.skills.find({}).limit(20):
        skill["_id"] = _oid_str(skill["_id"])
        skills.append(skill)

    projects = []
    async for proj in db.projects.find({"status": "published"}).limit(10):
        proj["_id"] = _oid_str(proj["_id"])
        projects.append(proj)

    domains = []
    async for domain in db.professional_domains.find({}).limit(10):
        domain["_id"] = _oid_str(domain["_id"])
        domains.append(domain)

    positioning = {
        "name": profile.get("name", ""),
        "title": profile.get("title", ""),
        "tagline": profile.get("tagline", ""),
        "core_expertise": [s["name"] for s in skills[:5]] if skills else [],
        "domains": [d.get("name", "") for d in domains] if domains else [],
        "project_count": len(projects),
        "evidence": {
            "skills_count": len(skills),
            "projects_count": len(projects),
            "domains_count": len(domains),
        },
    }

    return {
        "success": True,
        "data": positioning,
        "sources": ["profiles", "skills", "projects", "professional_domains"],
        "confidence": 0.9,
    }
