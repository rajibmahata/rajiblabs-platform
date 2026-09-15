"""MCP data models and schemas."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    """Timezone-aware UTC now (replaces deprecated _utcnow())."""
    return datetime.now(timezone.utc)


# ── Tool Registry ──

class ToolCategory(str, Enum):
    PROFILE = "profile"
    PORTFOLIO = "portfolio"
    PROJECT = "project"
    SKILL = "skill"
    GITHUB = "github"
    KNOWLEDGE = "knowledge"
    SEO = "seo"
    CONTENT = "content"


class ToolPermission(str, Enum):
    PUBLIC = "public"
    AGENT = "agent"
    ADMIN = "admin"


class ToolDefinition(BaseModel):
    """MCP tool definition."""
    name: str
    description: str
    category: ToolCategory
    permission: ToolPermission = ToolPermission.AGENT
    input_schema: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] = Field(default_factory=dict)
    timeout_seconds: int = 30
    idempotent: bool = False


# ── Audit ──

class ToolAuditEntry(BaseModel):
    """Audit log entry for MCP tool usage."""
    tool: str
    agent: str = ""
    request_id: str = ""
    started_at: datetime
    completed_at: datetime | None = None
    duration_ms: int = 0
    status: str = "success"  # success | error | timeout
    error: str | None = None
    input_summary: str = ""
    records_changed: int = 0
    llm_used: bool = False
    tokens_used: int = 0
    estimated_cost: float = 0.0


# ── Content Versioning ──

class ContentVersion(BaseModel):
    """Versioned content change."""
    entity_type: str  # profile, project, skill, etc.
    entity_id: str
    version: int
    previous_content: dict[str, Any] = Field(default_factory=dict)
    new_content: dict[str, Any] = Field(default_factory=dict)
    reason: str = ""
    agent: str = ""
    mcp_tool: str = ""
    evidence: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=_utcnow)
    validation_score: float = 0.0
    seo_score: float = 0.0
    rollback_data: dict[str, Any] = Field(default_factory=dict)


# ── Skill Evidence ──

class SkillEvidence(BaseModel):
    """Evidence-backed skill record."""
    skill: str
    category: str
    confidence: float = 0.0
    evidence: list[str] = Field(default_factory=list)
    related_projects: list[str] = Field(default_factory=list)
    related_repositories: list[str] = Field(default_factory=list)
    first_seen: datetime = Field(default_factory=_utcnow)
    last_updated: datetime = Field(default_factory=_utcnow)


# ── Portfolio Ranking ──

class PortfolioRanking(BaseModel):
    """Portfolio ranking factors."""
    project_id: str
    technical_depth: float = 0.0
    business_value: float = 0.0
    recency: float = 0.0
    relevance: float = 0.0
    architecture_complexity: float = 0.0
    ai_capability: float = 0.0
    cloud_capability: float = 0.0
    professional_relevance: float = 0.0
    portfolio_completeness: float = 0.0
    evidence_quality: float = 0.0
    total_score: float = 0.0


# ── SEO ──

class SEOMetadata(BaseModel):
    """SEO metadata for a page."""
    title: str = ""
    description: str = ""
    keywords: list[str] = Field(default_factory=list)
    canonical_url: str = ""
    og_title: str = ""
    og_description: str = ""
    og_image: str = ""
    schema_type: str = ""
    schema_data: dict[str, Any] = Field(default_factory=dict)
    headings: dict[str, str] = Field(default_factory=dict)
    internal_links: list[str] = Field(default_factory=list)
    image_alt_texts: dict[str, str] = Field(default_factory=dict)


# ── Content Intelligence ──

class ContentHealth(BaseModel):
    """Health score for a content entity."""
    entity_type: str
    entity_id: str
    completeness: float = 0.0
    freshness: float = 0.0
    evidence_quality: float = 0.0
    seo_health: float = 0.0
    overall_score: float = 0.0
    issues: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    last_analyzed: datetime = Field(default_factory=_utcnow)
