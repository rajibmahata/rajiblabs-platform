"""FastAPI app factory — MongoDB backend replacing .NET API."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.core_logging import setup_logging
from app.database import init_db
from app.routers import health, public, admin_auth, admin_projects, admin_logs, github, ai, agent, chat, resume, legacy

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
            {"name": "Admin Auth", "description": "Dual-email login, JWT + cookies."},
            {"name": "Admin CMS", "description": "Dashboard, projects, leads, notifications."},
            {"name": "Admin System Logs", "description": "Failure logs with 5-day TTL retention."},
            {"name": "Admin GitHub", "description": "Repo sync (PAT stays server-side)."},
            {"name": "Admin AI", "description": "AI rewrite drafts + quality-gated approve/reject."},
            {"name": "Admin Agent", "description": "Daily-agent manual runs + QA status."},
            {"name": "Admin Resume", "description": "Resume upload/versioning."},
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
        (resume.router, ["Admin Resume"]),
        (legacy.router, ["Site API (v1)"]),
    ):
        app.include_router(r, tags=tags)
    return app


app = create_app()
