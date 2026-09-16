"""RajibLabs Agent Orchestrator — FastAPI entry point."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.config import settings
from app.database import connect_db, disconnect_db
from app.cache import connect_redis, disconnect_redis
from app.models import TaskType, AgentRole, RunStatus
from app.orchestrator import orchestrator
from app.mcp_client import mcp_client

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("rajiblabs-orchestrator")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting RajibLabs Agent Orchestrator v1.0.0")
    await connect_db()
    await connect_redis()
    yield
    await mcp_client.close()
    await disconnect_redis()
    await disconnect_db()
    logger.info("Orchestrator stopped")


app = FastAPI(
    title="RajibLabs Agent Orchestrator",
    version="1.0.0",
    description="PydanticAI-based content intelligence and agent orchestration",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RunTaskRequest(BaseModel):
    task_type: str
    description: str = ""
    entity_type: str = ""
    entity_id: str = ""


@app.get("/health")
async def health():
    mcp_health = await mcp_client.health()
    return {
        "status": "ok",
        "service": "rajiblabs-agent-orchestrator",
        "version": "1.0.0",
        "mcp": mcp_health.get("status", "unknown"),
    }


@app.post("/run")
async def run_task(request: RunTaskRequest):
    try:
        task_type = TaskType(request.task_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unknown task type: {request.task_type}")

    run = await orchestrator.execute_task(
        task_type=task_type,
        description=request.description,
        entity_type=request.entity_type,
        entity_id=request.entity_id,
    )
    return run.model_dump(mode="json")


@app.get("/runs")
async def list_runs(
    status: str | None = None,
    limit: int = Query(20, ge=1, le=100),
):
    run_status = None
    if status:
        try:
            run_status = RunStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Unknown status: {status}")

    runs = await orchestrator.list_runs(status=run_status, limit=limit)
    return {"runs": [r.model_dump(mode="json") for r in runs], "count": len(runs)}


@app.get("/runs/{run_id}")
async def get_run(run_id: str):
    run = await orchestrator.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run.model_dump(mode="json")


@app.get("/agents")
async def list_agents():
    agents = []
    for role in AgentRole:
        agents.append({
            "role": role.value,
            "name": role.value.replace("_", " ").title(),
        })
    return {"agents": agents, "count": len(agents)}


@app.get("/tasks")
async def list_task_types():
    types = []
    for tt in TaskType:
        types.append({
            "type": tt.value,
            "name": tt.value.replace("_", " ").title(),
        })
    return {"task_types": types, "count": len(types)}
