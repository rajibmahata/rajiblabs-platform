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
    "portfolio": [("slug", 1)],
    "products": [("slug", 1)],
    "website_contents": [("key", 1)],
}

# Legacy (.NET-parity) seeds: Page Flow + DocuFlow products, home_order content,
# and the Rajib Mahata profile (mirrors the removed .NET SeedData/SeedCms).
SEED_PRODUCTS = [
    {"name": "Page Flow", "slug": "page-flow", "category": "RajibLabs Product",
     "description": "Visual workflow builder for document-intensive business processes — drag-drop pipeline designer, sequential/parallel approvals, HMAC-SHA256 token auth, audit trail, white-label API. Powers DocSignerHub and Solicitor CMS.",
     "features": ["Visual workflow designer", "Sequential & parallel approvals",
                  "HMAC-SHA256 secure tokens", "Full audit trail", "White-label API",
                  "140+ REST endpoints"],
     "tech_stack": [".NET 8", "React", "Blazor", "Azure", "SQL Server", "OpenAI"],
     "architecture": "Microservices + CQRS + Event-driven",
     "ai_capabilities": "AI clause analysis, document intelligence",
     "status": "published", "featured": True, "display_order": 1},
    {"name": "DocuFlow", "slug": "docuflow", "category": "SaaS",
     "description": "Enterprise document automation platform — template-driven generation, deadline tracking, client portal.",
     "features": ["Template engine", "Deadline tracking"],
     "tech_stack": [".NET 8", "Blazor", "Cosmos DB"],
     "status": "published", "featured": False, "display_order": 2},
]

SEED_PROFILE = {
    "full_name": "Rajib Mahata",
    "title": "Senior Software Architect | AI & SaaS Platform Builder",
    "bio": "Independent software architect with 10+ years building production SaaS platforms, AI systems, and cloud-native applications. Specialising in .NET, Azure, and AI/LLM integrations.",
    "skills": [".NET 8/10", "C#", "ASP.NET Core", "Blazor", "React", "Python FastAPI",
               "Azure Cloud", "Azure DevOps", "Microservices", "CQRS & Design Patterns",
               "SQL Server", "Cosmos DB", "OpenAI/Gemini APIs", "RAG Systems", "Docker",
               "GitHub Copilot"],
    "social_links": {"github": "https://github.com/rajibmahata",
                     "linkedin": "https://linkedin.com/in/rajib-mahata"},
    "career": [
        {"company": "Fortune 500 Healthcare", "role": "Solutions Architect",
         "period": "Aug 2019 – Present", "client": "Healthcare & Pharmacy (USA)",
         "achievements": [
             "Led development of open APIs, reducing pharmacy vendor dependency by 100%",
             "Architected data lake on Azure for raw prescription/patient data ingestion and processing",
             "Automated Prescription Refill System — 30% faster processing, 40% fewer medication errors",
             "Vaccine Appointment System — streamlined COVID-19 immunization scheduling nationally",
             "Built Rule Engine (CQRS) on Azure PaaS processing 500K+ daily prescription events",
             "Deployed PWAs on Azure Cloud for secure, scalable pharmacy interfaces",
             "Integrated secure payment (MParks), barcode scanning, voice/SMS notifications"],
         "tech_stack": [".NET 8", "Blazor", "Azure Functions", "Logic Apps", "Service Bus",
                        "Event Grid", "Cosmos DB", "Azure Data Factory", "AngularJS", "Open API"]},
        {"company": "Telecom Enterprise", "role": "Platform Engineer",
         "period": "Jul 2016 – Feb 2019", "client": "Telecommunications (USA)",
         "achievements": [
             "Designed and built CMT application automating network equipment provisioning",
             "Reduced manual intervention by 30%, processing time by 40%",
             "Achieved 95% issue resolution within 24 hours via automated ticket system",
             "Built intuitive UI improving user satisfaction scores by 25%"],
         "tech_stack": ["ASP.NET MVC", "WCF", "Entity Framework", "SQL Server", "JavaScript"]},
        {"company": "Product Studio", "role": "Full-Stack Developer",
         "period": "Mar 2013 – Apr 2016", "client": "",
         "achievements": [
             "Built Corporate Hour — B2B media advertisement & trade platform",
             "Developed Cinematic Lens — product visual storytelling platform",
             "Created TRANSZOOM — car rental & TruckIt365 freight matching solution",
             "Full-stack ownership: database design to frontend deployment"],
         "tech_stack": ["ASP.NET MVC", "SQL Server", "JavaScript", "HTML/CSS", "AJAX"]},
    ],
    "phone": "+91 84202 49020", "whatsapp": "+91 84202 49020",
}

# Legacy (.NET-parity) project + activity seeds (mirrors removed .NET SeedData).
# Timestamps are relative at seed time; migration preserves real values.
SEED_LEGACY_PROJECTS = [
    {"title": "DocSignerHub", "slug": "docsignerhub",
     "description": "Digital signature SaaS platform with AI clause analysis, blockchain notarisation, visual workflow builder, and Stripe payment integration. 140+ REST API endpoints.",
     "tech_stack": [".NET 8", "React", "SQL Server", "Azure", "Stripe", "OpenAI"],
     "github_url": "https://github.com/rajibmahata/DocumentSigningPlatform",
     "live_url": "https://docsignerhub.com", "status": "development"},
    {"title": "AI Avatar RAG Platform", "slug": "ai-avatar-rag",
     "description": "Enterprise AI knowledge retrieval platform with avatar-based interaction, semantic search, and RAG pipelines.",
     "tech_stack": ["Python", "FastAPI", "OpenAI", "RAG", "Vector DB", "React"],
     "github_url": "https://github.com/rajibmahata/AI-Avatar-RAG-Platform",
     "live_url": None, "status": "development"},
    {"title": "Solicitor Case Management", "slug": "solicitor-cms",
     "description": "Legal enterprise workflow platform for case tracking, document management, and client communication.",
     "tech_stack": [".NET 8", "Blazor", "SQL Server", "Azure", "Cosmos DB"],
     "github_url": "https://github.com/rajibmahata/SolicitorCaseManagementSystem",
     "live_url": None, "status": "planning"},
    {"title": "Rajib Labs Platform", "slug": "rajiblabs",
     "description": "AI-powered portfolio and software lab. Auto-populated from GitHub, managed by OpenClaw agents. This very platform.",
     "tech_stack": [".NET 8", "React", "TypeScript", "Tailwind CSS", "SQLite", "OpenClaw"],
     "github_url": "https://github.com/rajibmahata/rajiblabs-platform",
     "live_url": None, "status": "development"},
]

SEED_ACTIVITIES = [
    # (project_slug, type, title, description)
    ("rajiblabs", "milestone", "Rajib Labs Platform — Design upgrade",
     "Modern glass-morphism UI with animations + SQLite backend live"),
    ("docsignerhub", "commit", "DocSignerHub — Auth refactor merged",
     "Middleware cleanup, API rate limiting, security hardening"),
    ("ai-avatar-rag", "milestone", "RAG Platform — Embedding pipeline live",
     "Hybrid vector search with semantic ranking operational"),
    ("docsignerhub", "deploy", "DocSignerHub — Blog system shipped",
     "AI-generated tutorial blogs live on docsignerhub.com/blog"),
    ("solicitor-cms", "commit", "Solicitor CMS — Workflow diagram module",
     "Visual case flow builder prototype in progress"),
    ("rajiblabs", "commit", "Rajib Labs — Initial scaffold",
     "React + .NET 8 + SQLite backend deployed, 4 projects seeded"),
]


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
    from app.config import get_settings
    settings = get_settings()
    db = get_db() if db is None else db
    for coll, keys in {
        "projects": [[("slug", 1)], [("published", 1)], [("featured", 1)], [("display_order", 1)]],
        "github_repositories": [[("github_id", 1)], [("full_name", 1)]],
        "github_commits": [[("repository_id", 1), ("committed_at", -1)]],
        "customer_leads": [[("status", 1)], [("created_at", -1)]],
        "notifications": [[("is_read", 1)], [("created_at", -1)]],
        "admins": [[("emails", 1)]],
        "portfolio": [[("slug", 1)]],
        "products": [[("slug", 1)]],
        "website_contents": [[("key", 1)]],
        "legacy_projects": [[("legacy_id", 1)], [("slug", 1)]],
        "activities": [[("project_id", 1)], [("timestamp", -1)]],
        "courses": [[("url", 1)]],
        "subscribers": [[("email", 1)]],
        "portfolio": [[("legacy_id", 1)], [("slug", 1)], [("status", 1)]],
        "legacy_repos": [[("legacy_id", 1)], [("github_id", 1)]],
        "sync_logs": [[("started_at", -1)]],
        "resume_extractions": [[("resume_id", 1)]],
        "error_logs": [[("level", 1), ("created_at", -1)], [("source", 1), ("created_at", -1)]],
    }.items():
        for key in keys:
            try:
                await db[coll].create_index(key, background=True)
            except Exception as e:
                log.warning("Index failed %s %s: %s", coll, key, e)
    # Failure-log retention: TTL index auto-deletes entries older than
    # LOG_RETENTION_DAYS (default 5). Rebuilt if the setting changed.
    try:
        ttl_seconds = max(1, settings.log_retention_days) * 86400
        info = await db["error_logs"].index_information()
        for name, spec in info.items():
            if spec.get("expireAfterSeconds") is not None and spec.get("expireAfterSeconds") != ttl_seconds:
                await db["error_logs"].drop_index(name)
        await db["error_logs"].create_index(
            [("created_at", 1)], expireAfterSeconds=ttl_seconds,
            background=True, name="created_at_ttl")
    except Exception as e:
        log.warning("TTL index failed error_logs: %s", e)


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
    # Legacy (.NET-parity) seeds — only when collections are empty.
    if await db["products"].count_documents({}) == 0:
        for p in SEED_PRODUCTS:
            await db["products"].insert_one(
                {**p, "screenshots": [], "logo_url": None, "product_url": None,
                 "github_repo_id": None, "created_at": utcnow(), "updated_at": utcnow()})
        log.info("Seeded legacy products (Page Flow, DocuFlow)")
    if await db["website_contents"].count_documents({}) == 0:
        await db["website_contents"].insert_one({
            "key": "home_order", "title": "Home Section Order",
            "body_json": '["hero","overview","about","whatido","expertise","ai","products",'
                         '"architecture","experience","projects","insights","contact"]',
            "updated_at": utcnow()})
    if await db["profiles"].count_documents({}) == 0:
        await db["profiles"].insert_one({**SEED_PROFILE, "updated_at": utcnow()})
        log.info("Seeded legacy profile")
    if await db["legacy_projects"].count_documents({}) == 0:
        import uuid as _uuid
        from datetime import timedelta as _td
        now = utcnow()
        slug_to_id: dict[str, str] = {}
        for i, p in enumerate(SEED_LEGACY_PROJECTS):
            lid = _uuid.uuid4().hex
            slug_to_id[p["slug"]] = lid
            await db["legacy_projects"].insert_one({
                **p, "legacy_id": lid, "created_at": now - _td(days=90 - i * 10),
                "updated_at": now - _td(hours=i * 5),
                "last_commit_at": now - _td(hours=i * 5 + 1)})
        for slug, atype, title, desc in SEED_ACTIVITIES:
            await db["activities"].insert_one({
                "legacy_id": _uuid.uuid4().hex, "project_id": slug_to_id[slug],
                "type": atype, "title": title, "description": desc, "timestamp": now})
        log.info("Seeded legacy projects + activities")
    if await db["resumes"].count_documents({}) == 0:
        seed_pdf = Path(__file__).resolve().parent.parent / "data" / "Rajib-Mahata-Resume-2026.pdf"
        if seed_pdf.is_file():
            updir = Path(settings.upload_dir) / "resumes"
            updir.mkdir(parents=True, exist_ok=True)
            dest = updir / "Rajib-Mahata-Resume-2026.pdf"
            try:
                if not dest.is_file():
                    dest.write_bytes(seed_pdf.read_bytes())
            except Exception as e:
                log.warning("Resume seed copy failed: %s", e)
            import os
            await db["resumes"].insert_one({
                "file_name": "Rajib-Mahata-Resume-2026.pdf", "stored_path": str(dest),
                "content_type": "application/pdf", "size_bytes": os.path.getsize(dest),
                "version": 1, "status": "published",
                "uploaded_at": utcnow(), "published_at": utcnow()})
            log.info("Seeded legacy resume v1")
