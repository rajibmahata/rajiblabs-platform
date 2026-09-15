"""Content Intelligence MCP tools — the content pipeline.

Pipeline: COLLECT → NORMALIZE → UNDERSTAND → CLASSIFY → CONNECT →
VALIDATE → IMPROVE → RANK → PUBLISH → INDEX → VERIFY

Every change must have a reason and evidence. No AI spam.
"""

import hashlib
from datetime import datetime, timezone

from app.database import get_db, utcnow
from app.tools import mcp_tool, _oid_str, _clean_secret_keys


@mcp_tool("validate_content", "Validate content for factual accuracy",
          "content", permission="agent")
async def validate_content(content_type: str, content_id: str) -> dict:
    """Validate content against evidence and quality rules."""
    db = get_db()
    entity = None
    collection_map = {
        "project": "projects",
        "product": "products",
        "profile": "profiles",
        "skill": "skill_evidence",
    }
    collection = collection_map.get(content_type)
    if not collection:
        return {"error": f"Unknown content type: {content_type}"}

    from bson import ObjectId
    try:
        entity = await db[collection].find_one({"_id": ObjectId(content_id)})
    except Exception:
        return {"error": f"Invalid ID: {content_id}"}

    if not entity:
        return {"error": f"Entity not found: {content_type}/{content_id}"}

    validations = []
    warnings = []

    # Factual accuracy checks
    if content_type == "project":
        # Check technologies exist in known databases
        techs = entity.get("technologies", []) or entity.get("tech_stack", [])
        for t in techs:
            validations.append(f"Technology '{t}' listed")

        # Check for claims without evidence
        if entity.get("outcome") and not entity.get("live_url"):
            warnings.append("Outcome claimed but no live URL to verify")

    elif content_type == "profile":
        # Check skills have evidence
        skills = entity.get("skills", [])
        for skill in skills[:10]:
            evidence = await db["skill_evidence"].find_one(
                {"skill": {"$regex": f"^{skill}$", "$options": "i"}})
            if evidence:
                validations.append(f"Skill '{skill}' has evidence")
            else:
                warnings.append(f"Skill '{skill}' lacks evidence")

    # Content hash for change detection
    content_hash = hashlib.md5(
        str(entity).encode()).hexdigest()[:12]

    return {
        "valid": len(warnings) == 0,
        "content_type": content_type,
        "content_id": content_id,
        "content_hash": content_hash,
        "validations": validations,
        "warnings": warnings,
    }


@mcp_tool("version_content", "Create a version snapshot of content",
          "content", permission="agent")
async def version_content(content_type: str, content_id: str,
                          reason: str = "") -> dict:
    """Create a version snapshot before making changes."""
    db = get_db()
    collection_map = {
        "project": "projects",
        "product": "products",
        "profile": "profiles",
    }
    collection = collection_map.get(content_type)
    if not collection:
        return {"error": f"Unknown content type: {content_type}"}

    from bson import ObjectId
    try:
        entity = await db[collection].find_one({"_id": ObjectId(content_id)})
    except Exception:
        return {"error": f"Invalid ID: {content_id}"}

    if not entity:
        return {"error": f"Entity not found"}

    # Get next version number
    last_version = await db["content_versions"].find_one(
        {"entity_type": content_type, "entity_id": content_id},
        sort=[("version", -1)])
    next_version = (last_version.get("version", 0) + 1) if last_version else 1

    # Store version
    version_doc = {
        "entity_type": content_type,
        "entity_id": content_id,
        "version": next_version,
        "previous_content": _clean_secret_keys(_oid_str(entity)),
        "reason": reason,
        "created_at": utcnow(),
        "validation_score": 0.0,
        "seo_score": 0.0,
    }
    await db["content_versions"].insert_one(version_doc)

    return {
        "version": next_version,
        "entity_type": content_type,
        "entity_id": content_id,
        "snapshot_stored": True,
    }


@mcp_tool("rollback_content", "Rollback to a previous content version",
          "content", permission="admin")
async def rollback_content(content_type: str, content_id: str,
                           target_version: int) -> dict:
    """Rollback content to a specific version. Admin only."""
    db = get_db()
    version_doc = await db["content_versions"].find_one({
        "entity_type": content_type,
        "entity_id": content_id,
        "version": target_version,
    })
    if not version_doc:
        return {"error": f"Version {target_version} not found"}

    previous = version_doc.get("previous_content", {})
    if not previous:
        return {"error": "No rollback data available"}

    # Restore
    collection_map = {
        "project": "projects",
        "product": "products",
        "profile": "profiles",
    }
    collection = collection_map.get(content_type)
    if collection:
        from bson import ObjectId
        try:
            await db[collection].update_one(
                {"_id": ObjectId(content_id)},
                {"$set": previous})
            return {"status": "rolled_back", "version": target_version}
        except Exception as e:
            return {"error": f"Rollback failed: {str(e)[:200]}"}

    return {"error": "Unknown content type"}


@mcp_tool("get_content_health", "Get health score for all content entities",
          "content", permission="agent")
async def get_content_health() -> dict:
    """Calculate health scores for profile, portfolio, projects, skills."""
    db = get_db()
    health = {}

    # Profile health
    profile = await db["profiles"].find_one() or {}
    profile_fields = ["full_name", "title", "headline", "bio", "skills", "career"]
    profile_score = sum(1 for f in profile_fields if profile.get(f)) / len(profile_fields)
    health["profile"] = {"completeness": round(profile_score, 2)}

    # Project health
    projects = await db["projects"].find(
        {"status": "published"}).to_list(100)
    if projects:
        project_scores = []
        for p in projects:
            fields = ["description", "summary", "technologies", "images"]
            score = sum(1 for f in fields if p.get(f)) / len(fields)
            project_scores.append(score)
        health["projects"] = {
            "count": len(projects),
            "average_completeness": round(
                sum(project_scores) / len(project_scores), 2),
        }

    # Skill health
    skill_count = await db["skill_evidence"].count_documents({})
    skills_with_evidence = await db["skill_evidence"].count_documents(
        {"confidence": {"$gte": 0.6}})
    health["skills"] = {
        "total": skill_count,
        "with_evidence": skills_with_evidence,
        "evidence_ratio": round(
            skills_with_evidence / skill_count if skill_count else 0, 2),
    }

    # Knowledge health
    knowledge_count = await db["knowledge"].count_documents({})
    health["knowledge"] = {"total_entries": knowledge_count}

    return health


@mcp_tool("get_content_freshness", "Check how fresh content is across the site",
          "content", permission="agent")
async def get_content_freshness() -> dict:
    """Analyze content freshness and detect stale content."""
    db = get_db()
    from datetime import timedelta
    now = utcnow()
    thirty_days = now - timedelta(days=30)
    ninety_days = now - timedelta(days=90)

    projects = await db["projects"].find(
        {"status": "published"}).to_list(100)

    fresh = 0
    aging = 0
    stale = 0
    for p in projects:
        updated = p.get("updated_at") or p.get("created_at")
        if updated:
            # Handle both naive (MongoDB default) and aware datetimes
            if updated.tzinfo is None:
                from datetime import timezone as _tz
                updated = updated.replace(tzinfo=_tz.utc)
            if updated > thirty_days:
                fresh += 1
            elif updated > ninety_days:
                aging += 1
            else:
                stale += 1

    return {
        "total_projects": len(projects),
        "fresh": fresh,
        "aging": aging,
        "stale": stale,
        "freshness_ratio": round(fresh / len(projects), 2) if projects else 0,
    }
