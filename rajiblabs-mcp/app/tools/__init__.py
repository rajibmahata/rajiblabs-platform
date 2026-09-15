from __future__ import annotations

import time
import logging
from functools import wraps
from typing import Any, Callable

from app.permissions import has_permission
from app.audit import audit_log, record_tool_usage

logger = logging.getLogger(__name__)

TOOL_REGISTRY: dict[str, dict[str, Any]] = {}


def mcp_tool(
    name: str,
    description: str,
    category: str,
    permission: str = "read",
    timeout: float = 30.0,
    idempotent: bool = True,
):
    def decorator(fn: Callable) -> Callable:
        TOOL_REGISTRY[name] = {
            "name": name,
            "description": description,
            "category": category,
            "permission": permission,
            "timeout": timeout,
            "idempotent": idempotent,
            "function": fn,
        }

        @wraps(fn)
        async def wrapper(*args: Any, agent_id: str = "anonymous", **kwargs: Any) -> dict:
            start = time.monotonic()
            granted = has_permission(agent_id, name)

            if not granted:
                await audit_log(
                    tool_name=name,
                    agent_id=agent_id,
                    arguments=kwargs,
                    result={},
                    permission_granted=False,
                    error="permission_denied",
                )
                return {
                    "success": False,
                    "error": {
                        "code": "PERMISSION_DENIED",
                        "message": f"Role '{agent_id}' lacks permission for tool '{name}'",
                    },
                }

            try:
                result = await fn(*args, agent_id=agent_id, **kwargs)
                duration = (time.monotonic() - start) * 1000
                await audit_log(
                    tool_name=name,
                    agent_id=agent_id,
                    arguments=kwargs,
                    result=result if isinstance(result, dict) else {"data": result},
                    duration_ms=duration,
                )
                await record_tool_usage(name, agent_id, True, duration)
                return result
            except Exception as e:
                duration = (time.monotonic() - start) * 1000
                logger.exception("Tool %s failed", name)
                await audit_log(
                    tool_name=name,
                    agent_id=agent_id,
                    arguments=kwargs,
                    result={},
                    duration_ms=duration,
                    error=str(e),
                )
                await record_tool_usage(name, agent_id, False, duration)
                return {
                    "success": False,
                    "error": {
                        "code": "TOOL_ERROR",
                        "message": str(e),
                    },
                }

        wrapper._mcp_tool_name = name
        wrapper._mcp_tool_description = description
        wrapper._mcp_tool_category = category
        wrapper._mcp_tool_permission = permission
        wrapper._mcp_tool_timeout = timeout
        wrapper._mcp_tool_idempotent = idempotent
        return wrapper

    return decorator


def _oid_str(obj: Any) -> str | None:
    if obj is None:
        return None
    if isinstance(obj, str):
        return obj
    from bson import ObjectId
    if isinstance(obj, ObjectId):
        return str(obj)
    return str(obj)


def _clean_secret_keys(data: dict) -> dict:
    sensitive = {"password", "secret", "token", "api_key", "jwt_secret", "smtp_password"}
    cleaned = {}
    for k, v in data.items():
        if any(s in k.lower() for s in sensitive):
            cleaned[k] = "***" if v else ""
        else:
            cleaned[k] = v
    return cleaned


def _scrub_text(text: str) -> str:
    import re
    patterns = [
        r"(?i)(password|secret|token|api_key)\s*[:=]\s*\S+",
        r"(?i)(smtp_password|jwt_secret)\s*[:=]\s*\S+",
    ]
    for p in patterns:
        text = re.sub(p, r"\1=***", text)
    return text


def _normalize_skill_category(category: str) -> str:
    mapping = {
        "frontend": "frontend",
        "front-end": "frontend",
        "backend": "backend",
        "back-end": "backend",
        "fullstack": "fullstack",
        "full-stack": "fullstack",
        "full stack": "fullstack",
        "devops": "devops",
        "mobile": "mobile",
        "database": "database",
        "data": "data",
        "ai": "ai",
        "ml": "ai",
        "design": "design",
        "testing": "testing",
        "security": "security",
        "cloud": "cloud",
        "other": "other",
    }
    return mapping.get(category.lower().strip(), "other")


KNOWN_SKILLS: dict[str, dict[str, str]] = {
    "python": {"category": "backend", "family": "language"},
    "javascript": {"category": "frontend", "family": "language"},
    "typescript": {"category": "frontend", "family": "language"},
    "csharp": {"category": "backend", "family": "language"},
    "c#": {"category": "backend", "family": "language"},
    "java": {"category": "backend", "family": "language"},
    "go": {"category": "backend", "family": "language"},
    "rust": {"category": "backend", "family": "language"},
    "php": {"category": "backend", "family": "language"},
    "ruby": {"category": "backend", "family": "language"},
    "swift": {"category": "mobile", "family": "language"},
    "kotlin": {"category": "mobile", "family": "language"},
    "dart": {"category": "mobile", "family": "language"},
    "sql": {"category": "database", "family": "language"},
    "html": {"category": "frontend", "family": "markup"},
    "css": {"category": "frontend", "family": "style"},
    "react": {"category": "frontend", "family": "framework"},
    "nextjs": {"category": "frontend", "family": "framework"},
    "next.js": {"category": "frontend", "family": "framework"},
    "vue": {"category": "frontend", "family": "framework"},
    "angular": {"category": "frontend", "family": "framework"},
    "svelte": {"category": "frontend", "family": "framework"},
    "node.js": {"category": "backend", "family": "runtime"},
    "nodejs": {"category": "backend", "family": "runtime"},
    "django": {"category": "backend", "family": "framework"},
    "fastapi": {"category": "backend", "family": "framework"},
    "flask": {"category": "backend", "family": "framework"},
    "express": {"category": "backend", "family": "framework"},
    "asp.net": {"category": "backend", "family": "framework"},
    "asp.net core": {"category": "backend", "family": "framework"},
    "dotnet": {"category": "backend", "family": "framework"},
    ".net": {"category": "backend", "family": "framework"},
    ".net core": {"category": "backend", "family": "framework"},
    "spring": {"category": "backend", "family": "framework"},
    "rails": {"category": "backend", "family": "framework"},
    "laravel": {"category": "backend", "family": "framework"},
    "mongodb": {"category": "database", "family": "database"},
    "postgresql": {"category": "database", "family": "database"},
    "mysql": {"category": "database", "family": "database"},
    "redis": {"category": "database", "family": "cache"},
    "elasticsearch": {"category": "database", "family": "search"},
    "qdrant": {"category": "database", "family": "vector_db"},
    "docker": {"category": "devops", "family": "tool"},
    "kubernetes": {"category": "devops", "family": "platform"},
    "aws": {"category": "cloud", "family": "provider"},
    "azure": {"category": "cloud", "family": "provider"},
    "gcp": {"category": "cloud", "family": "provider"},
    "google cloud": {"category": "cloud", "family": "provider"},
    "microsoft azure": {"category": "cloud", "family": "provider"},
    "azure functions": {"category": "cloud", "family": "service"},
    "azure devops": {"category": "devops", "family": "platform"},
    "github actions": {"category": "devops", "family": "ci"},
    "ci/cd": {"category": "devops", "family": "practice"},
    "git": {"category": "devops", "family": "tool"},
    "openai": {"category": "ai", "family": "provider"},
    "langchain": {"category": "ai", "family": "framework"},
    "tensorflow": {"category": "ai", "family": "framework"},
    "pytorch": {"category": "ai", "family": "framework"},
    "llm": {"category": "ai", "family": "concept"},
    "rag": {"category": "ai", "family": "concept"},
    "mcp": {"category": "ai", "family": "protocol"},
    "tailwind": {"category": "frontend", "family": "style"},
    "bootstrap": {"category": "frontend", "family": "style"},
    "sass": {"category": "frontend", "family": "style"},
    "vite": {"category": "frontend", "family": "tool"},
    "webpack": {"category": "frontend", "family": "tool"},
    "pytest": {"category": "testing", "family": "tool"},
    "jest": {"category": "testing", "family": "tool"},
    "cypress": {"category": "testing", "family": "tool"},
    "selenium": {"category": "testing", "family": "tool"},
}
