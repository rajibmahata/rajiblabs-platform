"""GitHub MCP tools — repository analysis and evidence extraction.

Uses existing GitHub integration. Analyzes repos for skills, technologies,
architecture, and project purpose. Never ingests secrets or private data.
"""

import re
from datetime import datetime, timezone

from app.database import get_db, utcnow
from app.tools import mcp_tool, _oid_str, _clean_secret_keys


# Files/patterns to never ingest
_BLOCKED_PATTERNS = re.compile(
    r"(?i)(\.env|credentials|tokens?|secrets?|password|private[_-]?key|"
    r"\.git/|node_modules/|dist/|build/|coverage/|__pycache__|"
    r"\.pyc|\.dll|\.exe|\.so|\.dylib|binaries?)")


@mcp_tool("get_repositories", "Get all synced GitHub repositories",
          "github", permission="public")
async def get_repositories(owner: str | None = None) -> dict:
    """Return GitHub repositories from the database."""
    db = get_db()
    query = {}
    if owner:
        query["owner"] = owner
    repos = await db["github_repositories"].find(query).sort(
        "stargazers_count", -1).to_list(100)
    return {"repositories": [_clean_secret_keys(_oid_str(r)) for r in repos],
            "count": len(repos)}


@mcp_tool("analyze_repository", "Analyze a repository for skills and technologies",
          "github", permission="agent")
async def analyze_repository(repo_name: str) -> dict:
    """Analyze a repository to extract skills, technologies, and purpose."""
    db = get_db()
    repo = await db["github_repositories"].find_one({"name": repo_name})
    if not repo:
        return {"error": f"Repository not found: {repo_name}"}

    analysis = {
        "name": repo.get("name", ""),
        "description": repo.get("description", ""),
        "language": repo.get("language", ""),
        "topics": repo.get("topics", []),
        "technologies": [],
        "skills_extracted": [],
        "architecture_signals": [],
        "purpose": "",
    }

    # Extract technologies from language + topics
    if repo.get("language"):
        analysis["technologies"].append(repo["language"])
    for topic in (repo.get("topics") or []):
        if topic not in analysis["technologies"]:
            analysis["technologies"].append(topic)

    # Read README for architecture signals
    readme = await db["github_readmes"].find_one({"repository": repo_name})
    if readme:
        content = readme.get("content", "").lower()

        # Architecture signals
        arch_keywords = {
            "microservices": "Microservices architecture",
            "clean architecture": "Clean Architecture",
            "domain-driven": "Domain-Driven Design",
            "cqrs": "CQRS pattern",
            "event-driven": "Event-driven architecture",
            "serverless": "Serverless architecture",
            "container": "Containerized deployment",
            "docker": "Docker containerization",
            "kubernetes": "Kubernetes orchestration",
            "ci/cd": "CI/CD pipeline",
            "terraform": "Infrastructure as Code",
        }
        for keyword, signal in arch_keywords.items():
            if keyword in content:
                analysis["architecture_signals"].append(signal)

        # Extract purpose from first paragraph
        lines = readme.get("content", "").split("\n")
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#") and not line.startswith("!"):
                analysis["purpose"] = line[:200]
                break

    # Connect to projects
    projects = await db["projects"].find({
        "technologies": {"$in": analysis["technologies"][:5]},
        "status": "published",
    }).to_list(10)
    analysis["related_projects"] = [
        {"id": str(p["_id"]), "title": p.get("title", "")}
        for p in projects[:5]
    ]

    # Extract skills
    from app.tools import KNOWN_SKILLS, _normalize_skill_category
    for tech in analysis["technologies"]:
        tech_lower = tech.lower()
        if tech_lower in KNOWN_SKILLS:
            info = KNOWN_SKILLS[tech_lower]
            analysis["skills_extracted"].append({
                "skill": tech,
                "category": _normalize_skill_category(info["category"]),
                "confidence": 0.85,
            })

    return analysis


@mcp_tool("extract_project_evidence",
          "Extract project evidence from a repository",
          "github", permission="agent")
async def extract_project_evidence(repo_name: str) -> dict:
    """Extract evidence that can improve project descriptions."""
    db = get_db()
    repo = await db["github_repositories"].find_one({"name": repo_name})
    if not repo:
        return {"error": f"Repository not found: {repo_name}"}

    evidence = {
        "repository": repo_name,
        "description": repo.get("description", ""),
        "language": repo.get("language", ""),
        "stars": repo.get("stargazers_count", 0),
        "forks": repo.get("forks_count", 0),
        "topics": repo.get("topics", []),
        "created_at": repo.get("created_at"),
        "updated_at": repo.get("updated_at"),
        "readme_summary": "",
        "features": [],
        "technologies": [],
    }

    # Extract from README
    readme = await db["github_readmes"].find_one({"repository": repo_name})
    if readme:
        content = readme.get("content", "")
        # Extract features (lines starting with - or * after "features" heading)
        in_features = False
        for line in content.split("\n"):
            lower = line.lower().strip()
            if "feature" in lower and "#" in line:
                in_features = True
                continue
            if in_features and (line.strip().startswith("- ") or
                                line.strip().startswith("* ")):
                feature = line.strip().lstrip("- *").strip()
                if feature and len(feature) > 5:
                    evidence["features"].append(feature[:200])
            elif in_features and "#" in line:
                in_features = False

        # Summary from first meaningful paragraph
        for line in content.split("\n"):
            line = line.strip()
            if (line and not line.startswith("#") and not line.startswith("!") and
                    not line.startswith("[") and len(line) > 20):
                evidence["readme_summary"] = line[:300]
                break

    return evidence


@mcp_tool("extract_skills_from_github",
          "Extract skills from all GitHub repositories",
          "github", permission="agent")
async def extract_skills_from_github() -> dict:
    """Scan all repos and extract skills with evidence."""
    db = get_db()
    repos = await db["github_repositories"].find({}).to_list(100)

    skills_map = {}  # skill -> {evidence, repos}
    for repo in repos:
        name = repo.get("name", "")
        lang = repo.get("language", "")
        topics = repo.get("topics", []) or []

        if lang:
            key = lang.lower()
            if key not in skills_map:
                skills_map[key] = {"skill": lang, "evidence": [], "repos": []}
            skills_map[key]["evidence"].append(f"github:{name}")
            if name not in skills_map[key]["repos"]:
                skills_map[key]["repos"].append(name)

        for topic in topics:
            key = topic.lower()
            if key not in skills_map:
                skills_map[key] = {"skill": topic, "evidence": [], "repos": []}
            skills_map[key]["evidence"].append(f"github:{name}")
            if name not in skills_map[key]["repos"]:
                skills_map[key]["repos"].append(name)

    return {
        "total_repos": len(repos),
        "unique_skills": len(skills_map),
        "skills": list(skills_map.values()),
    }


@mcp_tool("sync_repository", "Sync a repository's metadata from GitHub",
          "github", permission="admin")
async def sync_repository(repo_name: str) -> dict:
    """Trigger a sync for a specific repository. Admin only."""
    db = get_db()
    repo = await db["github_repositories"].find_one({"name": repo_name})
    if not repo:
        return {"error": f"Repository not found: {repo_name}"}

    # Mark for sync
    await db["github_repositories"].update_one(
        {"_id": repo["_id"]},
        {"$set": {"sync_requested_at": utcnow(), "sync_status": "pending"}})

    return {
        "repository": repo_name,
        "status": "sync_queued",
        "message": f"Repository {repo_name} queued for sync",
    }
