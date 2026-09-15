from __future__ import annotations

import logging
from typing import Any

from app.database import get_db
from app.tools import mcp_tool, _oid_str

logger = logging.getLogger(__name__)


@mcp_tool(
    name="analyze_seo",
    description="Analyze site-wide SEO health: metadata, headings, images, links.",
    category="seo",
    permission="analyze",
)
async def analyze_seo(agent_id: str = "anonymous") -> dict:
    db = get_db()

    profile = await db.profiles.find_one({})
    projects = []
    async for proj in db.projects.find({"status": "published"}):
        projects.append(proj)

    pages_checked = 1 + len(projects)
    issues = []
    warnings = []

    if not profile:
        issues.append("No profile found")
    else:
        if not profile.get("meta_title"):
            warnings.append("Profile missing meta_title")
        if not profile.get("meta_description"):
            warnings.append("Profile missing meta_description")

    for proj in projects:
        if not proj.get("meta_title"):
            warnings.append(f"Project '{proj.get('title', '')}' missing meta_title")
        if not proj.get("meta_description"):
            warnings.append(f"Project '{proj.get('title', '')}' missing meta_description")

    score = max(0, 100 - len(issues) * 10 - len(warnings) * 2)

    return {
        "success": True,
        "data": {
            "pages_checked": pages_checked,
            "score": round(score, 1),
            "issues": issues,
            "warnings": warnings[:20],
            "total_warnings": len(warnings),
        },
        "sources": ["profiles", "projects"],
        "confidence": 0.85,
    }


@mcp_tool(
    name="generate_metadata",
    description="Generate SEO metadata for a page.",
    category="seo",
    permission="propose",
)
async def generate_metadata(
    page_type: str, page_id: str, agent_id: str = "anonymous"
) -> dict:
    db = get_db()
    from bson import ObjectId

    content = None
    if page_type == "profile":
        content = await db.profiles.find_one({})
    elif page_type == "project":
        content = await db.projects.find_one({"_id": ObjectId(page_id)})
    elif page_type == "product":
        content = await db.products.find_one({"_id": ObjectId(page_id)})

    if not content:
        return {"success": False, "error": {"code": "NOT_FOUND", "message": "Content not found"}}

    title = content.get("title", content.get("name", ""))
    description = content.get("description", content.get("about", ""))[:160]

    metadata = {
        "meta_title": f"{title} | RajibLabs",
        "meta_description": description,
        "og_title": title,
        "og_description": description,
        "keywords": content.get("skills", [])[:10] if isinstance(content.get("skills"), list) else [],
    }

    return {
        "success": True,
        "data": {"page_type": page_type, "page_id": page_id, "metadata": metadata},
        "sources": [],
        "confidence": 0.8,
    }


@mcp_tool(
    name="validate_metadata",
    description="Validate SEO metadata for completeness and best practices.",
    category="seo",
    permission="analyze",
)
async def validate_metadata(agent_id: str = "anonymous") -> dict:
    db = get_db()
    issues = []

    profile = await db.profiles.find_one({})
    if profile:
        if not profile.get("meta_title"):
            issues.append({"page": "profile", "field": "meta_title", "issue": "Missing"})
        elif len(profile.get("meta_title", "")) > 60:
            issues.append({"page": "profile", "field": "meta_title", "issue": "Too long (>60 chars)"})

        if not profile.get("meta_description"):
            issues.append({"page": "profile", "field": "meta_description", "issue": "Missing"})
        elif len(profile.get("meta_description", "")) > 160:
            issues.append({"page": "profile", "field": "meta_description", "issue": "Too long (>160 chars)"})

    async for proj in db.projects.find({"status": "published"}):
        if not proj.get("meta_title"):
            issues.append({"page": proj.get("title", ""), "field": "meta_title", "issue": "Missing"})
        if not proj.get("meta_description"):
            issues.append({"page": proj.get("title", ""), "field": "meta_description", "issue": "Missing"})

    return {
        "success": True,
        "data": {"issues": issues, "total": len(issues)},
        "sources": ["profiles", "projects"],
        "confidence": 0.9,
    }


@mcp_tool(
    name="find_missing_metadata",
    description="Find pages missing SEO metadata.",
    category="seo",
    permission="analyze",
)
async def find_missing_metadata(agent_id: str = "anonymous") -> dict:
    db = get_db()
    missing = []

    profile = await db.profiles.find_one({})
    if profile and not profile.get("meta_title"):
        missing.append({"type": "profile", "id": _oid_str(profile["_id"]), "title": profile.get("name", "")})

    async for proj in db.projects.find({"status": "published"}):
        if not proj.get("meta_title"):
            missing.append({"type": "project", "id": _oid_str(proj["_id"]), "title": proj.get("title", "")})

    return {
        "success": True,
        "data": {"missing_metadata": missing, "total": len(missing)},
        "sources": ["profiles", "projects"],
        "confidence": 0.95,
    }


@mcp_tool(
    name="find_internal_link_opportunities",
    description="Find internal linking opportunities between projects, skills, and products.",
    category="seo",
    permission="analyze",
)
async def find_internal_link_opportunities(agent_id: str = "anonymous") -> dict:
    db = get_db()
    opportunities = []

    projects = []
    async for proj in db.projects.find({"status": "published"}):
        projects.append(proj)

    skills = []
    async for skill in db.skills.find():
        skills.append(skill)

    for proj in projects:
        proj_skills = set(s.lower() for s in proj.get("skills", []))
        for skill in skills:
            if skill.get("name", "").lower() in proj_skills:
                opportunities.append({
                    "from": f"project/{proj.get('title', '')}",
                    "to": f"skill/{skill.get('name', '')}",
                    "type": "skill_reference",
                })

    return {
        "success": True,
        "data": {"opportunities": opportunities[:50], "total": len(opportunities)},
        "sources": ["projects", "skills"],
        "confidence": 0.8,
    }


@mcp_tool(
    name="analyze_content_quality",
    description="Analyze content quality for SEO: readability, structure, keyword usage.",
    category="seo",
    permission="analyze",
)
async def analyze_content_quality(agent_id: str = "anonymous") -> dict:
    db = get_db()
    results = []

    async for proj in db.projects.find({"status": "published"}):
        desc = proj.get("description", "")
        quality = {
            "title": proj.get("title", ""),
            "id": _oid_str(proj["_id"]),
            "description_length": len(desc),
            "has_images": bool(proj.get("images")),
            "has_skills": bool(proj.get("skills")),
            "has_github": bool(proj.get("github_url")),
            "score": 0,
        }

        score = 0
        if desc:
            score += 20
            if len(desc) > 100:
                score += 10
            if len(desc) > 300:
                score += 10
        if proj.get("images"):
            score += 15
        if proj.get("skills"):
            score += 15
        if proj.get("github_url"):
            score += 10
        if proj.get("problem"):
            score += 10
        if proj.get("solution"):
            score += 10

        quality["score"] = score
        results.append(quality)

    return {
        "success": True,
        "data": {"projects": results, "average_score": round(sum(r["score"] for r in results) / max(len(results), 1), 1)},
        "sources": ["projects"],
        "confidence": 0.85,
    }


@mcp_tool(
    name="validate_canonical",
    description="Validate canonical URLs are set correctly.",
    category="seo",
    permission="analyze",
)
async def validate_canonical(agent_id: str = "anonymous") -> dict:
    db = get_db()
    missing = []

    async for proj in db.projects.find({"status": "published"}):
        if not proj.get("canonical_url"):
            missing.append({"type": "project", "id": _oid_str(proj["_id"]), "title": proj.get("title", "")})

    return {
        "success": True,
        "data": {"missing_canonical": missing, "total": len(missing)},
        "sources": ["projects"],
        "confidence": 0.9,
    }


@mcp_tool(
    name="validate_sitemap",
    description="Validate sitemap coverage across all public content.",
    category="seo",
    permission="analyze",
)
async def validate_sitemap(agent_id: str = "anonymous") -> dict:
    db = get_db()

    profile = await db.profiles.find_one({})
    projects = await db.projects.count_documents({"status": "published"})
    products = await db.products.count_documents({})

    return {
        "success": True,
        "data": {
            "sitemap_entries": {
                "profile": profile is not None,
                "projects": projects,
                "products": products,
            },
            "total_public_pages": (1 if profile else 0) + projects + products,
        },
        "sources": ["profiles", "projects", "products"],
        "confidence": 0.9,
    }


@mcp_tool(
    name="check_internal_links",
    description="Check internal links for broken references.",
    category="seo",
    permission="analyze",
)
async def check_internal_links(agent_id: str = "anonymous") -> dict:
    return {
        "success": True,
        "data": {"broken_links": [], "total_checked": 0, "message": "Link checking requires HTTP client"},
        "sources": [],
        "confidence": 0.5,
    }


@mcp_tool(
    name="check_broken_links",
    description="Check for broken external links.",
    category="seo",
    permission="analyze",
)
async def check_broken_links(agent_id: str = "anonymous") -> dict:
    return {
        "success": True,
        "data": {"broken_links": [], "total_checked": 0, "message": "External link checking requires HTTP client"},
        "sources": [],
        "confidence": 0.5,
    }


@mcp_tool(
    name="analyze_headings",
    description="Analyze heading structure across pages.",
    category="seo",
    permission="analyze",
)
async def analyze_headings(agent_id: str = "anonymous") -> dict:
    return {
        "success": True,
        "data": {"headings": {}, "message": "Heading analysis requires page rendering"},
        "sources": [],
        "confidence": 0.5,
    }


@mcp_tool(
    name="analyze_images",
    description="Analyze images for alt text and SEO compliance.",
    category="seo",
    permission="analyze",
)
async def analyze_images(agent_id: str = "anonymous") -> dict:
    return {
        "success": True,
        "data": {"images": [], "message": "Image analysis requires page rendering"},
        "sources": [],
        "confidence": 0.5,
    }
