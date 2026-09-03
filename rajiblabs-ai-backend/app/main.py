"""FastAPI app factory — MongoDB backend replacing .NET API."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.core_logging import setup_logging
from app.database import init_db
from app.routers import health, public, admin_auth, admin_projects, github, ai, agent, chat, resume

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
    app = FastAPI(title="RajibLabs API", version="2.0.0",
                  docs_url="/docs" if settings.app_env != "production" else None)
    app.add_middleware(
        CORSMiddleware, allow_origins=settings.cors_list, allow_credentials=True,
        allow_methods=["*"], allow_headers=["*"])
    for r in (health.router, public.router, admin_auth.router, admin_projects.router,
              github.router, ai.router, agent.router, chat.router, resume.router):
        app.include_router(r)
    return app


app = create_app()


@app.on_event("startup")
async def _startup():
    await init_db()
