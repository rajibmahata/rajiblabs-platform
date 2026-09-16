"""Central orchestrator — coordinates agents, MCP, and workflows."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from app.config import settings
from app.models import (
    AgentRun, AgentRole, RunStatus, RunStep, StepStatus,
    TaskType, QualityResult, ContentImprovement, EvidenceSource,
)
from app.mcp_client import mcp_client
from app.database import get_db
from app.cache import cache_invalidate, cache_invalidate_pattern
from app.engine.quality import compute_quality
from app.engine.content_intelligence import gather_evidence, analyze_content_quality
from app.agents import ALL_AGENTS, OrchestratorDeps

logger = logging.getLogger(__name__)


def _make_run_id() -> str:
    return f"run_{uuid.uuid4().hex[:12]}"


class Orchestrator:
    def __init__(self):
        self.deps = OrchestratorDeps(mcp=mcp_client)

    async def execute_task(
        self,
        task_type: TaskType,
        description: str = "",
        entity_type: str = "",
        entity_id: str = "",
        agent: AgentRole = AgentRole.ORCHESTRATOR,
    ) -> AgentRun:
        run_id = _make_run_id()
        run = AgentRun(
            run_id=run_id,
            task_type=task_type,
            agent=agent,
            task_description=description,
            status=RunStatus.RUNNING,
        )

        await self._save_run(run)

        try:
            if task_type == TaskType.PROJECT_IMPROVEMENT:
                await self._run_project_improvement(run, entity_type, entity_id)
            elif task_type == TaskType.PROFILE_IMPROVEMENT:
                await self._run_profile_improvement(run)
            elif task_type == TaskType.PORTFOLIO_OPTIMIZATION:
                await self._run_portfolio_optimization(run)
            elif task_type == TaskType.SKILL_DISCOVERY:
                await self._run_skill_discovery(run)
            elif task_type == TaskType.CONTENT_AUDIT:
                await self._run_content_audit(run)
            elif task_type == TaskType.SEO_AUDIT:
                await self._run_seo_audit(run)
            elif task_type == TaskType.FULL_AUDIT:
                await self._run_full_audit(run)
            else:
                run.errors.append(f"Unknown task type: {task_type}")

            if not run.errors:
                run.status = RunStatus.COMPLETED
            else:
                run.status = RunStatus.FAILED

        except Exception as e:
            logger.exception("Run %s failed", run_id)
            run.status = RunStatus.FAILED
            run.errors.append(str(e))

        run.completed_at = datetime.now(timezone.utc)
        run.duration_ms = (run.completed_at - run.started_at).total_seconds() * 1000
        await self._save_run(run)
        return run

    async def _run_project_improvement(self, run: AgentRun, entity_type: str, entity_id: str):
        step1 = self._add_step(run, "gather_evidence", AgentRole.GITHUB_INTELLIGENCE, "Gathering evidence")
        evidence = await gather_evidence(entity_type or "project", entity_id)
        self._complete_step(step1, {"evidence_count": len(evidence)})
        run.sources = evidence

        step2 = self._add_step(run, "analyze_content", AgentRole.CONTENT_QUALITY, "Analyzing content quality")
        analysis = await analyze_content_quality(entity_type or "project", entity_id)
        self._complete_step(step2, analysis)

        step3 = self._add_step(run, "validate_facts", AgentRole.CONTENT_QUALITY, "Validating factual accuracy")
        validation = compute_quality(
            analysis.get("content", {}),
            evidence=[{"source_type": e.source_type, "content": e.content} for e in evidence],
            required_fields=["title", "description", "problem", "solution", "skills"],
            text_fields=["description", "problem", "solution", "architecture"],
        )
        self._complete_step(step3, {"quality_score": validation.total_score, "grade": validation.grade.value})
        run.validation = validation

        if validation.publishable:
            step4 = self._add_step(run, "publish", AgentRole.PROJECT_INTELLIGENCE, "Content is publishable")
            self._complete_step(step4, {"action": "no_change_needed"})
        elif validation.passed:
            step4 = self._add_step(run, "improve", AgentRole.CONTENT_WRITER, "Content acceptable")
            self._complete_step(step4, {"action": "content_acceptable"})
        else:
            step4 = self._add_step(run, "flag", AgentRole.CONTENT_QUALITY, "Needs improvement")
            self._complete_step(step4, {"action": "flagged_for_review", "score": validation.total_score})

        step5 = self._add_step(run, "invalidate_cache", AgentRole.RAG, "Invalidating cache")
        await cache_invalidate_pattern("projects")
        await cache_invalidate_pattern("portfolio")
        self._complete_step(step5, {"action": "cache_invalidated"})

    async def _run_profile_improvement(self, run: AgentRun):
        step1 = self._add_step(run, "get_profile", AgentRole.PROFILE_MANAGER, "Retrieving profile")
        profile_result = await mcp_client.call_tool("get_profile")
        self._complete_step(step1, {"found": profile_result.get("success", False)})

        step2 = self._add_step(run, "analyze_profile", AgentRole.PROFILE_MANAGER, "Analyzing profile")
        analysis = await mcp_client.call_tool("analyze_profile")
        self._complete_step(step2, analysis.get("data", {}))

        step3 = self._add_step(run, "gather_evidence", AgentRole.SKILL_INTELLIGENCE, "Gathering evidence")
        evidence = await gather_evidence("profile", "")
        self._complete_step(step3, {"evidence_count": len(evidence)})

        step4 = self._add_step(run, "validate", AgentRole.CONTENT_QUALITY, "Validating profile")
        validation = compute_quality(
            profile_result.get("data", {}),
            evidence=[{"source_type": e.source_type} for e in evidence],
            required_fields=["name", "title", "about", "skills"],
            text_fields=["about", "tagline"],
        )
        self._complete_step(step4, {"quality_score": validation.total_score, "grade": validation.grade.value})
        run.validation = validation

        step5 = self._add_step(run, "invalidate_cache", AgentRole.RAG, "Invalidating cache")
        await cache_invalidate("profile", "full")
        self._complete_step(step5, {"action": "cache_invalidated"})

    async def _run_portfolio_optimization(self, run: AgentRun):
        step1 = self._add_step(run, "rank_projects", AgentRole.PORTFOLIO_INTELLIGENCE, "Ranking projects")
        ranking = await mcp_client.call_tool("rank_projects", {"limit": 10})
        self._complete_step(step1, ranking.get("data", {}))

        step2 = self._add_step(run, "select_featured", AgentRole.PORTFOLIO_INTELLIGENCE, "Selecting featured")
        featured = await mcp_client.call_tool("select_featured_projects", {"count": 3})
        self._complete_step(step2, featured.get("data", {}))

        step3 = self._add_step(run, "validate_portfolio", AgentRole.CONTENT_QUALITY, "Validating portfolio")
        validation = await mcp_client.call_tool("validate_portfolio")
        self._complete_step(step3, validation.get("data", {}))

        step4 = self._add_step(run, "invalidate_cache", AgentRole.RAG, "Invalidating cache")
        await cache_invalidate_pattern("portfolio")
        self._complete_step(step4, {"action": "cache_invalidated"})

    async def _run_skill_discovery(self, run: AgentRun):
        step1 = self._add_step(run, "discover_skills", AgentRole.SKILL_INTELLIGENCE, "Discovering skills")
        skills = await mcp_client.call_tool("discover_skills")
        self._complete_step(step1, skills.get("data", {}))

        step2 = self._add_step(run, "validate_skills", AgentRole.SKILL_INTELLIGENCE, "Validating skills")
        skill_data = skills.get("data", {})
        validated = 0
        for skill in skill_data.get("skills", [])[:20]:
            result = await mcp_client.call_tool("validate_skill", {"skill_name": skill.get("name", "")})
            if result.get("success") and result.get("data", {}).get("validated"):
                validated += 1
        self._complete_step(step2, {"validated": validated, "total": len(skill_data.get("skills", []))})

    async def _run_content_audit(self, run: AgentRun):
        step1 = self._add_step(run, "detect_missing", AgentRole.CONTENT_QUALITY, "Detecting missing info")
        missing = await mcp_client.call_tool("detect_missing_information")
        self._complete_step(step1, missing.get("data", {}))

        step2 = self._add_step(run, "detect_conflicts", AgentRole.CONTENT_QUALITY, "Detecting conflicts")
        conflicts = await mcp_client.call_tool("detect_conflicts")
        self._complete_step(step2, conflicts.get("data", {}))

        step3 = self._add_step(run, "detect_stale", AgentRole.CONTENT_QUALITY, "Detecting stale content")
        stale = await mcp_client.call_tool("detect_outdated_content")
        self._complete_step(step3, stale.get("data", {}))

    async def _run_seo_audit(self, run: AgentRun):
        step1 = self._add_step(run, "analyze_seo", AgentRole.SEO, "Analyzing SEO")
        seo = await mcp_client.call_tool("analyze_seo")
        self._complete_step(step1, seo.get("data", {}))

        step2 = self._add_step(run, "validate_metadata", AgentRole.SEO, "Validating metadata")
        metadata = await mcp_client.call_tool("validate_metadata")
        self._complete_step(step2, metadata.get("data", {}))

        step3 = self._add_step(run, "find_missing", AgentRole.SEO, "Finding missing metadata")
        missing = await mcp_client.call_tool("find_missing_metadata")
        self._complete_step(step3, missing.get("data", {}))

    async def _run_full_audit(self, run: AgentRun):
        await self._run_content_audit(run)
        await self._run_seo_audit(run)
        await self._run_skill_discovery(run)
        await self._run_portfolio_optimization(run)

    def _add_step(self, run: AgentRun, step_id: str, agent: AgentRole, task: str) -> RunStep:
        step = RunStep(
            step_id=step_id,
            agent=agent,
            task=task,
            status=StepStatus.RUNNING,
            started_at=datetime.now(timezone.utc),
        )
        run.steps.append(step)
        return step

    def _complete_step(self, step: RunStep, output: dict):
        step.status = StepStatus.COMPLETED
        step.output_data = output
        step.completed_at = datetime.now(timezone.utc)
        if step.started_at:
            step.duration_ms = (step.completed_at - step.started_at).total_seconds() * 1000

    async def _save_run(self, run: AgentRun):
        try:
            db = get_db()
            data = run.model_dump(mode="json")
            await db.agent_runs.update_one(
                {"run_id": run.run_id},
                {"$set": data},
                upsert=True,
            )
        except Exception as e:
            logger.warning("Failed to save run %s: %s", run.run_id, e)

    async def get_run(self, run_id: str) -> AgentRun | None:
        try:
            db = get_db()
            doc = await db.agent_runs.find_one({"run_id": run_id})
            if doc:
                doc.pop("_id", None)
                return AgentRun(**doc)
        except Exception as e:
            logger.warning("Failed to get run %s: %s", run_id, e)
        return None

    async def list_runs(
        self, status: RunStatus | None = None, limit: int = 20
    ) -> list[AgentRun]:
        try:
            db = get_db()
            query = {}
            if status:
                query["status"] = status.value
            cursor = db.agent_runs.find(query).sort("started_at", -1).limit(limit)
            runs = []
            async for doc in cursor:
                doc.pop("_id", None)
                runs.append(AgentRun(**doc))
            return runs
        except Exception as e:
            logger.warning("Failed to list runs: %s", e)
            return []


orchestrator = Orchestrator()
