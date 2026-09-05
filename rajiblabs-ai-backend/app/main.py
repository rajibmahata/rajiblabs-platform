"""FastAPI app factory — MongoDB backend replacing .NET API."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.core_logging import setup_logging
from app.database import init_db
from app.routers import health, public, admin_auth, admin_projects, admin_logs, github, ai, agent, chat, resume, legacy, lead_chat, rag, admin_rag, admin_workbench, languages, admin_languages, concierge, admin_agents, admin_career

setup_logging()
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    # Scheduler starts only if enabled and not in test
    try:
        from app.workers.scheduler import start_scheduler
        if settings.daily_agent_enabled:
            start_scheduler()
    except Exception:
        pass
    yield


def create_app() -> FastAPI:
    docs_enabled = settings.app_env != "production"
    app = FastAPI(
        title="RajibLabs API",
        version="2.0.0",
        description=(
            "AI-assisted portfolio CMS backend (FastAPI + MongoDB). "
            "Public CMS served under `/api/public/*`; admin endpoints under "
            "`/api/admin/*` require a Bearer JWT from `POST /api/admin/auth/login` "
            "(or the `rlabs_access` HttpOnly cookie) — use the Authorize button. "
            "Docs are disabled in production."
        ),
        contact={"name": "RajibLabs", "url": "https://rajiblabs.com"},
        license_info={"name": "Proprietary — RajibLabs"},
        openapi_tags=[
            {"name": "System", "description": "Health checks."},
            {"name": "Public CMS", "description": "Published-only content for the React site."},
            {"name": "Public Chat & Leads", "description": "AI chat widget + lead/quote capture (rate-limited)."},
            {"name": "Public RAG", "description": "Grounded knowledge Q&A (intent + sources)."},
            {"name": "Admin RAG", "description": "RAG dashboard, knowledge CRUD, reindex, evaluate."},
            {"name": "Admin Auth", "description": "Dual-email login, JWT + cookies."},
            {"name": "Admin CMS", "description": "Dashboard, projects, leads, notifications."},
            {"name": "Admin System Logs", "description": "Failure logs with 5-day TTL retention."},
            {"name": "Admin GitHub", "description": "Repo sync (PAT stays server-side)."},
            {"name": "Admin AI", "description": "AI rewrite drafts + quality-gated approve/reject."},
            {"name": "Admin Agent", "description": "Daily-agent manual runs + QA status."},
            {"name": "Admin Resume", "description": "Resume upload/versioning."},
            {"name": "Public Concierge", "description": "RajibLabs Concierge Agent chat (tools + grounded replies)."},
            {"name": "Admin Agents", "description": "AI agent configs, test console, stats, conversations."},
            {"name": "Site API (v1)", "description": "Port of the retired .NET API — same paths/shapes for the React site and admin panel."},
        ],
        lifespan=lifespan,
        docs_url="/docs" if docs_enabled else None,
        redoc_url="/redoc" if docs_enabled else None,
        openapi_url="/openapi.json" if docs_enabled else None,
    )
    app.add_middleware(
        CORSMiddleware, allow_origins=settings.cors_list, allow_credentials=True,
        allow_methods=["*"], allow_headers=["*"])
    # Public uploads (images/gallery). Starlette blocks path traversal;
    # filenames are server-generated uuids, never user input.
    from pathlib import Path as _Path
    from fastapi.staticfiles import StaticFiles
    _up = _Path(settings.upload_dir)
    _up.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=str(_up)), name="uploads")
    for r, tags in (
        (health.router, ["System"]),
        (public.router, ["Public CMS"]),
        (admin_auth.router, ["Admin Auth"]),
        (admin_projects.router, ["Admin CMS"]),
        (admin_logs.router, ["Admin System Logs"]),
        (github.router, ["Admin GitHub"]),
        (ai.router, ["Admin AI"]),
        (agent.router, ["Admin Agent"]),
        (chat.router, ["Public Chat & Leads"]),
        (lead_chat.router, ["Public Chat & Leads"]),
        (rag.router, ["Public RAG"]),
        (admin_rag.router, ["Admin RAG"]),
        (languages.router, ["Public Languages"]),
        (admin_languages.router, ["Admin Languages"]),
        (admin_workbench.router, ["Admin AI Workbench"]),
        (resume.router, ["Admin Resume"]),
        (legacy.router, ["Site API (v1)"]),
        (concierge.router, ["Public Concierge"]),
        (admin_agents.router, ["Admin Agents"]),
        (admin_career.router, ["Admin Career"]),
    ):
        app.include_router(r, tags=tags)
    return app


app = create_app()
