"""MCP API routers."""

from app.routers.health import router as health_router
from app.routers.profile import router as profile_router
from app.routers.project import router as project_router
from app.routers.skill import router as skill_router
from app.routers.github import router as github_router
from app.routers.knowledge import router as knowledge_router
from app.routers.seo import router as seo_router
from app.routers.content import router as content_router
from app.routers.audit import router as audit_router

__all__ = [
    "health_router", "profile_router", "project_router",
    "skill_router", "github_router", "knowledge_router",
    "seo_router", "content_router", "audit_router",
]
