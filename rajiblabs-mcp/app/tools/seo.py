"""SEO MCP tools — search engine optimization intelligence.

Operates from verified RajibLabs knowledge. Never generates fake
achievements, keywords, or content.
"""

import re
from datetime import datetime, timezone
from urllib.parse import urlparse

from app.database import get_db, utcnow
from app.tools import mcp_tool, _oid_str, _clean_secret_keys


@mcp_tool("analyze_seo", "Analyze SEO health for a page or the entire site",
          "seo", permission="agent")
async def analyze_seo(url: str | None = None) -> dict:
    """Analyze SEO metrics for a page or site-wide."""
    db = get_db()
    issues = []
    recommendations = []

    # Get site content
    projects = await db["projects"].find(
        {"status": "published"}).to_list(100)
    products = await db["products"].find(
        {"status": "published"}).to_list(50)

    # Check pages for SEO issues
    pages_analyzed = 0
    for p in projects:
        title = p.get("title", "")
        desc = p.get("description", "") or p.get("summary", "")

        if not title:
            issues.append(f"Project {p.get('slug', '')}: missing title")
        if len(title) > 60:
            issues.append(f"Project '{title}': title too long ({len(title)} chars)")
        if not desc:
            issues.append(f"Project '{title}': missing description")
        elif len(desc) < 50:
            issues.append(f"Project '{title}': description too short")
        elif len(desc) > 160:
            issues.append(f"Project '{title}': description too long ({len(desc)} chars)")

        pages_analyzed += 1

    for p in products:
        title = p.get("title", "")
        desc = p.get("description", "") or p.get("summary", "")

        if not title:
            issues.append(f"Product {p.get('slug', '')}: missing title")
        if not desc:
            issues.append(f"Product '{title}': missing description")

        pages_analyzed += 1

    return {
        "pages_analyzed": pages_analyzed,
        "issues_count": len(issues),
        "issues": issues[:30],
        "recommendations": recommendations,
    }


@mcp_tool("generate_metadata", "Generate SEO metadata for a page",
          "seo", permission="agent")
async def generate_metadata(page_type: str, page_id: str) -> dict:
    """Generate title, description, and keywords for a page."""
    db = get_db()
    entity = None
    if page_type == "project":
        from bson import ObjectId
        try:
            entity = await db["projects"].find_one({"_id": ObjectId(page_id)})
        except Exception:
            entity = await db["projects"].find_one({"slug": page_id})
    elif page_type == "product":
        from bson import ObjectId
        try:
            entity = await db["products"].find_one({"_id": ObjectId(page_id)})
        except Exception:
            entity = await db["products"].find_one({"slug": page_id})

    if not entity:
        return {"error": f"Entity not found: {page_type}/{page_id}"}

    title = entity.get("title", "")
    desc = entity.get("description", "") or entity.get("summary", "")
    techs = entity.get("technologies", []) or entity.get("tech_stack", [])

    # Generate metadata
    meta = {
        "title": f"{title} | RajibLabs" if title else "",
        "description": desc[:160] if desc else "",
        "keywords": list(set(techs + ["RajibLabs", "Rajib Mahata"]))[:10],
        "og_title": title,
        "og_description": desc[:200] if desc else "",
        "schema_type": "SoftwareApplication" if page_type == "project" else "Product",
    }

    return meta


@mcp_tool("validate_metadata", "Validate SEO metadata for completeness",
          "seo", permission="agent")
async def validate_metadata(page_type: str, page_id: str) -> dict:
    """Validate that a page has proper SEO metadata."""
    metadata = await generate_metadata(page_type=page_type, page_id=page_id)
    if "error" in metadata:
        return metadata

    issues = []
    if not metadata.get("title"):
        issues.append("Missing title")
    elif len(metadata["title"]) > 60:
        issues.append(f"Title too long ({len(metadata['title'])} chars)")
    if not metadata.get("description"):
        issues.append("Missing description")
    elif len(metadata["description"]) > 160:
        issues.append(f"Description too long ({len(metadata['description'])} chars)")
    if not metadata.get("keywords"):
        issues.append("Missing keywords")

    return {
        "valid": len(issues) == 0,
        "metadata": metadata,
        "issues": issues,
    }


@mcp_tool("find_missing_metadata", "Find pages missing SEO metadata",
          "seo", permission="agent")
async def find_missing_metadata() -> dict:
    """Scan all published pages for missing metadata."""
    db = get_db()
    missing = []

    projects = await db["projects"].find(
        {"status": "published"}).to_list(100)
    for p in projects:
        issues = []
        if not p.get("description") and not p.get("summary"):
            issues.append("missing_description")
        if not p.get("technologies") and not p.get("tech_stack"):
            issues.append("missing_technologies")
        if not p.get("images"):
            issues.append("missing_images")
        if issues:
            missing.append({
                "type": "project",
                "id": str(p["_id"]),
                "title": p.get("title", ""),
                "slug": p.get("slug", ""),
                "issues": issues,
            })

    products = await db["products"].find(
        {"status": "published"}).to_list(50)
    for p in products:
        issues = []
        if not p.get("description"):
            issues.append("missing_description")
        if issues:
            missing.append({
                "type": "product",
                "id": str(p["_id"]),
                "title": p.get("title", ""),
                "slug": p.get("slug", ""),
                "issues": issues,
            })

    return {"pages_with_missing_metadata": missing, "count": len(missing)}


@mcp_tool("find_internal_link_opportunities",
          "Find opportunities for internal linking",
          "seo", permission="agent")
async def find_internal_link_opportunities() -> dict:
    """Suggest internal link connections between related content."""
    db = get_db()
    projects = await db["projects"].find(
        {"status": "published"}).to_list(100)

    opportunities = []
    for i, p1 in enumerate(projects):
        tech1 = set(t.lower() for t in (p1.get("technologies") or []))
        for p2 in projects[i+1:]:
            tech2 = set(t.lower() for t in (p2.get("technologies") or []))
            shared = tech1 & tech2
            if len(shared) >= 2:
                opportunities.append({
                    "from": p1.get("title", ""),
                    "to": p2.get("title", ""),
                    "shared_technologies": list(shared)[:5],
                })

    return {"opportunities": opportunities[:20], "count": len(opportunities)}


@mcp_tool("analyze_content_quality",
          "Analyze content quality across the site",
          "seo", permission="agent")
async def analyze_content_quality() -> dict:
    """Analyze content quality metrics site-wide."""
    db = get_db()
    projects = await db["projects"].find(
        {"status": "published"}).to_list(100)

    quality_scores = []
    for p in projects:
        desc_len = len(p.get("description", "") or "")
        summary_len = len(p.get("summary", "") or "")
        has_tech = bool(p.get("technologies") or p.get("tech_stack"))
        has_features = bool(p.get("features"))
        has_images = bool(p.get("images"))
        has_challenges = bool(p.get("challenges"))
        has_outcome = bool(p.get("outcome"))

        score = 0
        if desc_len >= 100: score += 20
        elif desc_len >= 50: score += 10
        if summary_len >= 50: score += 15
        if has_tech: score += 15
        if has_features: score += 15
        if has_images: score += 10
        if has_challenges: score += 10
        if has_outcome: score += 15

        quality_scores.append({
            "title": p.get("title", ""),
            "score": score,
            "description_length": desc_len,
            "has_technologies": has_tech,
            "has_features": has_features,
            "has_images": has_images,
        })

    avg_score = (sum(q["score"] for q in quality_scores) / len(quality_scores)
                 if quality_scores else 0)

    return {
        "pages_analyzed": len(quality_scores),
        "average_quality_score": round(avg_score, 1),
        "pages": sorted(quality_scores, key=lambda x: x["score"])[:10],
    }
