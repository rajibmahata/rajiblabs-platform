"""MCP tool base module with audit logging and metrics."""

import time
import functools
from datetime import datetime, timezone
from typing import Any, Callable

from app.database import get_db, utcnow


def mcp_tool(name: str, description: str, category: str,
             permission: str = "agent", timeout_seconds: int = 30,
             idempotent: bool = False):
    """Decorator to register an MCP tool with audit logging."""
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            db = get_db()
            t0 = time.time()
            request_id = kwargs.pop("request_id", "")
            agent = kwargs.pop("agent", "")
            entry = {
                "tool": name,
                "agent": agent,
                "request_id": request_id,
                "started_at": utcnow(),
                "status": "success",
                "input_summary": str(kwargs)[:200],
                "records_changed": 0,
                "llm_used": False,
                "tokens_used": 0,
                "estimated_cost": 0.0,
            }
            try:
                result = await func(*args, **kwargs)
                entry["duration_ms"] = int((time.time() - t0) * 1000)
                entry["completed_at"] = utcnow()
                if isinstance(result, dict):
                    entry["records_changed"] = result.get("_records_changed", 0)
                    entry["llm_used"] = result.get("_llm_used", False)
                    entry["tokens_used"] = result.get("_tokens_used", 0)
                    entry["estimated_cost"] = result.get("_estimated_cost", 0.0)
                return result
            except Exception as e:
                entry["status"] = "error"
                entry["error"] = str(e)[:500]
                entry["duration_ms"] = int((time.time() - t0) * 1000)
                entry["completed_at"] = utcnow()
                raise
            finally:
                try:
                    await db["mcp_audit_log"].insert_one(entry)
                except Exception:
                    pass

        # Attach metadata
        wrapper._mcp_tool_name = name
        wrapper._mcp_description = description
        wrapper._mcp_category = category
        wrapper._mcp_permission = permission
        wrapper._mcp_timeout = timeout_seconds
        wrapper._mcp_idempotent = idempotent
        return wrapper
    return decorator


def _oid_str(doc: dict | None) -> dict:
    """Convert MongoDB _id to string id."""
    if not doc:
        return {}
    d = dict(doc)
    if "_id" in d:
        d["id"] = str(d.pop("_id"))
    return d


def _clean_secret_keys(obj: Any) -> Any:
    """Recursively remove secret-looking keys from output."""
    import re
    blocked = re.compile(
        r"(?i)(password|secret|token|api[_-]?key|jwt|credential|"
        r"private[_-]?key|connection[_-]?string)")
    if isinstance(obj, dict):
        return {k: _clean_secret_keys(v) for k, v in obj.items()
                if not blocked.search(str(k))}
    if isinstance(obj, list):
        return [_clean_secret_keys(v) for v in obj]
    return obj


def _normalize_skill_category(raw: str) -> str:
    """Normalize skill category names."""
    mapping = {
        "backend": "Backend",
        "frontend": "Frontend",
        "database": "Databases",
        "databases": "Databases",
        "cloud": "Cloud",
        "devops": "DevOps",
        "ai": "AI / ML",
        "ml": "AI / ML",
        "ai/ml": "AI / ML",
        "agentic ai": "Agentic AI",
        "architecture": "Architecture",
        "api": "APIs",
        "apis": "APIs",
        "testing": "Testing / QA",
        "qa": "Testing / QA",
        "tools": "Tools",
        "business": "Business / Domain",
        "domain": "Business / Domain",
        "languages": "Programming Languages",
        "frameworks": "Frameworks",
    }
    return mapping.get(raw.lower().strip(), raw.strip().title())


# ── Known Skills Database ──

KNOWN_SKILLS: dict[str, dict] = {
    # Programming Languages
    "c#": {"category": "Backend", "aliases": ["csharp", "c-sharp"]},
    "python": {"category": "Backend", "aliases": ["py"]},
    "javascript": {"category": "Frontend", "aliases": ["js"]},
    "typescript": {"category": "Frontend", "aliases": ["ts"]},
    "sql": {"category": "Databases", "aliases": ["tsql", "t-sql"]},
    "powershell": {"category": "DevOps", "aliases": ["pwsh"]},
    "bash": {"category": "DevOps", "aliases": ["shell", "sh"]},
    "html": {"category": "Frontend", "aliases": []},
    "css": {"category": "Frontend", "aliases": ["scss", "sass", "less"]},

    # Frameworks
    ".net": {"category": "Backend", "aliases": ["dotnet", ".net core", "aspnet", "asp.net"]},
    "asp.net": {"category": "Backend", "aliases": ["aspnet", "aspnet core", "asp.net core"]},
    "asp.net core": {"category": "Backend", "aliases": ["aspnet core"]},
    "blazor": {"category": "Frontend", "aliases": []},
    "react": {"category": "Frontend", "aliases": ["reactjs", "react.js"]},
    "angular": {"category": "Frontend", "aliases": ["angularjs"]},
    "vue": {"category": "Frontend", "aliases": ["vuejs", "vue.js"]},
    "fastapi": {"category": "Backend", "aliases": ["fast api"]},
    "flask": {"category": "Backend", "aliases": []},
    "django": {"category": "Backend", "aliases": []},
    "node.js": {"category": "Backend", "aliases": ["nodejs", "node"]},
    "express": {"category": "Backend", "aliases": ["expressjs"]},
    "next.js": {"category": "Frontend", "aliases": ["nextjs"]},
    "tailwind": {"category": "Frontend", "aliases": ["tailwindcss", "tailwind css"]},
    "vite": {"category": "Frontend", "aliases": []},

    # Databases
    "mongodb": {"category": "Databases", "aliases": ["mongo"]},
    "sql server": {"category": "Databases", "aliases": ["mssql", "ms sql", "sqlserver"]},
    "postgresql": {"category": "Databases", "aliases": ["postgres", "psql"]},
    "mysql": {"category": "Databases", "aliases": []},
    "redis": {"category": "Databases", "aliases": []},
    "elasticsearch": {"category": "Databases", "aliases": ["elastic", "es"]},
    "qdrant": {"category": "Databases", "aliases": []},
    "cosmos db": {"category": "Databases", "aliases": ["cosmosdb", "cosmos"]},

    # Cloud
    "azure": {"category": "Cloud", "aliases": ["microsoft azure"]},
    "aws": {"category": "Cloud", "aliases": ["amazon web services"]},
    "gcp": {"category": "Cloud", "aliases": ["google cloud"]},
    "docker": {"category": "DevOps", "aliases": []},
    "kubernetes": {"category": "DevOps", "aliases": ["k8s"]},

    # AI / ML
    "openai": {"category": "AI / ML", "aliases": ["gpt", "gpt-4", "gpt-4o"]},
    "langchain": {"category": "AI / ML", "aliases": []},
    "semantic kernel": {"category": "AI / ML", "aliases": ["sk"]},
    "ai": {"category": "AI / ML", "aliases": ["artificial intelligence"]},
    "machine learning": {"category": "AI / ML", "aliases": ["ml"]},
    "agentic ai": {"category": "Agentic AI", "aliases": ["agents", "ai agents"]},
    "rag": {"category": "AI / ML", "aliases": ["retrieval augmented generation"]},
    "llm": {"category": "AI / ML", "aliases": ["large language model"]},
    "vector database": {"category": "AI / ML", "aliases": ["vector db"]},

    # Architecture
    "microservices": {"category": "Architecture", "aliases": []},
    "clean architecture": {"category": "Architecture", "aliases": []},
    "domain-driven design": {"category": "Architecture", "aliases": ["ddd"]},
    "cqrs": {"category": "Architecture", "aliases": []},
    "event sourcing": {"category": "Architecture", "aliases": []},
    "mediator": {"category": "Architecture", "aliases": ["mediatr"]},

    # Tools
    "git": {"category": "Tools", "aliases": ["github"]},
    "github actions": {"category": "DevOps", "aliases": []},
    "jira": {"category": "Tools", "aliases": []},
    "figma": {"category": "Tools", "aliases": []},
    "visual studio": {"category": "Tools", "aliases": ["vs"]},
    "vs code": {"category": "Tools", "aliases": ["vscode"]},

    # Business
    "erp": {"category": "Business / Domain", "aliases": []},
    "crm": {"category": "Business / Domain", "aliases": []},
    "fintech": {"category": "Business / Domain", "aliases": ["financial technology"]},
    "healthcare": {"category": "Business / Domain", "aliases": []},
    "ecommerce": {"category": "Business / Domain", "aliases": ["e-commerce"]},
    "saas": {"category": "Business / Domain", "aliases": ["software as a service"]},
}
