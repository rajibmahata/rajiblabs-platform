"""Skill Intelligence MCP tools — automatic skill discovery and organization.

Skills are extracted from resume, GitHub, projects, and experience.
Every skill has evidence and confidence score. Never invent skills.
"""

import re
from datetime import datetime, timezone

from app.database import get_db, utcnow
from app.tools import (
    mcp_tool, _oid_str, _clean_secret_keys,
    _normalize_skill_category, KNOWN_SKILLS,
)


@mcp_tool("get_skills", "Get all skills with evidence and categories",
          "skill", permission="public")
async def get_skills(category: str | None = None) -> dict:
    """Return skills organized by category with evidence."""
    db = get_db()
    query = {}
    if category:
        query["category"] = {"$regex": f"^{re.escape(category)}$", "$options": "i"}

    skills = await db["skill_evidence"].find(query).sort(
        "confidence", -1).to_list(200)

    # Group by category
    by_category = {}
    for s in skills:
        cat = s.get("category", "Other")
        by_category.setdefault(cat, []).append(_oid_str(s))

    return {
        "skills": [_oid_str(s) for s in skills],
        "by_category": by_category,
        "total": len(skills),
    }


@mcp_tool("extract_skills", "Extract skills from resume, projects, and GitHub",
          "skill", permission="agent")
async def extract_skills() -> dict:
    """Discover and normalize skills from all available evidence sources."""
    db = get_db()
    extracted = {}  # skill_name -> {category, confidence, evidence}

    # ── Source 1: Resume ──
    resume = await db["resumes"].find_one({"status": "active"}) or {}
    resume_skills = resume.get("skills", []) or []
    for skill in resume_skills:
        name = skill if isinstance(skill, str) else skill.get("name", "")
        if not name:
            continue
        key = name.lower().strip()
        if key not in extracted:
            info = KNOWN_SKILLS.get(key, {})
            extracted[key] = {
                "skill": name,
                "category": _normalize_skill_category(
                    info.get("category", "Other")),
                "confidence": 0.9,
                "evidence": ["resume"],
                "related_projects": [],
                "related_repositories": [],
            }
        else:
            extracted[key]["confidence"] = min(1.0, extracted[key]["confidence"] + 0.1)
            if "resume" not in extracted[key]["evidence"]:
                extracted[key]["evidence"].append("resume")

    # ── Source 2: Historical Resumes ──
    historical = await db["resumes"].find(
        {"status": {"$ne": "active"}}).to_list(20)
    for h in historical:
        for skill in (h.get("skills") or []):
            name = skill if isinstance(skill, str) else skill.get("name", "")
            if not name:
                continue
            key = name.lower().strip()
            if key not in extracted:
                info = KNOWN_SKILLS.get(key, {})
                extracted[key] = {
                    "skill": name,
                    "category": _normalize_skill_category(
                        info.get("category", "Other")),
                    "confidence": 0.7,
                    "evidence": ["historical_resume"],
                    "related_projects": [],
                    "related_repositories": [],
                }
            else:
                if "historical_resume" not in extracted[key]["evidence"]:
                    extracted[key]["evidence"].append("historical_resume")
                    extracted[key]["confidence"] = min(
                        1.0, extracted[key]["confidence"] + 0.05)

    # ── Source 3: Projects ──
    projects = await db["projects"].find(
        {"status": "published"}).to_list(100)
    for p in projects:
        techs = p.get("technologies", []) or p.get("tech_stack", [])
        title = p.get("title", "")
        for t in techs:
            name = str(t).strip()
            if not name:
                continue
            key = name.lower()
            if key not in extracted:
                info = KNOWN_SKILLS.get(key, {})
                extracted[key] = {
                    "skill": name,
                    "category": _normalize_skill_category(
                        info.get("category", "Other")),
                    "confidence": 0.8,
                    "evidence": [f"project:{title}"],
                    "related_projects": [title],
                    "related_repositories": [],
                }
            else:
                extracted[key]["confidence"] = min(
                    1.0, extracted[key]["confidence"] + 0.05)
                if f"project:{title}" not in extracted[key]["evidence"]:
                    extracted[key]["evidence"].append(f"project:{title}")
                if title not in extracted[key]["related_projects"]:
                    extracted[key]["related_projects"].append(title)

    # ── Source 4: GitHub Repositories ──
    repos = await db["github_repositories"].find({}).to_list(100)
    for r in repos:
        lang = r.get("language", "")
        topics = r.get("topics", []) or []
        name = r.get("name", "")
        all_techs = [lang] + topics
        for t in all_techs:
            if not t:
                continue
            key = str(t).lower().strip()
            if key not in extracted:
                info = KNOWN_SKILLS.get(key, {})
                extracted[key] = {
                    "skill": str(t),
                    "category": _normalize_skill_category(
                        info.get("category", "Other")),
                    "confidence": 0.75,
                    "evidence": [f"github:{name}"],
                    "related_projects": [],
                    "related_repositories": [name],
                }
            else:
                if f"github:{name}" not in extracted[key]["evidence"]:
                    extracted[key]["evidence"].append(f"github:{name}")
                if name not in extracted[key]["related_repositories"]:
                    extracted[key]["related_repositories"].append(name)
                extracted[key]["confidence"] = min(
                    1.0, extracted[key]["confidence"] + 0.03)

    # ── Source 5: Career Experience ──
    profile = await db["profiles"].find_one() or {}
    for c in (profile.get("career") or []):
        techs = c.get("tech_stack", []) or c.get("technologies", [])
        role = c.get("role", "")
        for t in techs:
            name = str(t).strip()
            if not name:
                continue
            key = name.lower()
            if key not in extracted:
                info = KNOWN_SKILLS.get(key, {})
                extracted[key] = {
                    "skill": name,
                    "category": _normalize_skill_category(
                        info.get("category", "Other")),
                    "confidence": 0.85,
                    "evidence": [f"career:{role}"],
                    "related_projects": [],
                    "related_repositories": [],
                }
            else:
                if f"career:{role}" not in extracted[key]["evidence"]:
                    extracted[key]["evidence"].append(f"career:{role}")
                extracted[key]["confidence"] = min(
                    1.0, extracted[key]["confidence"] + 0.05)

    # ── Persist ──
    upserted = 0
    for key, skill_data in extracted.items():
        existing = await db["skill_evidence"].find_one(
            {"skill": {"$regex": f"^{re.escape(skill_data['skill'])}$",
                        "$options": "i"}})
        if existing:
            # Merge evidence
            all_evidence = list(set(
                (existing.get("evidence") or []) + skill_data["evidence"]))
            all_projects = list(set(
                (existing.get("related_projects") or []) +
                skill_data["related_projects"]))
            all_repos = list(set(
                (existing.get("related_repositories") or []) +
                skill_data["related_repositories"]))
            await db["skill_evidence"].update_one(
                {"_id": existing["_id"]},
                {"$set": {
                    "confidence": max(existing.get("confidence", 0),
                                      skill_data["confidence"]),
                    "evidence": all_evidence,
                    "related_projects": all_projects,
                    "related_repositories": all_repos,
                    "last_updated": utcnow(),
                }})
        else:
            skill_data["first_seen"] = utcnow()
            skill_data["last_updated"] = utcnow()
            await db["skill_evidence"].insert_one(skill_data)
        upserted += 1

    return {
        "total_extracted": len(extracted),
        "upserted": upserted,
        "sources_used": ["resume", "historical_resumes", "projects",
                         "github", "career"],
        "categories": list(set(s["category"] for s in extracted.values())),
    }


@mcp_tool("validate_skill", "Validate a skill claim against evidence",
          "skill", permission="agent")
async def validate_skill(skill_name: str) -> dict:
    """Check if a skill claim is supported by evidence."""
    db = get_db()
    evidence = await db["skill_evidence"].find_one(
        {"skill": {"$regex": f"^{re.escape(skill_name)}$", "$options": "i"}})

    if not evidence:
        return {
            "skill": skill_name,
            "valid": False,
            "confidence": 0.0,
            "evidence_count": 0,
            "message": "No evidence found for this skill",
        }

    return {
        "skill": evidence.get("skill", skill_name),
        "valid": evidence.get("confidence", 0) >= 0.6,
        "confidence": evidence.get("confidence", 0),
        "category": evidence.get("category", ""),
        "evidence_count": len(evidence.get("evidence", [])),
        "evidence": evidence.get("evidence", []),
        "related_projects": evidence.get("related_projects", []),
        "related_repositories": evidence.get("related_repositories", []),
    }
