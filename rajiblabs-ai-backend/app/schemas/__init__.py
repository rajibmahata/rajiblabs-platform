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
    message: str = Field(min_length=1, max_length=2000)
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


class LoginIn(BaseModel):
    email: str
    password: str


class QualityScore(BaseModel):
    accuracy: int
    completeness: int
    professional: int
    seo: int
    overall: int
    flags: list[str] = []
    passed: bool
