"""MongoDB connection (Motor async), indexes, and seed data. Replaces SQLite."""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import get_settings

log = logging.getLogger("rajiblabs")

_clients: dict[int, AsyncIOMotorClient] = {}


def get_client() -> AsyncIOMotorClient:
    """Cache Motor client per event loop (tests create a new loop per test)."""
    import asyncio
    try:
        loop_id = id(asyncio.get_running_loop())
    except RuntimeError:
        loop_id = 0
    if loop_id not in _clients:
        settings = get_settings()
        _clients[loop_id] = AsyncIOMotorClient(settings.database_url, serverSelectionTimeoutMS=5000)
    return _clients[loop_id]


def get_db() -> AsyncIOMotorDatabase:
    settings = get_settings()
    return get_client()[settings.mongo_db_name]


async def get_db_dep() -> AsyncIOMotorDatabase:
    return get_db()


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


INDEXES: dict[str, list[tuple]] = {
    "projects": [("slug", 1), ("published", 1), ("featured", 1), ("display_order", 1)],
    "github_repositories": [("github_id", 1), ("full_name", 1)],
    "github_commits": [("repository_id", 1), ("committed_at", -1)],
    "customer_leads": [("status", 1), ("created_at", -1)],
    "notifications": [("is_read", 1), ("created_at", -1)],
    "ai_jobs": [("status", 1), ("input_hash", 1)],
}

SEED_HOME = [
    ("hero", "RajibLabs", "Enterprise software & AI product development", {
        "headline": "I design and build the software systems companies run on.",
        "lede": "Twelve years shipping enterprise platforms on .NET and Azure. Production systems for real businesses, and AI-native products under RajibLabs.",
    }, 1),
    ("about", "About", "Architecture thinking, AI-native delivery", {
        "paragraphs": [
            "Rajib Mahata is a Senior .NET and Azure Solutions Architect with twelve years of enterprise delivery experience.",
            "He runs RajibLabs, an independent studio taking products from first sketch to production.",
        ]
    }, 2),
    ("process", "How engagements work", "Discover → Design → Build → Deliver", {
        "steps": [
            {"name": "Discover", "desc": "Understand the business problem before writing any code."},
            {"name": "Design", "desc": "Sketch the approach and lay out the technical architecture."},
            {"name": "Build", "desc": "Implement in focused iterations, with working software early."},
            {"name": "Deliver", "desc": "Ship, gather feedback, and stay on to support what's live."},
        ]
    }, 3),
    ("cta", "Let's build something intelligent", "", {"lede": "Reach out about a project, a technical problem, or a collaboration."}, 4),
    ("metrics", "Results", "", {"items": [
        {"num": "12+", "label": "years of enterprise software delivery"},
        {"num": "6", "label": "products and platforms built under RajibLabs"},
        {"num": "2", "label": "client platforms live in production today"},
    ]}, 5),
]

SEED_SKILLS = [
    ("Backend & architecture", ["C#", ".NET", "ASP.NET Core", "EF Core", "REST APIs", "Microservices"]),
    ("Cloud & DevOps", ["Azure", "Docker", "Docker Compose", "CI/CD", "Azure DevOps"]),
    ("Data & AI", ["SQL Server", "RAG pipelines", "LLM integration", "Vector search", "Prompt engineering"]),
    ("Frontend", ["React", "JavaScript", "HTML & CSS", "Responsive UI"]),
]

SEED_EXPERIENCE = [
    ("TCS", "Assistant Consultant — Meijer pharmacy account", "Aug 2019 — Present",
     "Building the systems behind pharmacy digital transformation and prescription automation."),
    ("Accenture", "Enterprise Software Delivery — Cincinnati Bell account", "Jul 2016 — Feb 2019",
     "Enterprise software delivery on the Cincinnati Bell engagement."),
    ("Keshri Software Solutions", "Enterprise Software Developer", "Mar 2013 — Apr 2016",
     "Started his career in enterprise software development."),
]

# Verified seed projects — github_url NULL until verified per spec §87 (never fabricate).
SEED_PROJECTS = [
    {"slug": "pestflow", "name": "PestFlow", "category": "product",
     "short_description": "Pest-control business platform (.NET, SQL Server, multi-tenant).",
     "technologies": [".NET", "SQL Server", "SignalR"], "featured": True, "published": True, "display_order": 1,
     "github_url": "https://github.com/rajibmahata/pestflow", "status": "published"},
    {"slug": "aria", "name": "ARIA", "category": "product",
     "short_description": "AI product with YouTube demo.",
     "technologies": ["AI", "LLM"], "featured": False, "published": True, "display_order": 2,
     "github_url": None, "demo_video_url": "https://youtu.be/6p5-A9PWn0E?si=hc4Ee8k3XQWRXf7F", "status": "published"},
    {"slug": "docusign-hub", "name": "DocuSign Hub", "category": "product",
     "short_description": "Document signing product with demo video.",
     "technologies": [".NET", "React"], "featured": False, "published": True, "display_order": 3,
     "github_url": None, "demo_video_url": "https://youtu.be/f4Y_l0h4Xt0?si=J-65kJsbKTJ9lKZe", "status": "published"},
    {"slug": "rm-enterprise", "name": "R.M. Enterprise", "category": "product",
     "short_description": "Business Website + CMS.",
     "technologies": ["Web", "CMS"], "featured": False, "published": True, "display_order": 4,
     "github_url": None, "live_url": "https://fryyofoods.com/", "status": "published"},
    {"slug": "apcs-pest-control", "name": "APCS Pest Control", "category": "project",
     "short_description": "Real business software for pest control.",
     "technologies": ["Web"], "featured": False, "published": True, "display_order": 5,
     "github_url": None, "live_url": "https://apcspestcontrol.com/", "status": "published"},
]


async def ensure_indexes(db=None) -> None:
    db = db or get_db()
    for coll, keys in {
        "projects": [[("slug", 1)], [("published", 1)], [("featured", 1)], [("display_order", 1)]],
        "github_repositories": [[("github_id", 1)], [("full_name", 1)]],
        "github_commits": [[("repository_id", 1), ("committed_at", -1)]],
        "customer_leads": [[("status", 1)], [("created_at", -1)]],
        "notifications": [[("is_read", 1)], [("created_at", -1)]],
        "admins": [[("emails", 1)]],
    }.items():
        for key in keys:
            try:
                await db[coll].create_index(key, background=True)
            except Exception as e:
                log.warning("Index failed %s %s: %s", coll, key, e)


async def init_db() -> None:
    settings = get_settings()
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    db = get_db()
    await ensure_indexes(db)
    if await db["homepage_content"].count_documents({}) == 0:
        for key, title, subtitle, body, order in SEED_HOME:
            await db["homepage_content"].insert_one({
                "section_key": key, "title": title, "subtitle": subtitle,
                "body": body, "display_order": order, "status": "published",
                "updated_at": utcnow()})
        log.info("Seeded homepage_content")
    if await db["skills"].count_documents({}) == 0:
        n = 0
        for category, names in SEED_SKILLS:
            for name in names:
                n += 1
                await db["skills"].insert_one({
                    "category": category, "name": name, "display_order": n, "status": "published"})
    if await db["experience"].count_documents({}) == 0:
        for i, (company, role, dates, desc) in enumerate(SEED_EXPERIENCE, 1):
            await db["experience"].insert_one({
                "company": company, "role": role, "date_range": dates,
                "description": desc, "achievements": [], "technologies": [],
                "display_order": i, "status": "published"})
    if await db["projects"].count_documents({}) == 0:
        for p in SEED_PROJECTS:
            await db["projects"].insert_one({**p, "created_at": utcnow(), "updated_at": utcnow()})
        log.info("Seeded verified projects (github NULL unless verified)")
    if await db["site_settings"].count_documents({}) == 0:
        await db["site_settings"].insert_many([
            {"key": "contact", "value": {
                "emails": ["rajibmahata143@gmail.com", "rajibmahata143@outlook.com"],
                "primary_phone": "+918420249020", "secondary_phone": "+919100184730",
                "whatsapp": "https://wa.me/918420249020"}, "updated_at": utcnow()},
        ])
