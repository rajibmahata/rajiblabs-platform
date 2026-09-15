from __future__ import annotations

import logging
from typing import Any

from app.database import get_db
from app.tools import mcp_tool, _oid_str, _clean_secret_keys

logger = logging.getLogger(__name__)


@mcp_tool(
    name="list_resumes",
    description="List all resume versions with metadata. Only published resume is public-safe.",
    category="resume",
    permission="read",
)
async def list_resumes(agent_id: str = "anonymous") -> dict:
    db = get_db()
    resumes = []
    async for resume in db.resumes.find().sort("created_at", -1):
        resume["_id"] = _oid_str(resume["_id"])
        resume.pop("raw_text", None)
        resume.pop("extracted_data", None)
        resumes.append(resume)

    return {
        "success": True,
        "data": {"resumes": resumes, "count": len(resumes)},
        "sources": ["resumes"],
        "confidence": 1.0,
    }


@mcp_tool(
    name="get_resume",
    description="Get a specific resume by ID. Returns metadata only, never raw PII.",
    category="resume",
    permission="read",
)
async def get_resume(resume_id: str, agent_id: str = "anonymous") -> dict:
    db = get_db()
    from bson import ObjectId
    resume = await db.resumes.find_one({"_id": ObjectId(resume_id)})
    if not resume:
        return {"success": False, "error": {"code": "NOT_FOUND", "message": "Resume not found"}}

    resume["_id"] = _oid_str(resume["_id"])
    resume.pop("raw_text", None)
    resume = _clean_secret_keys(resume)

    return {"success": True, "data": resume, "sources": ["resumes"], "confidence": 1.0}


@mcp_tool(
    name="analyze_resume",
    description="Analyze resume for completeness, quality, and evidence of skills/projects.",
    category="resume",
    permission="analyze",
)
async def analyze_resume(agent_id: str = "anonymous") -> dict:
    db = get_db()
    resume = await db.resumes.find_one(sort=[("created_at", -1)])
    if not resume:
        return {"success": False, "error": {"code": "NOT_FOUND", "message": "No resume found"}}

    extraction = await db.resume_extractions.find_one(
        {"resume_id": str(resume["_id"])}
    )

    analysis = {
        "resume_id": _oid_str(resume["_id"]),
        "filename": resume.get("filename", ""),
        "has_extraction": extraction is not None,
        "skills_found": len(extraction.get("skills", [])) if extraction else 0,
        "projects_found": len(extraction.get("projects", [])) if extraction else 0,
        "experience_found": len(extraction.get("experience", [])) if extraction else 0,
    }

    return {
        "success": True,
        "data": analysis,
        "sources": ["resumes", "resume_extractions"],
        "confidence": 0.9,
    }


@mcp_tool(
    name="extract_resume_experience",
    description="Extract work experience entries from resume.",
    category="resume",
    permission="analyze",
)
async def extract_resume_experience(agent_id: str = "anonymous") -> dict:
    db = get_db()
    extraction = await db.resume_extractions.find_one(sort=[("created_at", -1)])
    if not extraction:
        return {"success": False, "error": {"code": "NOT_FOUND", "message": "No resume extraction found"}}

    return {
        "success": True,
        "data": {"experience": extraction.get("experience", [])},
        "sources": ["resume_extractions"],
        "confidence": 0.85,
    }


@mcp_tool(
    name="extract_resume_skills",
    description="Extract skills from resume with evidence.",
    category="resume",
    permission="analyze",
)
async def extract_resume_skills(agent_id: str = "anonymous") -> dict:
    db = get_db()
    extraction = await db.resume_extractions.find_one(sort=[("created_at", -1)])
    if not extraction:
        return {"success": False, "error": {"code": "NOT_FOUND", "message": "No resume extraction found"}}

    return {
        "success": True,
        "data": {"skills": extraction.get("skills", [])},
        "sources": ["resume_extractions"],
        "confidence": 0.85,
    }


@mcp_tool(
    name="extract_resume_projects",
    description="Extract project entries from resume.",
    category="resume",
    permission="analyze",
)
async def extract_resume_projects(agent_id: str = "anonymous") -> dict:
    db = get_db()
    extraction = await db.resume_extractions.find_one(sort=[("created_at", -1)])
    if not extraction:
        return {"success": False, "error": {"code": "NOT_FOUND", "message": "No resume extraction found"}}

    return {
        "success": True,
        "data": {"projects": extraction.get("projects", [])},
        "sources": ["resume_extractions"],
        "confidence": 0.85,
    }


@mcp_tool(
    name="compare_resume_versions",
    description="Compare two resume versions to detect changes in skills, experience, and projects.",
    category="resume",
    permission="analyze",
)
async def compare_resume_versions(
    resume_id_1: str, resume_id_2: str, agent_id: str = "anonymous"
) -> dict:
    db = get_db()
    from bson import ObjectId

    r1 = await db.resumes.find_one({"_id": ObjectId(resume_id_1)})
    r2 = await db.resumes.find_one({"_id": ObjectId(resume_id_2)})
    if not r1 or not r2:
        return {"success": False, "error": {"code": "NOT_FOUND", "message": "One or both resumes not found"}}

    e1 = await db.resume_extractions.find_one({"resume_id": resume_id_1})
    e2 = await db.resume_extractions.find_one({"resume_id": resume_id_2})

    s1 = set(e1.get("skills", [])) if e1 else set()
    s2 = set(e2.get("skills", [])) if e2 else set()

    return {
        "success": True,
        "data": {
            "resume_1": resume_id_1,
            "resume_2": resume_id_2,
            "skills_added": list(s2 - s1),
            "skills_removed": list(s1 - s2),
            "skills_common": list(s1 & s2),
        },
        "sources": ["resumes", "resume_extractions"],
        "confidence": 0.9,
    }


@mcp_tool(
    name="sync_resume_to_knowledge",
    description="Sync resume skills and experience into the knowledge base for RAG retrieval.",
    category="resume",
    permission="write",
)
async def sync_resume_to_knowledge(agent_id: str = "anonymous") -> dict:
    db = get_db()
    extraction = await db.resume_extractions.find_one(sort=[("created_at", -1)])
    if not extraction:
        return {"success": False, "error": {"code": "NOT_FOUND", "message": "No resume extraction found"}}

    synced = 0
    for skill in extraction.get("skills", []):
        existing = await db.knowledge_documents.find_one(
            {"content": {"$regex": skill, "$options": "i"}, "source_type": "resume"}
        )
        if not existing:
            await db.knowledge_documents.insert_one({
                "content": f"Skill from resume: {skill}",
                "source_type": "resume",
                "category": "skills",
                "created_at": __import__("datetime").datetime.utcnow(),
            })
            synced += 1

    return {
        "success": True,
        "data": {"synced_count": synced},
        "sources": ["resume_extractions", "knowledge_documents"],
        "confidence": 0.9,
    }
