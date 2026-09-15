"""RajibLabs MCP Content Intelligence Platform — Server Entry Point.

A reusable, Dockerized MCP layer that allows RajibLabs agents to
intelligently manage, validate, organize, refine, and continuously
improve profile, portfolio, projects, products, skills, GitHub knowledge,
SEO content, and RAG knowledge.

Architecture:
  MongoDB = Source of Truth
  Qdrant = Retrieval Layer
  MCP = Controlled Tool Interface
  Agents = Reasoning + Orchestration
  FastAPI = Application/API Layer
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import connect_db, close_db, ensure_indexes

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("rajiblabs-mcp")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle."""
    log.info("Starting RajibLabs MCP Content Intelligence Platform...")
    await connect_db()
    await ensure_indexes()
    log.info("MCP server ready — %s tools registered",
             _count_tools())
    yield
    log.info("Shutting down MCP server...")
    await close_db()


def _count_tools() -> int:
    """Count registered MCP tools."""
    count = 0
    import inspect
    import app.tools.profile
    import app.tools.project
    import app.tools.skill
    import app.tools.github
    import app.tools.knowledge
    import app.tools.seo
    import app.tools.content
    for module in [app.tools.profile, app.tools.project, app.tools.skill,
                   app.tools.github, app.tools.knowledge, app.tools.seo,
                   app.tools.content]:
        for name, obj in inspect.getmembers(module, inspect.iscoroutinefunction):
            if hasattr(obj, "_mcp_tool_name"):
                count += 1
    return count


app = FastAPI(
    title="RajibLabs MCP Content Intelligence Platform",
    description=(
        "Dockerized MCP (Model Context Protocol) layer for intelligent "
        "content management across profile, portfolio, projects, skills, "
        "GitHub, knowledge, and SEO."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
from app.routers import (
    health_router, profile_router, project_router,
    skill_router, github_router, knowledge_router,
    seo_router, content_router, audit_router,
)

app.include_router(health_router)
app.include_router(profile_router)
app.include_router(project_router)
app.include_router(skill_router)
app.include_router(github_router)
app.include_router(knowledge_router)
app.include_router(seo_router)
app.include_router(content_router)
app.include_router(audit_router)


@app.get("/")
async def root():
    return {
        "service": "rajiblabs-mcp",
        "version": "1.0.0",
        "description": "RajibLabs MCP Content Intelligence Platform",
        "tools": _count_tools(),
        "docs": "/docs",
    }
