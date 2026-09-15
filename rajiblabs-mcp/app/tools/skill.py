from __future__ import annotations

import logging
from typing import Any

from app.database import get_db
from app.tools import mcp_tool, _oid_str, _normalize_skill_category, KNOWN_SKILLS
from app.cache import cache_get, cache_set

logger = logging.getLogger(__name__)


@mcp_tool(
    name="discover_skills",
    description="Discover skills from all sources: projects, GitHub, resume, knowledge base.",
    category="skill",
    permission="analyze",
)
async def discover_skills(agent_id: str = "anonymous") -> dict:
    db = get_db()

    project_skills = set()
    async for proj in db.projects.find({"status": "published"}):
        for s in proj.get("skills", []):
            project_skills.add(s.lower().strip())

    github_skills = set()
    async for repo in db.github_repositories.find():
        for lang in repo.get("languages", []):
            github_skills.add(lang.lower().strip())
        for topic in repo.get("topics", []):
            github_skills.add(topic.lower().strip())

    db_skills = set()
    async for skill in db.skills.find():
        db_skills.add(skill.get("name", "").lower().strip())

    all_skills = project_skills | github_skills | db_skills

    discovered = []
    for skill_name in all_skills:
        info = KNOWN_SKILLS.get(skill_name, {})
        discovered.append({
            "name": skill_name,
            "category": info.get("category", "unknown"),
            "family": info.get("family", "unknown"),
            "sources": {
                "projects": skill_name in project_skills,
                "github": skill_name in github_skills,
                "database": skill_name in db_skills,
            },
        })

    return {
        "success": True,
        "data": {"skills": discovered, "total": len(discovered)},
        "sources": ["projects", "github_repositories", "skills"],
        "confidence": 0.85,
    }


@mcp_tool(
    name="normalize_skill",
    description="Normalize a skill name to canonical form with category.",
    category="skill",
    permission="analyze",
)
async def normalize_skill(skill_name: str, agent_id: str = "anonymous") -> dict:
    normalized = skill_name.lower().strip()
    info = KNOWN_SKILLS.get(normalized, {})

    return {
        "success": True,
        "data": {
            "original": skill_name,
            "normalized": normalized,
            "category": info.get("category", "unknown"),
            "family": info.get("family", "unknown"),
            "is_known": bool(info),
        },
        "sources": ["skill_registry"],
        "confidence": 1.0,
    }


@mcp_tool(
    name="validate_skill",
    description="Validate a skill has proper evidence and is not fabricated.",
    category="skill",
    permission="analyze",
)
async def validate_skill(skill_name: str, agent_id: str = "anonymous") -> dict:
    db = get_db()
    evidence = []

    project_count = await db.projects.count_documents({"skills": {"$regex": skill_name, "$options": "i"}})
    if project_count > 0:
        evidence.append({"source": "projects", "count": project_count})

    repo_count = await db.github_repositories.count_documents(
        {"$or": [{"languages": {"$regex": skill_name, "$options": "i"}}, {"topics": {"$regex": skill_name, "$options": "i"}}]}
    )
    if repo_count > 0:
        evidence.append({"source": "github_repositories", "count": repo_count})

    skill_doc = await db.skills.find_one({"name": {"$regex": f"^{skill_name}$", "$options": "i"}})
    if skill_doc:
        evidence.append({"source": "skills_database", "count": 1})

    resume_count = await db.resume_extractions.count_documents(
        {"skills": {"$regex": skill_name, "$options": "i"}}
    )
    if resume_count > 0:
        evidence.append({"source": "resume", "count": resume_count})

    total_evidence = sum(e["count"] for e in evidence)
    validated = total_evidence >= 1

    return {
        "success": True,
        "data": {
            "skill": skill_name,
            "validated": validated,
            "evidence_count": total_evidence,
            "evidence": evidence,
        },
        "sources": ["projects", "github_repositories", "skills", "resume_extractions"],
        "confidence": 0.9 if validated else 0.3,
    }


@mcp_tool(
    name="get_skill_evidence",
    description="Get all evidence for a skill across projects, GitHub, resume, and knowledge.",
    category="skill",
    permission="read",
)
async def get_skill_evidence(skill_name: str, agent_id: str = "anonymous") -> dict:
    db = get_db()

    projects = []
    async for proj in db.projects.find({"skills": {"$regex": skill_name, "$options": "i"}}):
        projects.append({"id": _oid_str(proj["_id"]), "title": proj.get("title", "")})

    repositories = []
    async for repo in db.github_repositories.find(
        {"$or": [{"languages": {"$regex": skill_name, "$options": "i"}}, {"topics": {"$regex": skill_name, "$options": "i"}}]}
    ):
        repositories.append({"id": _oid_str(repo["_id"]), "name": repo.get("name", "")})

    return {
        "success": True,
        "data": {
            "skill": skill_name,
            "projects": projects,
            "repositories": repositories,
            "total_evidence": len(projects) + len(repositories),
        },
        "sources": ["projects", "github_repositories"],
        "confidence": 0.9,
    }


@mcp_tool(
    name="link_skill_to_project",
    description="Link a skill to a project.",
    category="skill",
    permission="write",
)
async def link_skill_to_project(
    skill_name: str, project_id: str, agent_id: str = "anonymous"
) -> dict:
    db = get_db()
    from bson import ObjectId

    await db.projects.update_one(
        {"_id": ObjectId(project_id)},
        {"$addToSet": {"skills": skill_name}},
    )

    return {
        "success": True,
        "data": {"skill": skill_name, "project_id": project_id},
        "sources": ["projects"],
        "changed": True,
        "confidence": 1.0,
    }


@mcp_tool(
    name="link_skill_to_repository",
    description="Link a skill to a GitHub repository.",
    category="skill",
    permission="write",
)
async def link_skill_to_repository(
    skill_name: str, repository_id: str, agent_id: str = "anonymous"
) -> dict:
    db = get_db()
    from bson import ObjectId

    repo = await db.github_repositories.find_one({"_id": ObjectId(repository_id)})
    if not repo:
        return {"success": False, "error": {"code": "NOT_FOUND", "message": "Repository not found"}}

    existing_topics = repo.get("topics", [])
    if skill_name.lower() not in [t.lower() for t in existing_topics]:
        await db.github_repositories.update_one(
            {"_id": ObjectId(repository_id)},
            {"$push": {"topics": skill_name}},
        )

    return {
        "success": True,
        "data": {"skill": skill_name, "repository_id": repository_id},
        "sources": ["github_repositories"],
        "changed": True,
        "confidence": 1.0,
    }


@mcp_tool(
    name="link_skill_to_resume",
    description="Link a skill to the resume.",
    category="skill",
    permission="write",
)
async def link_skill_to_resume(skill_name: str, agent_id: str = "anonymous") -> dict:
    db = get_db()
    extraction = await db.resume_extractions.find_one(sort=[("created_at", -1)])
    if not extraction:
        return {"success": False, "error": {"code": "NOT_FOUND", "message": "No resume extraction found"}}

    existing = extraction.get("skills", [])
    if skill_name not in existing:
        await db.resume_extractions.update_one(
            {"_id": extraction["_id"]},
            {"$push": {"skills": skill_name}},
        )

    return {
        "success": True,
        "data": {"skill": skill_name, "resume_id": _oid_str(extraction["_id"])},
        "sources": ["resume_extractions"],
        "changed": True,
        "confidence": 1.0,
    }


@mcp_tool(
    name="get_skill_relationships",
    description="Get all relationships for a skill: projects, repositories, products, domains.",
    category="skill",
    permission="read",
)
async def get_skill_relationships(skill_name: str, agent_id: str = "anonymous") -> dict:
    db = get_db()

    projects = []
    async for proj in db.projects.find({"skills": {"$regex": skill_name, "$options": "i"}}):
        projects.append({"id": _oid_str(proj["_id"]), "title": proj.get("title", "")})

    repos = []
    async for repo in db.github_repositories.find(
        {"$or": [{"languages": {"$regex": skill_name, "$options": "i"}}, {"topics": {"$regex": skill_name, "$options": "i"}}]}
    ):
        repos.append({"id": _oid_str(repo["_id"]), "name": repo.get("name", "")})

    return {
        "success": True,
        "data": {
            "skill": skill_name,
            "projects": projects,
            "repositories": repos,
        },
        "sources": ["projects", "github_repositories"],
        "confidence": 0.9,
    }
