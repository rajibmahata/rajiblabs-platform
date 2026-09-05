"""Pydantic request/response schemas with structured validation."""
from datetime import datetime
from typing import Any, Literal, Optional
from pydantic import BaseModel, Field, field_validator

GITHUB_URL_PREFIX = "https://github.com/"


def validate_github_url(v: Optional[str]) -> Optional[str]:
    if v in (None, ""):
        return None
    v = v.strip()
    if not v.startswith(GITHUB_URL_PREFIX):
        raise ValueError("github_url must start with https://github.com/ or be null")
    if v.rstrip("/") == "https://github.com/rajibmahata":
        raise ValueError("generic profile URL not allowed — use per-project repository URL or null")
    for bad in ("javascript:", "data:", "file:"):
        if bad in v.lower():
            raise ValueError("dangerous URL scheme")
    return v


class ProjectIn(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    slug: Optional[str] = None
    category: str = "project"
    status: Literal["draft", "review", "approved", "published", "archived"] = "draft"
    short_description: str = ""
    full_description: str = ""
    problem: str = ""
    solution: str = ""
    business_value: str = ""
    features: list[str] = []
    architecture: str = ""
    technologies: list[str] = []
    github_url: Optional[str] = None
    live_url: Optional[str] = None
    demo_url: Optional[str] = None
    video_url: Optional[str] = None
    featured_image: Optional[str] = None
    gallery: list[str] = []
    featured: bool = False
    published: bool = False
    display_order: int = 0
    locked_fields: list[str] = []

    _gh = field_validator("github_url")(validate_github_url)


class AIContentOut(BaseModel):
    title: str
    short_description: str
    description: str
    problem: str = ""
    solution: str = ""
    features: list[str] = []
    architecture_summary: str = ""
    technology_summary: str = ""
    business_value: str = ""
    seo_title: str = ""
    seo_description: str = ""


class LeadIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    phone: str = Field(min_length=7, max_length=20)
    description: str = Field(min_length=5, max_length=5000)
    product: Optional[str] = None


class ChatMessageIn(BaseModel):
    session_token: Optional[str] = None
    session_id: Optional[str] = Field(default=None, max_length=64)  # preferred; token kept for compat
    message: str = Field(min_length=1, max_length=2000)
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    # RAG mode selector (§15/§19): "lead" (default) or "rag". Additive — old clients omit it.
    mode: Optional[str] = Field(default=None, max_length=16)
    # Response language (BCP-47-ish code, e.g. bn, zh-CN). Same KB, localized answer.
    language: Optional[str] = Field(default=None, max_length=12)


class LoginIn(BaseModel):
    email: str
    password: str


# ── AI Lead Conversation (structured AI output — validated before any DB write) ──

class LeadAssistantLead(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company_name: Optional[str] = None
    industry: Optional[str] = None


class LeadAssistantIdea(BaseModel):
    description: Optional[str] = None
    problem_statement: Optional[str] = None
    current_process: Optional[str] = None
    desired_outcome: Optional[str] = None


class LeadAssistantOut(BaseModel):
    """Structured result of one lead-assistant turn. Backend recomputes
    missing_fields/is_lead_captured authoritatively — AI values are hints."""
    reply: str = Field(min_length=1, max_length=2000)
    lead: LeadAssistantLead = LeadAssistantLead()
    idea: LeadAssistantIdea = LeadAssistantIdea()
    missing_fields: list[str] = []
    is_lead_captured: bool = False
    next_action: Literal["continue", "analyze_idea", "lead_captured", "human_followup"] = "continue"


class ChatSessionOut(BaseModel):
    session_id: str


class ScopeSection(BaseModel):
    problem_understanding: str = ""
    proposed_solution: str = ""
    core_features: list[str] = []
    user_roles: list[str] = []
    main_workflow: list[str] = []
    mvp_scope: list[str] = []
    future_features: list[str] = []
    technology_direction: str = ""
    risks_assumptions: list[str] = []
    discovery_questions: list[str] = []


class LeadPatch(BaseModel):
    name: Optional[str] = Field(default=None, max_length=120)
    email: Optional[str] = None
    phone: Optional[str] = Field(default=None, max_length=20)
    company_name: Optional[str] = Field(default=None, max_length=200)
    industry: Optional[str] = Field(default=None, max_length=120)
    status: Optional[Literal["new", "contacted", "qualified", "proposal", "won",
                             "lost", "archived", "spam", "closed"]] = None


class QualityScore(BaseModel):
    accuracy: int
    completeness: int
    professional: int
    seo: int
    overall: int
    flags: list[str] = []
    passed: bool


# ── RAG knowledge system ──

class RagIntent(str):
    ABOUT_RAJIB = "ABOUT_RAJIB"
    ABOUT_RAJIBLABS = "ABOUT_RAJIBLABS"
    PROJECT_INFORMATION = "PROJECT_INFORMATION"
    GITHUB_INFORMATION = "GITHUB_INFORMATION"
    TECHNICAL_EXPERIENCE = "TECHNICAL_EXPERIENCE"
    CAREER_INFORMATION = "CAREER_INFORMATION"
    SERVICES = "SERVICES"
    PRODUCTS = "PRODUCTS"
    BUSINESS_INQUIRY = "BUSINESS_INQUIRY"
    IDEA_SUBMISSION = "IDEA_SUBMISSION"
    RECRUITER = "RECRUITER"
    WORK_WITH_RAJIBLABS = "WORK_WITH_RAJIBLABS"
    GENERAL = "GENERAL"


RAG_INTENTS = (
    "ABOUT_RAJIB", "ABOUT_RAJIBLABS", "PROJECT_INFORMATION",
    "GITHUB_INFORMATION", "TECHNICAL_EXPERIENCE", "CAREER_INFORMATION",
    "SERVICES", "PRODUCTS", "BUSINESS_INQUIRY", "IDEA_SUBMISSION",
    "RECRUITER", "WORK_WITH_RAJIBLABS", "GENERAL",
)

# Intents that continue through the lead/business discovery flow.
LEAD_FLOW_INTENTS = frozenset(
    {"BUSINESS_INQUIRY", "IDEA_SUBMISSION", "WORK_WITH_RAJIBLABS"})

# Valid knowledge source types (§4). Anything else is rejected at ingestion.
RAG_SOURCE_TYPES = frozenset({
    "resume", "profile", "project", "product", "service", "case_study",
    "wip", "github_repository", "github_readme", "github_documentation",
    "github_commit", "github_issue", "website_content", "admin_knowledge",
})


class KnowledgeDocumentIn(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    content: str = Field(min_length=10, max_length=60000)
    source_type: str = "admin_knowledge"
    # Stable dedup identity. When omitted on admin create, one is derived
    # from the title hash (admin:<slug>) so re-posts update instead of dup.
    source_id: Optional[str] = Field(default=None, max_length=300)
    url: Optional[str] = None
    repository: Optional[str] = None
    language: Optional[str] = None
    tags: list[str] = []
    visibility: Literal["public"] = "public"
    guardrails: Optional[dict] = None
    hallucination_control: Optional[dict] = None


class KnowledgeDocumentPatch(BaseModel):
    title: Optional[str] = Field(default=None, min_length=2, max_length=200)
    content: Optional[str] = Field(default=None, min_length=10, max_length=60000)
    url: Optional[str] = None
    repository: Optional[str] = None
    language: Optional[str] = None
    tags: Optional[list[str]] = None
    status: Optional[Literal["active", "inactive"]] = None
    guardrails: Optional[dict] = None
    hallucination_control: Optional[dict] = None


class RetrievedChunk(BaseModel):
    chunk_id: str
    document_id: str
    score: float
    source_type: str
    title: str
    url: Optional[str] = None


class RagAnswer(BaseModel):
    answer: str
    intent: str
    sources: list[RetrievedChunk] = []
    grounded: bool = True


class RagQueryIn(BaseModel):
    question: str = Field(min_length=2, max_length=1000)
    session_id: Optional[str] = Field(default=None, max_length=64)
    top_k: int = Field(default=5, ge=1, le=20)
    language: str = Field(default="en", max_length=12)


class RagEvaluateItem(BaseModel):
    question: str = Field(min_length=2, max_length=1000)
    expected_keywords: list[str] = Field(min_length=1, max_length=10)
    intent_hint: Optional[str] = None
    top_k: int = Field(default=5, ge=1, le=20)


class RagEvaluateIn(BaseModel):
    items: list[RagEvaluateItem] = Field(min_length=1, max_length=25)


# ── Admin AI Proposal Studio (workbench) ──

WorkbenchMode = Literal["cover_letter", "freelance_proposal", "client_proposal",
                        "job_application", "project_summary", "project_explanation",
                        "custom"]
WORKBENCH_MODES = ("cover_letter", "freelance_proposal", "client_proposal",
                   "job_application", "project_summary", "project_explanation",
                   "custom")

ProposalStatus = Literal["draft", "ready", "submitted", "won", "lost", "archived"]
PROPOSAL_STATUSES = ("draft", "ready", "submitted", "won", "lost", "archived")


class RequirementAnalysis(BaseModel):
    title: str = ""
    company: str = ""
    industry: str = ""
    required_skills: list[str] = []
    preferred_skills: list[str] = []
    years_experience: str = ""
    project_type: str = ""
    business_problem: str = ""
    responsibilities: list[str] = []
    deliverables: list[str] = []
    technologies: list[str] = []
    ai_requirements: list[str] = []
    cloud_requirements: list[str] = []
    database_requirements: list[str] = []
    keywords: list[str] = []
    concerns: list[str] = []
    pain_points: list[str] = []


class ExperienceMatch(BaseModel):
    requirement: str
    experience: str = ""
    project: str = ""
    evidence: str = ""
    url: str = ""


class ProposalSource(BaseModel):
    title: str
    type: str = "project"
    url: str = ""
    reason: str = ""


class MatchReport(BaseModel):
    match_score: int = 0
    strengths: list[str] = []
    gaps: list[str] = []


class ProposalResult(BaseModel):
    analysis: RequirementAnalysis = RequirementAnalysis()
    match: MatchReport = MatchReport()
    relevant_experience: list[ExperienceMatch] = []
    proposal: str = ""
    cover_letter: str = ""
    short_summary: str = ""
    sources: list[ProposalSource] = []
    quality: dict[str, Any] = {}
    ai_generated: bool = True


class AnalyzeIn(BaseModel):
    job_description: str = Field(min_length=20, max_length=20000)
    mode: WorkbenchMode = "freelance_proposal"
    session_id: Optional[str] = Field(default=None, max_length=64)
    company: Optional[str] = Field(default=None, max_length=200)
    instructions: Optional[str] = Field(default=None, max_length=2000)


class GenerateIn(BaseModel):
    job_description: str = Field(min_length=20, max_length=20000)
    mode: WorkbenchMode = "freelance_proposal"
    analysis: Optional[RequirementAnalysis] = None
    tone: str = Field(default="professional", max_length=40)
    length: str = Field(default="standard", max_length=40)
    source_ids: list[str] = []
    language: str = Field(default="en", max_length=12)
    session_id: Optional[str] = Field(default=None, max_length=64)
    company: Optional[str] = Field(default=None, max_length=200)
    instructions: Optional[str] = Field(default=None, max_length=2000)


class RefineIn(BaseModel):
    session_id: Optional[str] = None
    document_id: Optional[str] = None
    target: str = Field(default="proposal", max_length=20)  # proposal|cover_letter|summary
    instruction: str = Field(min_length=2, max_length=2000)


class ProposalSaveIn(BaseModel):
    type: WorkbenchMode = "freelance_proposal"
    title: str = Field(min_length=2, max_length=200)
    job_description: str = Field(min_length=20, max_length=20000)
    analysis: RequirementAnalysis = RequirementAnalysis()
    match: MatchReport = MatchReport()
    relevant_experience: list[ExperienceMatch] = []
    proposal: str = ""
    cover_letter: str = ""
    summary: str = ""
    explanation: str = ""
    sources: list[ProposalSource] = []
    status: ProposalStatus = "draft"
    session_id: Optional[str] = None


class ProposalStatusIn(BaseModel):
    status: ProposalStatus


class WorkbenchChatIn(BaseModel):
    session_id: Optional[str] = Field(default=None, max_length=64)
    message: str = Field(min_length=1, max_length=4000)
    mode: WorkbenchMode = "freelance_proposal"
    language: str = Field(default="en", max_length=12)


# ── Multilingual framework (languages / translations / cache) ──

class LanguageIn(BaseModel):
    code: str = Field(min_length=2, max_length=12)
    name: str = Field(min_length=2, max_length=80)
    native_name: str = Field(min_length=1, max_length=80)
    enabled: bool = True
    direction: Literal["ltr", "rtl"] = "ltr"
    sort_order: int = 100


class LanguagePatch(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=80)
    native_name: Optional[str] = Field(default=None, min_length=1, max_length=80)
    direction: Optional[Literal["ltr", "rtl"]] = None
    sort_order: Optional[int] = None


class LanguageStatusIn(BaseModel):
    enabled: bool


class TranslationGenerateIn(BaseModel):
    target_language: str = Field(min_length=2, max_length=12)
    keys: list[str] = Field(default=[], max_length=200)
    limit: int = Field(default=50, ge=1, le=200)
    force: bool = False  # regenerate even when a valid translation exists


class TranslationEditIn(BaseModel):
    translated_text: str = Field(min_length=1, max_length=20000)


class TranslateIn(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    target_language: str = Field(min_length=2, max_length=12)
    source_language: str = Field(default="en", max_length=12)
    context: str = Field(default="", max_length=1000)

