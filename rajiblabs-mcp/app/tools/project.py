"""Project & Portfolio MCP tools — intelligent project management.

Tools for analyzing, organizing, ranking, and improving projects.
Maintains distinction: PROJECTS = all meaningful work, PORTFOLIO = strongest.
"""

import re
from datetime import datetime, timezone

from app.database import get_db, utcnow
from app.tools import mcp_tool, _oid_str, _clean_secret_keys


# ── Project Tools ──

@mcp_tool("get_projects", "Get all published projects with full details",
          "project", permission="public")
async def get_projects(status: str = "published", limit: int = 50) -> dict:
    """Return published projects."""
    db = get_db()
    query = {"status": status} if status != "all" else {}
    projects = await db["projects"].find(query).sort(
        "created_at", -1).limit(limit).to_list(limit)
    return {"projects": [_clean_secret_keys(_oid_str(p)) for p in projects],
            "count": len(projects)}


@mcp_tool("analyze_project", "Analyze a project for completeness and quality",
          "project", permission="agent")
async def analyze_project(project_id: str) -> dict:
    """Analyze a single project for evidence, completeness, and quality."""
    db = get_db()
    from bson import ObjectId
    try:
        project = await db["projects"].find_one({"_id": ObjectId(project_id)})
    except Exception:
        project = await db["projects"].find_one({"slug": project_id})

    if not project:
        return {"error": f"Project not found: {project_id}"}

    issues = []
    recommendations = []
    score = 0

    # Required fields for a strong case study
    required = [
        ("title", "Title", 5),
        ("description", "Description", 10),
        ("summary", "Summary", 8),
        ("technologies", "Technologies", 7),
        ("features", "Key Features", 6),
        ("architecture", "Architecture", 5),
        ("challenges", "Challenges", 4),
        ("outcome", "Outcome / Business Value", 5),
        ("live_url", "Live URL", 3),
        ("github_url", "GitHub URL", 3),
        ("images", "Screenshots", 3),
    ]

    for field, label, points in required:
        val = project.get(field)
        if val and (not isinstance(val, list) or len(val) > 0):
            score += points
        else:
            issues.append(f"Missing {label}")
            recommendations.append(f"Add {label} to improve case study quality")

    # Bonus for professional relevance
    desc = (project.get("description", "") + " " + project.get("summary", "")).lower()
    if any(kw in desc for kw in ["enterprise", "production", "scaled", "millions"]):
        score += 5
    if any(kw in desc for kw in ["ai", "machine learning", "llm", "rag"]):
        score += 3
    if any(kw in desc for kw in ["azure", "cloud", "aws", "gcp"]):
        score += 3

    max_score = sum(p for _, _, p in required) + 11
    normalized_score = min(1.0, score / max_score) if max_score > 0 else 0

    # Connect to skills
    tech = project.get("technologies", []) or project.get("tech_stack", [])
    related_skills = []
    for t in tech:
        evidence = await db["skill_evidence"].find_one(
            {"skill": {"$regex": f"^{re.escape(str(t))}$", "$options": "i"}})
        if evidence:
            related_skills.append(str(t))

    return {
        "project_id": str(project["_id"]),
        "title": project.get("title", ""),
        "score": round(normalized_score, 2),
        "max_score": max_score,
        "raw_score": score,
        "issues": issues,
        "recommendations": recommendations,
        "related_skills": related_skills,
        "is_portfolio_ready": normalized_score >= 0.7,
    }


@mcp_tool("improve_project", "Suggest improvements for a project",
          "project", permission="agent")
async def improve_project(project_id: str) -> dict:
    """Generate improvement suggestions for a project."""
    analysis = await analyze_project(project_id=project_id)
    if "error" in analysis:
        return analysis

    improvements = []

    # Add missing fields based on analysis
    for issue in analysis.get("issues", []):
        if "Description" in issue:
            improvements.append({
                "priority": "high",
                "field": "description",
                "action": "Write a clear 2-3 sentence description of what the project does",
            })
        elif "Technologies" in issue:
            improvements.append({
                "priority": "high",
                "field": "technologies",
                "action": "List all technologies, frameworks, and tools used",
            })
        elif "Architecture" in issue:
            improvements.append({
                "priority": "medium",
                "field": "architecture",
                "action": "Describe the system architecture and key design decisions",
            })
        elif "Challenges" in issue:
            improvements.append({
                "priority": "medium",
                "field": "challenges",
                "action": "Document technical challenges and how they were solved",
            })
        elif "Outcome" in issue:
            improvements.append({
                "priority": "medium",
                "field": "outcome",
                "action": "Describe business impact, metrics, or results",
            })

    return {
        "project_id": analysis["project_id"],
        "current_score": analysis["score"],
        "improvement_count": len(improvements),
        "improvements": improvements,
    }


@mcp_tool("organize_projects", "Organize projects into categories",
          "project", permission="agent")
async def organize_projects() -> dict:
    """Categorize projects by type, technology, and business domain."""
    db = get_db()
    projects = await db["projects"].find(
        {"status": "published"}).to_list(100)

    categories = {
        "enterprise": [],
        "ai_ml": [],
        "cloud": [],
        "web_app": [],
        "mobile": [],
        "api": [],
        "saas": [],
        "other": [],
    }

    for p in projects:
        desc = (p.get("description", "") + " " + p.get("summary", "")).lower()
        tech = str(p.get("technologies", []) or p.get("tech_stack", [])).lower()

        categorized = False
        if any(kw in desc or kw in tech for kw in ["ai", "llm", "rag", "machine learning"]):
            categories["ai_ml"].append(p.get("title", ""))
            categorized = True
        if any(kw in desc or kw in tech for kw in ["azure", "aws", "cloud", "kubernetes"]):
            categories["cloud"].append(p.get("title", ""))
            categorized = True
        if any(kw in desc for kw in ["enterprise", "production", "business"]):
            categories["enterprise"].append(p.get("title", ""))
            categorized = True
        if any(kw in desc for kw in ["saas", "platform", "subscription"]):
            categories["saas"].append(p.get("title", ""))
            categorized = True
        if any(kw in desc for kw in ["mobile", "ios", "android", "xamarin", "maui"]):
            categories["mobile"].append(p.get("title", ""))
            categorized = True
        if any(kw in desc for kw in ["api", "rest", "graphql", "microservice"]):
            categories["api"].append(p.get("title", ""))
            categorized = True
        if any(kw in desc for kw in ["web", "dashboard", "portal", "frontend"]):
            categories["web_app"].append(p.get("title", ""))
            categorized = True
        if not categorized:
            categories["other"].append(p.get("title", ""))

    return {
        "total_projects": len(projects),
        "categories": {k: v for k, v in categories.items() if v},
    }


@mcp_tool("rank_projects", "Rank projects by professional importance",
          "project", permission="agent")
async def rank_projects() -> dict:
    """Rank projects by multiple factors for portfolio selection."""
    db = get_db()
    projects = await db["projects"].find(
        {"status": "published"}).to_list(100)

    rankings = []
    for p in projects:
        desc = (p.get("description", "") + " " + p.get("summary", "")).lower()
        tech = str(p.get("technologies", []) or p.get("tech_stack", [])).lower()

        # Calculate scores
        tech_depth = min(1.0, len(p.get("technologies", []) or []) / 10)
        business_value = 0.8 if any(kw in desc for kw in [
            "enterprise", "production", "business", "revenue"]) else 0.4
        ai_score = 0.9 if any(kw in desc or kw in tech for kw in [
            "ai", "llm", "rag", "machine learning"]) else 0.0
        cloud_score = 0.9 if any(kw in desc or kw in tech for kw in [
            "azure", "aws", "cloud", "kubernetes"]) else 0.0
        arch_score = 0.8 if any(kw in desc for kw in [
            "architecture", "microservices", "system design"]) else 0.3

        # Completeness
        fields = ["description", "summary", "technologies", "features",
                   "architecture", "challenges", "outcome", "images"]
        completeness = sum(1 for f in fields if p.get(f)) / len(fields)

        total = (tech_depth * 0.2 + business_value * 0.2 + ai_score * 0.15 +
                 cloud_score * 0.15 + arch_score * 0.15 + completeness * 0.15)

        rankings.append({
            "id": str(p["_id"]),
            "title": p.get("title", ""),
            "technical_depth": round(tech_depth, 2),
            "business_value": round(business_value, 2),
            "ai_capability": round(ai_score, 2),
            "cloud_capability": round(cloud_score, 2),
            "architecture_complexity": round(arch_score, 2),
            "completeness": round(completeness, 2),
            "total_score": round(total, 2),
        })

    rankings.sort(key=lambda x: x["total_score"], reverse=True)

    return {
        "rankings": rankings,
        "total": len(rankings),
    }


# ── Portfolio Tools ──

@mcp_tool("get_portfolio", "Get portfolio-ready projects ranked by importance",
          "portfolio", permission="public")
async def get_portfolio(limit: int = 10) -> dict:
    """Return the strongest professionally presentable projects."""
    db = get_db()
    # Portfolio = projects marked as portfolio or top-ranked
    portfolio = await db["projects"].find(
        {"status": "published", "$or": [
            {"is_portfolio": True},
            {"featured": True},
        ]}
    ).sort("created_at", -1).limit(limit).to_list(limit)

    # If not enough portfolio projects, fill from ranking
    if len(portfolio) < limit:
        existing_ids = [p["_id"] for p in portfolio]
        remaining = await db["projects"].find(
            {"status": "published", "_id": {"$nin": existing_ids}}
        ).sort("created_at", -1).limit(limit - len(portfolio)).to_list(limit - len(portfolio))
        portfolio.extend(remaining)

    return {
        "portfolio": [_clean_secret_keys(_oid_str(p)) for p in portfolio[:limit]],
        "count": min(len(portfolio), limit),
    }


@mcp_tool("analyze_portfolio", "Analyze portfolio health and completeness",
          "portfolio", permission="agent")
async def analyze_portfolio() -> dict:
    """Analyze portfolio for completeness, diversity, and evidence."""
    db = get_db()
    projects = await db["projects"].find(
        {"status": "published"}).to_list(100)

    portfolio = [p for p in projects if p.get("is_portfolio") or p.get("featured")]

    issues = []
    recommendations = []

    if not portfolio:
        issues.append("No projects marked as portfolio")
        recommendations.append("Mark strong projects as portfolio-worthy")

    # Check diversity
    tech_diversity = set()
    domain_diversity = set()
    for p in portfolio:
        for t in (p.get("technologies") or []):
            tech_diversity.add(t.lower())
        for d in (p.get("domains") or []):
            domain_diversity.add(d.lower())

    if len(tech_diversity) < 5:
        issues.append(f"Only {len(tech_diversity)} unique technologies in portfolio")
    if len(domain_diversity) < 3:
        issues.append(f"Only {len(domain_diversity)} domains represented")

    # Check completeness
    complete_projects = 0
    for p in portfolio:
        fields = ["description", "summary", "technologies", "images"]
        if sum(1 for f in fields if p.get(f)) >= 3:
            complete_projects += 1

    completeness = complete_projects / len(portfolio) if portfolio else 0

    return {
        "total_portfolio_projects": len(portfolio),
        "total_published": len(projects),
        "tech_diversity": len(tech_diversity),
        "domain_diversity": len(domain_diversity),
        "completeness": round(completeness, 2),
        "issues": issues,
        "recommendations": recommendations,
    }
