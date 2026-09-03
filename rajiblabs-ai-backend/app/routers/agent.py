"""Daily agent: manual run + status. Scheduler in app/workers/scheduler.py."""
from fastapi import APIRouter, Depends
from app.auth.dependencies import require_admin
from app.database import get_db
from app.models import oid_str
from app.agents.daily_agent import run_daily_agent

router = APIRouter(prefix="/api/admin/agent")


@router.post("/run")
async def run(email: str = Depends(require_admin)):
    return await run_daily_agent(triggered_by=email)


@router.get("/runs")
async def runs(email: str = Depends(require_admin)):
    db = get_db()
    cur = db["agent_runs"].find().sort("started_at", -1).limit(20)
    return [oid_str(d) async for d in cur]


@router.get("/qa")
async def qa_status(email: str = Depends(require_admin)):
    db = get_db()
    last_qa = await db["agent_runs"].find_one({"agent": "qa"}, sort=[("started_at", -1)])
    return {"last_qa": oid_str(last_qa) if last_qa else None,
            "note": "Run pytest + playwright locally; results posted here by scripts/run_qa.py"}
