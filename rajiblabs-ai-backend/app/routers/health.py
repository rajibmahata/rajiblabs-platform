"""GET /health — no secrets exposed."""
from fastapi import APIRouter
from app.config import get_settings
from app.database import get_db

router = APIRouter()


@router.get("/health")
async def health():
    s = get_settings()
    db_ok = github_ok = openai_ok = "ok"
    try:
        await get_db().command("ping")
    except Exception:
        db_ok = "down"
    if not s.github_token:
        github_ok = "not-configured"
    if not s.openai_api_key:
        openai_ok = "not-configured"
    status = "ok" if db_ok == "ok" else "degraded"
    return {"status": status, "database": db_ok, "github": github_ok, "openai": openai_ok}
