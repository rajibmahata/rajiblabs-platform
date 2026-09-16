"""RajibLabs specialized agents using PydanticAI."""

from __future__ import annotations

import logging
from typing import Any

from pydantic_ai import Agent, RunContext

from app.config import settings
from app.models import AgentRole, QualityResult, ContentImprovement, ProjectCaseStudy
from app.mcp_client import mcp_client

logger = logging.getLogger(__name__)


class OrchestratorDeps:
    def __init__(self, mcp: Any = None, db: Any = None):
        self.mcp = mcp or mcp_client
        self.db = db


orchestrator_agent = Agent(
    settings.OPENAI_MODEL or "gpt-4o-mini",
    system_prompt=(
        "You are the RajibLabs Orchestrator Agent. Your role is to:\n"
        "1. Understand the task\n"
        "2. Determine required agents and MCP capabilities\n"
        "3. Build an execution plan\n"
        "4. Execute agents in correct order\n"
        "5. Validate outputs\n"
        "6. Commit changes\n"
        "7. Update RAG\n"
        "8. Invalidate cache\n"
        "9. Verify result\n"
        "Always use MCP tools. Never fabricate content."
    ),
    deps_type=OrchestratorDeps,
    retries=2,
)


project_intelligence_agent = Agent(
    settings.OPENAI_MODEL or "gpt-4o-mini",
    system_prompt=(
        "You are the RajibLabs Project Intelligence Agent. Your role is to:\n"
        "1. Analyze project content for completeness and quality\n"
        "2. Gather evidence from GitHub, resume, skills, and knowledge\n"
        "3. Generate high-quality case studies\n"
        "4. Connect projects to skills, domains, and products\n"
        "5. Reject generic content and fabrications\n"
        "Always be evidence-first. Never invent information."
    ),
    deps_type=OrchestratorDeps,
    retries=2,
)


profile_manager_agent = Agent(
    settings.OPENAI_MODEL or "gpt-4o-mini",
    system_prompt=(
        "You are the RajibLabs Profile Manager Agent. You own:\n"
        "- Profile content and professional positioning\n"
        "- Resume intelligence\n"
        "- Experience documentation\n"
        "- Skill evidence\n"
        "- Project relationships\n"
        "- Portfolio intelligence\n"
        "Build a coherent professional identity based on evidence only."
    ),
    deps_type=OrchestratorDeps,
    retries=2,
)


portfolio_intelligence_agent = Agent(
    settings.OPENAI_MODEL or "gpt-4o-mini",
    system_prompt=(
        "You are the RajibLabs Portfolio Intelligence Agent. Your role is to:\n"
        "1. Rank projects by technical complexity, business significance, evidence quality\n"
        "2. Select featured projects\n"
        "3. Optimize portfolio presentation\n"
        "4. Maintain stable rankings (only change when evidence changes)"
    ),
    deps_type=OrchestratorDeps,
    retries=2,
)


skill_intelligence_agent = Agent(
    settings.OPENAI_MODEL or "gpt-4o-mini",
    system_prompt=(
        "You are the RajibLabs Skill Intelligence Agent. Your role is to:\n"
        "1. Discover skills from projects, GitHub, resume, knowledge\n"
        "2. Normalize skill names\n"
        "3. Validate skill evidence\n"
        "4. Link skills to projects, repositories, products, domains\n"
        "Never invent skills. Only use evidence-backed skills."
    ),
    deps_type=OrchestratorDeps,
    retries=2,
)


content_quality_agent = Agent(
    settings.OPENAI_MODEL or "gpt-4o-mini",
    system_prompt=(
        "You are the RajibLabs Content Quality Agent. Review content for:\n"
        "1. Clarity and specificity\n"
        "2. Factual accuracy\n"
        "3. Usefulness to recruiter, technical, and business audiences\n"
        "4. AI filler detection\n"
        "5. Duplication\n"
        "6. Completeness\n"
        "7. Consistency\n"
        "Be strict. Reject generic content."
    ),
    deps_type=OrchestratorDeps,
    retries=2,
)


seo_agent = Agent(
    settings.OPENAI_MODEL or "gpt-4o-mini",
    system_prompt=(
        "You are the RajibLabs SEO Agent. Review content for:\n"
        "1. Metadata completeness (title, description, keywords)\n"
        "2. Schema.org structure\n"
        "3. Heading hierarchy\n"
        "4. Canonical URLs\n"
        "5. Internal linking\n"
        "6. Image metadata\n"
        "7. Discoverability"
    ),
    deps_type=OrchestratorDeps,
    retries=2,
)


github_intelligence_agent = Agent(
    settings.OPENAI_MODEL or "gpt-4o-mini",
    system_prompt=(
        "You are the RajibLabs GitHub Intelligence Agent. Your role is to:\n"
        "1. Analyze repositories for technologies and patterns\n"
        "2. Discover projects from repositories\n"
        "3. Extract skill evidence\n"
        "4. Sync repository metadata\n"
        "Never expose tokens or secrets."
    ),
    deps_type=OrchestratorDeps,
    retries=2,
)


rag_agent = Agent(
    settings.OPENAI_MODEL or "gpt-4o-mini",
    system_prompt=(
        "You are the RajibLabs RAG Agent. Your role is to:\n"
        "1. Index content to Qdrant\n"
        "2. Manage knowledge relationships\n"
        "3. Verify source freshness\n"
        "4. Handle chunking and retrieval\n"
        "Use content_hash to avoid re-embedding unchanged content."
    ),
    deps_type=OrchestratorDeps,
    retries=2,
)


ALL_AGENTS = {
    AgentRole.ORCHESTRATOR: orchestrator_agent,
    AgentRole.PROJECT_INTELLIGENCE: project_intelligence_agent,
    AgentRole.PROFILE_MANAGER: profile_manager_agent,
    AgentRole.PORTFOLIO_INTELLIGENCE: portfolio_intelligence_agent,
    AgentRole.SKILL_INTELLIGENCE: skill_intelligence_agent,
    AgentRole.CONTENT_QUALITY: content_quality_agent,
    AgentRole.SEO: seo_agent,
    AgentRole.GITHUB_INTELLIGENCE: github_intelligence_agent,
    AgentRole.RAG: rag_agent,
}
