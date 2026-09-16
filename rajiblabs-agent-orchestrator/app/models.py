"""Core models for agent orchestration."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class RunStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    WAITING = "waiting"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    CANCELLED = "cancelled"


class QualityGrade(str, Enum):
    REJECT = "reject"
    NEEDS_IMPROVEMENT = "needs_improvement"
    ACCEPTABLE = "acceptable"
    PUBLISH = "publish"


class AgentRole(str, Enum):
    ORCHESTRATOR = "orchestrator"
    PROFILE_MANAGER = "profile_manager"
    PROJECT_INTELLIGENCE = "project_intelligence"
    PORTFOLIO_INTELLIGENCE = "portfolio_intelligence"
    SKILL_INTELLIGENCE = "skill_intelligence"
    GITHUB_INTELLIGENCE = "github_intelligence"
    CONTENT_QUALITY = "content_quality"
    SEO = "seo"
    RAG = "rag"
    CONTENT_WRITER = "content_writer"


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class TaskType(str, Enum):
    CONTENT_IMPROVEMENT = "content_improvement"
    PROJECT_IMPROVEMENT = "project_improvement"
    PROFILE_IMPROVEMENT = "profile_improvement"
    PORTFOLIO_OPTIMIZATION = "portfolio_optimization"
    SKILL_DISCOVERY = "skill_discovery"
    GITHUB_SYNC = "github_sync"
    SEO_AUDIT = "seo_audit"
    CONTENT_AUDIT = "content_audit"
    FULL_AUDIT = "full_audit"


class EvidenceSource(BaseModel):
    source_type: str
    source_id: str = ""
    content: str = ""
    confidence: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class QualityDimension(BaseModel):
    dimension: str
    score: float = 0.0
    max_score: float = 10.0
    evidence: list[str] = Field(default_factory=list)
    issues: list[str] = Field(default_factory=list)


class QualityResult(BaseModel):
    total_score: float = 0.0
    grade: QualityGrade = QualityGrade.REJECT
    dimensions: list[QualityDimension] = Field(default_factory=list)
    passed: bool = False
    publishable: bool = False


class ContentVersion(BaseModel):
    version: int = 0
    content: dict[str, Any] = Field(default_factory=dict)
    quality_score: float = 0.0
    agent: str = ""
    run_id: str = ""
    reason: str = ""
    evidence: list[EvidenceSource] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RunStep(BaseModel):
    step_id: str
    agent: AgentRole
    task: str
    status: StepStatus = StepStatus.PENDING
    input_data: dict[str, Any] = Field(default_factory=dict)
    output_data: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: float = 0.0
    mcp_calls: int = 0
    llm_calls: int = 0
    tokens_used: int = 0


class AgentRun(BaseModel):
    run_id: str
    parent_run_id: str | None = None
    task_type: TaskType
    agent: AgentRole = AgentRole.ORCHESTRATOR
    status: RunStatus = RunStatus.QUEUED
    task_description: str = ""
    steps: list[RunStep] = Field(default_factory=list)
    tools_used: list[str] = Field(default_factory=list)
    mcp_calls: int = 0
    llm_calls: int = 0
    tokens_used: int = 0
    estimated_cost: float = 0.0
    sources: list[EvidenceSource] = Field(default_factory=list)
    changes: list[dict[str, Any]] = Field(default_factory=list)
    validation: QualityResult | None = None
    errors: list[str] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None
    duration_ms: float = 0.0


class ProjectCaseStudy(BaseModel):
    project_id: str
    title: str
    positioning: str = ""
    category: str = ""
    technologies: list[str] = Field(default_factory=list)
    status: str = ""
    links: dict[str, str] = Field(default_factory=dict)
    what_is_it: str = ""
    why_built: str = ""
    problem: str = ""
    users: str = ""
    solution: str = ""
    capabilities: str = ""
    workflow: str = ""
    architecture: str = ""
    technology_choices: str = ""
    ai_automation: str = ""
    role: str = ""
    engineering_decisions: str = ""
    challenges: str = ""
    outcomes: str = ""
    skills_demonstrated: list[str] = Field(default_factory=list)
    domains: list[str] = Field(default_factory=list)
    evidence: list[EvidenceSource] = Field(default_factory=list)


class ContentImprovement(BaseModel):
    entity_type: str
    entity_id: str
    before: dict[str, Any] = Field(default_factory=dict)
    after: dict[str, Any] = Field(default_factory=dict)
    why_changed: str = ""
    evidence: list[EvidenceSource] = Field(default_factory=list)
    quality_before: QualityResult | None = None
    quality_after: QualityResult | None = None
    agent: str = ""
    run_id: str = ""
    version: int = 0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
