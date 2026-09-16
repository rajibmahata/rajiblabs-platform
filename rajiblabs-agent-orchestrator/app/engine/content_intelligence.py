"""Content intelligence engine — evidence-first content analysis and improvement."""

from __future__ import annotations

import logging
import re
from typing import Any

from app.mcp_client import mcp_client
from app.models import EvidenceSource, ContentImprovement

logger = logging.getLogger(__name__)

GENERIC_FILLERS = [
    r"(?i)\b(powerful|innovative|cutting.edge|seamless|robust|scalable|state.of.the.art|world.class|best.in.class|next.generation|revolutionary|transformative)\b",
    r"(?i)\b(leverages?|utilizes?|employs?|harnesses?)\s+(modern|advanced|powerful|innovative|latest)\b",
    r"(?i)\b(comprehensive|holistic|end.to.end|full.stack|enterprise.grade|mission.critical)\b",
    r"(?i)\bthis (is a )?powerful\b",
    r"(?i)\bprovides?\s+(seamless|intuitive|powerful)\b",
]

MISSING_FIELD_PATTERNS = {
    "project": ["description", "problem", "solution", "role", "skills", "architecture", "business_value"],
    "profile": ["about", "tagline", "skills", "experience_years"],
    "product": ["description", "features", "tech_stack"],
}


async def gather_evidence(entity_type: str, entity_id: str) -> list[EvidenceSource]:
    sources: list[EvidenceSource] = []

    result = await mcp_client.call_tool("get_project", {"project_id": entity_id})
    if result.get("success"):
        sources.append(EvidenceSource(
            source_type="project",
            source_id=entity_id,
            content=str(result.get("data", {})),
            confidence=1.0,
        ))

    if entity_type == "project":
        skills_result = await mcp_client.call_tool("discover_skills")
        if skills_result.get("success"):
            sources.append(EvidenceSource(
                source_type="skills",
                content=str(skills_result.get("data", {})),
                confidence=0.8,
            ))

        repos_result = await mcp_client.call_tool("list_repositories")
        if repos_result.get("success"):
            sources.append(EvidenceSource(
                source_type="github",
                content=str(repos_result.get("data", {})),
                confidence=0.9,
            ))

    knowledge_result = await mcp_client.call_tool(
        "search_knowledge", {"query": f"{entity_type} {entity_id}"}
    )
    if knowledge_result.get("success") and knowledge_result.get("data", {}).get("results"):
        sources.append(EvidenceSource(
            source_type="knowledge",
            content=str(knowledge_result["data"]["results"]),
            confidence=0.7,
        ))

    return sources


def detect_generic_content(text: str) -> list[str]:
    issues = []
    for pattern in GENERIC_FILLERS:
        matches = re.findall(pattern, text)
        for m in matches:
            issues.append(f"Generic filler: '{m}'")
    return issues


def detect_missing_fields(content: dict, entity_type: str) -> list[str]:
    required = MISSING_FIELD_PATTERNS.get(entity_type, [])
    return [f for f in required if not content.get(f)]


def detect_weak_content(content: dict, entity_type: str) -> list[dict[str, Any]]:
    weaknesses = []

    for field in ["description", "problem", "solution", "about"]:
        text = content.get(field, "")
        if text and len(text) < 50:
            weaknesses.append({
                "field": field,
                "issue": "too_short",
                "current_length": len(text),
                "recommendation": f"Expand {field} to at least 100 words",
            })
        if text:
            generic = detect_generic_content(text)
            if generic:
                weaknesses.append({
                    "field": field,
                    "issue": "generic_content",
                    "count": len(generic),
                    "recommendation": f"Replace generic language in {field}",
                })

    missing = detect_missing_fields(content, entity_type)
    for f in missing:
        weaknesses.append({
            "field": f,
            "issue": "missing",
            "recommendation": f"Add {f}",
        })

    return weaknesses


async def analyze_content_quality(
    entity_type: str, entity_id: str
) -> dict[str, Any]:
    result = await mcp_client.call_tool(
        f"get_{'project' if entity_type == 'project' else entity_type}",
        {f"{'project_id' if entity_type == 'project' else entity_type + '_id'}": entity_id} if entity_type != "profile" else {},
    )

    if not result.get("success"):
        return {"success": False, "error": "Entity not found"}

    content = result.get("data", {})
    evidence = await gather_evidence(entity_type, entity_id)
    weaknesses = detect_weak_content(content, entity_type)

    return {
        "success": True,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "content": content,
        "evidence_count": len(evidence),
        "weaknesses": weaknesses,
        "weakness_count": len(weaknesses),
    }


async def improve_content(
    entity_type: str,
    entity_id: str,
    evidence: list[EvidenceSource] | None = None,
    audience: str = "technical",
) -> ContentImprovement | None:
    analysis = await analyze_content_quality(entity_type, entity_id)
    if not analysis.get("success"):
        return None

    content = analysis["content"]
    evidence = evidence or await gather_evidence(entity_type, entity_id)

    improved = dict(content)
    weaknesses = analysis.get("weaknesses", [])

    for w in weaknesses:
        field = w.get("field", "")
        if w.get("issue") == "missing" and field:
            improved[field] = f"[NEEDS CONTENT] {field} — evidence available from {len(evidence)} sources"
        elif w.get("issue") == "generic_content":
            text = improved.get(field, "")
            for pattern in GENERIC_FILLERS:
                text = re.sub(pattern, "", text)
            improved[field] = text.strip()

    return ContentImprovement(
        entity_type=entity_type,
        entity_id=entity_id,
        before=content,
        after=improved,
        why_changed=f"Addressed {len(weaknesses)} weaknesses detected in content analysis",
        evidence=evidence,
        agent="content_intelligence",
    )
