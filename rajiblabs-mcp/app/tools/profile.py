"""Profile MCP tools — evidence-backed professional profile management.

Tools for getting, analyzing, validating, and optimizing the RajibLabs
professional profile. Every major claim must have evidence.
"""

from datetime import datetime, timezone

from app.database import get_db, utcnow
from app.tools import (
    mcp_tool, _oid_str, _clean_secret_keys, _normalize_skill_category,
    KNOWN_SKILLS,
)


@mcp_tool("get_profile", "Get the complete RajibLabs professional profile",
          "profile", permission="public")
async def get_profile() -> dict:
    """Return the full profile with evidence."""
    db = get_db()
    profile = await db["profiles"].find_one() or {}
    if not profile:
        return {"error": "No profile found", "profile": None}

    # Enrich with skill evidence
    skills_with_evidence = []
    for skill_name in profile.get("skills", []):
        evidence_doc = await db["skill_evidence"].find_one(
            {"skill": {"$regex": f"^{skill_name}$", "$options": "i"}})
        if evidence_doc:
            skills_with_evidence.append(_oid_str(evidence_doc))
        else:
            skills_with_evidence.append({"skill": skill_name, "confidence": 0.5})

    result = _oid_str(profile)
    result["skills_with_evidence"] = skills_with_evidence
    return _clean_secret_keys(result)


@mcp_tool("analyze_profile", "Analyze profile completeness and evidence quality",
          "profile", permission="agent")
async def analyze_profile() -> dict:
    """Analyze profile for completeness, evidence, and issues."""
    db = get_db()
    profile = await db["profiles"].find_one() or {}
    if not profile:
        return {"error": "No profile found", "completeness": 0}

    issues = []
    recommendations = []
    evidence_count = 0

    # Check required fields
    required_fields = [
        ("full_name", "Full name"),
        ("title", "Professional title"),
        ("headline", "Headline"),
        ("bio", "Bio/About"),
        ("location", "Location"),
    ]
    present = 0
    for field, label in required_fields:
        if profile.get(field):
            present += 1
        else:
            issues.append(f"Missing {label}")
            recommendations.append(f"Add {label} to profile")

    # Check skills
    skills = profile.get("skills", [])
    if len(skills) < 5:
        issues.append(f"Only {len(skills)} skills listed (recommended: 15+)")
        recommendations.append("Add more verified skills")

    # Check career
    career = profile.get("career", [])
    if not career:
        issues.append("No career history")
        recommendations.append("Add professional experience")

    # Check social links
    links = profile.get("social_links", {})
    if not links.get("github"):
        issues.append("No GitHub link")
    if not links.get("linkedin"):
        issues.append("No LinkedIn link")

    # Count evidence
    evidence_count = await db["skill_evidence"].count_documents({})

    # Check projects
    projects = await db["projects"].count_documents({"status": "published"})
    if projects == 0:
        issues.append("No published projects")
        recommendations.append("Add portfolio projects")

    completeness = present / len(required_fields) if required_fields else 0
    completeness = min(1.0, (completeness * 0.4 +
                             (min(len(skills), 20) / 20) * 0.3 +
                             (min(projects, 10) / 10) * 0.3))

    return {
        "completeness": round(completeness, 2),
        "total_skills": len(skills),
        "total_career_entries": len(career),
        "total_projects": projects,
        "evidence_count": evidence_count,
        "social_links": list(links.keys()),
        "issues": issues,
        "recommendations": recommendations,
    }


@mcp_tool("validate_profile", "Validate profile for factual accuracy",
          "profile", permission="agent")
async def validate_profile() -> dict:
    """Validate profile claims against evidence."""
    db = get_db()
    profile = await db["profiles"].find_one() or {}
    if not profile:
        return {"error": "No profile found", "valid": False}

    validations = []
    warnings = []

    # Validate skills against evidence
    skills = profile.get("skills", [])
    skills_with_evidence = 0
    for skill in skills:
        evidence = await db["skill_evidence"].find_one(
            {"skill": {"$regex": f"^{skill}$", "$options": "i"}})
        if evidence and evidence.get("confidence", 0) >= 0.6:
            skills_with_evidence += 1
        else:
            warnings.append(f"Skill '{skill}' lacks sufficient evidence")

    # Validate career claims
    career = profile.get("career", [])
    for entry in career:
        if entry.get("achievements"):
            validations.append(
                f"Career '{entry.get('role', '')}' has {len(entry['achievements'])} achievements")

    # Validate projects
    projects_count = await db["projects"].count_documents({"status": "published"})
    validations.append(f"{projects_count} published projects verified in database")

    skill_evidence_ratio = (skills_with_evidence / len(skills)
                            if skills else 0)

    return {
        "valid": len(warnings) == 0,
        "skill_evidence_ratio": round(skill_evidence_ratio, 2),
        "skills_with_evidence": skills_with_evidence,
        "total_skills": len(skills),
        "validations": validations,
        "warnings": warnings[:20],
    }


@mcp_tool("optimize_profile", "Optimize profile presentation for clarity",
          "profile", permission="agent")
async def optimize_profile() -> dict:
    """Suggest optimizations for profile clarity and impact."""
    db = get_db()
    profile = await db["profiles"].find_one() or {}
    if not profile:
        return {"error": "No profile found"}

    optimizations = []

    # Analyze headline
    headline = profile.get("headline", "")
    if headline and len(headline) > 120:
        optimizations.append({
            "field": "headline",
            "issue": "Headline too long",
            "suggestion": f"Shorten from {len(headline)} to under 120 characters",
        })

    # Analyze bio
    bio = profile.get("bio", "")
    if bio and len(bio) < 100:
        optimizations.append({
            "field": "bio",
            "issue": "Bio too short",
            "suggestion": "Expand bio to 200-500 characters for better impact",
        })

    # Analyze skills organization
    skills = profile.get("skills", [])
    if skills:
        categorized = {}
        for skill in skills:
            evidence = None
            # Check known skills
            skill_lower = skill.lower()
            for known, info in KNOWN_SKILLS.items():
                if skill_lower == known or skill_lower in info.get("aliases", []):
                    cat = _normalize_skill_category(info["category"])
                    categorized.setdefault(cat, []).append(skill)
                    break
            else:
                categorized.setdefault("Other", []).append(skill)

        optimizations.append({
            "field": "skills_organization",
            "issue": "Skills can be better organized",
            "suggestion": f"Organize {len(skills)} skills into {len(categorized)} categories",
            "categories": categorized,
        })

    # Check for missing professional positioning
    positioning_keywords = [
        "solution architect", "software engineer", ".net", "azure",
        "ai", "agentic", "cloud", "enterprise"
    ]
    all_text = f"{profile.get('title', '')} {profile.get('headline', '')} {profile.get('bio', '')}".lower()
    missing_positioning = [kw for kw in positioning_keywords if kw not in all_text]
    if missing_positioning:
        optimizations.append({
            "field": "professional_positioning",
            "issue": "Missing key positioning keywords",
            "suggestion": f"Consider incorporating: {', '.join(missing_positioning)}",
        })

    return {
        "optimization_count": len(optimizations),
        "optimizations": optimizations,
    }


@mcp_tool("get_professional_positioning",
          "Get evidence-backed professional positioning statement",
          "profile", permission="public")
async def get_professional_positioning() -> dict:
    """Return professional positioning backed by evidence."""
    db = get_db()
    profile = await db["profiles"].find_one() or {}
    if not profile:
        return {"error": "No profile found"}

    # Gather evidence from multiple sources
    career = profile.get("career", [])
    projects = await db["projects"].find(
        {"status": "published"}).to_list(50)
    skills = profile.get("skills", [])

    # Build positioning claims with evidence
    claims = []

    # Solution Architect
    arch_evidence = []
    for p in projects:
        desc = (p.get("description", "") + " " + p.get("summary", "")).lower()
        if any(kw in desc for kw in ["architecture", "architect", "microservices", "system design"]):
            arch_evidence.append(f"project:{p.get('title', '')}")
    for c in career:
        role = (c.get("role", "") or "").lower()
        if "architect" in role:
            arch_evidence.append(f"career:{c.get('role', '')}")
    if arch_evidence:
        claims.append({
            "claim": "Solution Architect",
            "confidence": min(1.0, len(arch_evidence) * 0.3),
            "evidence": arch_evidence[:5],
        })

    # .NET Expert
    dotnet_evidence = []
    for p in projects:
        tech = str(p.get("technologies", []) or p.get("tech_stack", [])).lower()
        if ".net" in tech or "c#" in tech or "asp.net" in tech:
            dotnet_evidence.append(f"project:{p.get('title', '')}")
    for c in career:
        tech = str(c.get("tech_stack", []) or c.get("technologies", [])).lower()
        if ".net" in tech or "c#" in tech:
            dotnet_evidence.append(f"career:{c.get('role', '')}")
    if dotnet_evidence:
        claims.append({
            "claim": ".NET Technology Expertise",
            "confidence": min(1.0, len(dotnet_evidence) * 0.25),
            "evidence": dotnet_evidence[:5],
        })

    # Azure Cloud
    azure_evidence = []
    for p in projects:
        tech = str(p.get("technologies", []) or p.get("tech_stack", [])).lower()
        desc = (p.get("description", "") + " " + p.get("summary", "")).lower()
        if "azure" in tech or "azure" in desc:
            azure_evidence.append(f"project:{p.get('title', '')}")
    if azure_evidence:
        claims.append({
            "claim": "Azure Cloud / PaaS",
            "confidence": min(1.0, len(azure_evidence) * 0.25),
            "evidence": azure_evidence[:5],
        })

    # AI Engineering
    ai_evidence = []
    for p in projects:
        tech = str(p.get("technologies", []) or p.get("tech_stack", [])).lower()
        desc = (p.get("description", "") + " " + p.get("summary", "")).lower()
        if any(kw in tech or kw in desc for kw in ["ai", "openai", "llm", "rag", "ml"]):
            ai_evidence.append(f"project:{p.get('title', '')}")
    if ai_evidence:
        claims.append({
            "claim": "AI Engineering / Agentic AI",
            "confidence": min(1.0, len(ai_evidence) * 0.3),
            "evidence": ai_evidence[:5],
        })

    return {
        "positioning_claims": claims,
        "total_evidence_sources": sum(len(c["evidence"]) for c in claims),
        "overall_confidence": (sum(c["confidence"] for c in claims) / len(claims)
                               if claims else 0),
    }
