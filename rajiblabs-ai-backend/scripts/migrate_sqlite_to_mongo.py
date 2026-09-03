"""One-shot SQLite (removed .NET backend) → Mongo migration.

Migrates every table, preserving IDs as `legacy_id` so admin links keep
working. Safe to re-run: existing docs (matched by `legacy_id`, slug, key,
url or email) are skipped, never overwritten.

`backend/` was deleted from the repo — extract rajiblabs.db from git history
(e.g. `git show <sha>:backend/RajibLabs.Api/rajiblabs.db > /tmp/rajiblabs.db`)
and pass its path explicitly.

Usage: `python scripts/migrate_sqlite_to_mongo.py /tmp/rajiblabs.db`
"""
import asyncio
import json
import sqlite3
import sys
sys.path.insert(0, ".")
from app.database import get_db, utcnow


TABLES = ("Projects", "Activities", "Profiles", "Contacts", "LinkedInCourses",
          "Subscribers", "AdminUsers", "Resumes", "ResumeExtractions",
          "PortfolioProjects", "Products", "GitHubRepositories",
          "ProjectSyncLogs", "WebsiteContents")


def load_sqlite(path: str) -> dict:
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    out: dict = {}
    for tbl in TABLES:
        try:
            out[tbl] = [dict(r) for r in con.execute(f'SELECT * FROM "{tbl}"')]
        except Exception as e:
            print(f"  skip {tbl}: {e}")
            out[tbl] = []
    con.close()
    return out


def _j(raw: str | None, default):
    if not raw:
        return default
    try:
        return json.loads(raw)
    except Exception:
        return default


async def main(sqlite_path: str):
    db = get_db()
    data = load_sqlite(sqlite_path)
    counts: dict[str, int] = {}

    async def insert_once(coll: str, filt: dict, doc: dict):
        if await db[coll].find_one(filt):
            return False
        await db[coll].insert_one(doc)
        return True

    # Projects → legacy_projects
    n = 0
    for p in data["Projects"]:
        lid = str(p.get("Id", ""))
        if await insert_once("legacy_projects", {"legacy_id": lid}, {
                "legacy_id": lid, "title": p.get("Title", ""), "slug": p.get("Slug", ""),
                "description": p.get("Description", ""),
                "tech_stack": _j(p.get("TechStackJson"), []),
                "github_url": p.get("GitHubUrl") or "", "live_url": p.get("LiveUrl"),
                "status": p.get("Status", "planning"),
                "created_at": p.get("CreatedAt"), "updated_at": p.get("UpdatedAt"),
                "last_commit_at": p.get("LastCommitAt")}):
            n += 1
    counts["legacy_projects"] = n

    # Activities → activities
    n = 0
    for a in data["Activities"]:
        lid = str(a.get("Id", ""))
        if await insert_once("activities", {"legacy_id": lid}, {
                "legacy_id": lid, "project_id": str(a.get("ProjectId", "")),
                "type": a.get("Type", "commit"), "title": a.get("Title", ""),
                "description": a.get("Description", ""), "timestamp": a.get("Timestamp")}):
            n += 1
    counts["activities"] = n

    # Profiles → profiles (single doc; skip if one already seeded)
    if data["Profiles"] and await db["profiles"].count_documents({}) == 0:
        p = data["Profiles"][0]
        await db["profiles"].insert_one({
            "legacy_id": str(p.get("Id", "")), "full_name": p.get("FullName", ""),
            "title": p.get("Title", ""), "bio": p.get("Bio", ""),
            "skills": _j(p.get("SkillsJson"), []), "social_links": _j(p.get("SocialLinksJson"), {}),
            "career": _j(p.get("CareerJson"), []), "headline": p.get("Headline"),
            "location": p.get("Location"), "phone": p.get("Phone"), "whatsapp": p.get("WhatsApp"),
            "email": p.get("Email"), "linkedin": p.get("LinkedIn"), "github": p.get("GitHub"),
            "website": p.get("Website"), "profile_image_url": p.get("ProfileImageUrl"),
            "updated_at": p.get("UpdatedAt") or utcnow()})
        counts["profiles"] = 1
    else:
        counts["profiles"] = 0

    # Contacts → contacts
    n = 0
    for c in data["Contacts"]:
        lid = str(c.get("Id", ""))
        if await insert_once("contacts", {"legacy_id": lid}, {
                "legacy_id": lid, "name": c.get("Name", ""), "email": c.get("Email", ""),
                "company": c.get("Company"), "message": c.get("Message", ""),
                "submitted_at": c.get("SubmittedAt")}):
            n += 1
    counts["contacts"] = n

    # LinkedInCourses → courses (match by url)
    n = 0
    for c in data["LinkedInCourses"]:
        if c.get("Url") and await db["courses"].find_one({"url": c["Url"]}):
            continue
        await db["courses"].insert_one({
            "legacy_id": str(c.get("Id", "")), "title": c.get("Title", ""), "url": c.get("Url", ""),
            "instructor": c.get("Instructor"), "duration": c.get("Duration"), "level": c.get("Level"),
            "completed_at": c.get("CompletedAt"), "status": c.get("Status", "in-progress"),
            "updated_at": c.get("UpdatedAt") or utcnow()})
        n += 1
    counts["courses"] = n

    # Subscribers → subscribers (match by email)
    n = 0
    for s in data["Subscribers"]:
        email = (s.get("Email") or "").strip().lower()
        if email and await db["subscribers"].find_one({"email": email}):
            continue
        await db["subscribers"].insert_one({
            "legacy_id": str(s.get("Id", "")), "email": email,
            "is_active": bool(s.get("IsActive", 1)),
            "subscribed_at": s.get("SubscribedAt") or utcnow(),
            "unsubscribed_at": s.get("UnsubscribedAt")})
        n += 1
    counts["subscribers"] = n

    # AdminUsers → admins (BCrypt hashes verify as-is via app.auth.utils)
    n = 0
    for u in data["AdminUsers"]:
        username = (u.get("Username") or "").strip().lower()
        if not username or await db["admins"].find_one({"emails": username}):
            continue
        await db["admins"].insert_one({
            "emails": [username], "password_hash": u.get("PasswordHash", ""),
            "created_at": u.get("CreatedAt") or utcnow(),
            "last_login_at": u.get("LastLoginAt")})
        n += 1
    counts["admins"] = n

    # Resumes → resumes (file bytes stay on disk; doc keeps StoredPath)
    n = 0
    for r in data["Resumes"]:
        lid = str(r.get("Id", ""))
        if await insert_once("resumes", {"legacy_id": lid}, {
                "legacy_id": lid, "filename": r.get("FileName", ""),
                "stored_rel": r.get("StoredPath", ""), "stored_path": r.get("StoredPath", ""),
                "content_type": r.get("ContentType", ""), "size_bytes": r.get("SizeBytes", 0),
                "version": r.get("Version", 1), "status": (r.get("Status") or "published").lower(),
                "active": (r.get("Status") or "") == "published",
                "uploaded_at": r.get("UploadedAt") or utcnow(),
                "published_at": r.get("PublishedAt")}):
            n += 1
    counts["resumes"] = n

    # ResumeExtractions → resume_extractions
    n = 0
    for e in data["ResumeExtractions"]:
        lid = str(e.get("Id", ""))
        if await insert_once("resume_extractions", {"legacy_id": lid}, {
                "legacy_id": lid, "resume_id": str(e.get("ResumeId", "")),
                "extracted_json": e.get("ExtractedJson", "{}"),
                "status": e.get("Status", "review"), "created_at": e.get("CreatedAt") or utcnow()}):
            n += 1
    counts["resume_extractions"] = n

    # PortfolioProjects → portfolio
    n = 0
    for p in data["PortfolioProjects"]:
        slug = (p.get("Slug") or "").strip().lower()
        if slug and await db["portfolio"].find_one({"slug": slug}):
            continue
        await db["portfolio"].insert_one({
            "legacy_id": str(p.get("Id", "")), "title": p.get("Title", ""), "slug": slug,
            "short_description": p.get("ShortDescription", ""), "description": p.get("Description", ""),
            "problem": p.get("Problem", ""), "solution": p.get("Solution", ""),
            "role": p.get("Role", ""), "architecture": p.get("Architecture", ""),
            "tech_stack": _j(p.get("TechStackJson"), []),
            "ai_capabilities": _j(p.get("AiCapabilitiesJson"), []),
            "cloud_capabilities": _j(p.get("CloudCapabilitiesJson"), []),
            "screenshots": _j(p.get("ScreenshotsJson"), []),
            "demo_url": p.get("DemoUrl"), "github_url": p.get("GitHubUrl"),
            "product_url": p.get("ProductUrl"), "status": p.get("Status", "draft"),
            "featured": bool(p.get("Featured", 0)), "display_order": p.get("DisplayOrder", 0),
            "created_at": p.get("CreatedAt") or utcnow(), "updated_at": p.get("UpdatedAt") or utcnow(),
            "published_at": p.get("PublishedAt"),
            "is_manual_edit": bool(p.get("IsManualEdit", 0))})
        n += 1
    counts["portfolio"] = n

    # Products → products (match by slug; keep seed if slug taken)
    n = 0
    for p in data["Products"]:
        slug = (p.get("Slug") or "").strip().lower()
        if slug and await db["products"].find_one({"slug": slug}):
            continue
        await db["products"].insert_one({
            "legacy_id": str(p.get("Id", "")), "name": p.get("Name", ""), "slug": slug,
            "category": p.get("Category", ""), "description": p.get("Description", ""),
            "logo_url": p.get("LogoUrl"), "screenshots": _j(p.get("ScreenshotsJson"), []),
            "features": _j(p.get("FeaturesJson"), []), "tech_stack": _j(p.get("TechStackJson"), []),
            "ai_capabilities": p.get("AiCapabilities"), "architecture": p.get("Architecture"),
            "product_url": p.get("ProductUrl"), "github_repo_id": p.get("GitHubRepoId"),
            "status": p.get("Status", "draft"), "featured": bool(p.get("Featured", 0)),
            "display_order": p.get("DisplayOrder", 0),
            "created_at": p.get("CreatedAt") or utcnow(), "updated_at": p.get("UpdatedAt") or utcnow()})
        n += 1
    counts["products"] = n

    # GitHubRepositories → legacy_repos
    n = 0
    for r in data["GitHubRepositories"]:
        gid = r.get("GitHubId")
        if gid is not None and await db["legacy_repos"].find_one({"github_id": gid}):
            continue
        await db["legacy_repos"].insert_one({
            "legacy_id": str(r.get("Id", "")), "github_id": gid, "name": r.get("Name", ""),
            "full_name": r.get("FullName", ""), "description": r.get("Description", ""),
            "html_url": r.get("HtmlUrl", ""), "language": r.get("Language", ""),
            "topics": _j(r.get("TopicsJson"), []), "stars": r.get("Stars", 0),
            "forks": r.get("Forks", 0), "readme": r.get("Readme"),
            "pushed_at": r.get("PushedAt"), "updated_at_github": r.get("UpdatedAtGitHub"),
            "is_private": bool(r.get("IsPrivate", 0)),
            "default_branch": r.get("DefaultBranch", "main"),
            "classification": r.get("Classification", "professional"),
            "ai_title": r.get("AiTitle"), "ai_summary": r.get("AiSummary"),
            "ai_problem": r.get("AiProblem"), "ai_tech_stack": r.get("AiTechStack"),
            "ai_confidence": r.get("AiConfidence", "low"),
            "sync_status": r.get("SyncStatus", "review"),
            "last_synced_at": r.get("LastSyncedAt") or utcnow(),
            "is_manually_edited": bool(r.get("IsManuallyEdited", 0)),
            "published_at": r.get("PublishedAt")})
        n += 1
    counts["legacy_repos"] = n

    # ProjectSyncLogs → sync_logs
    n = 0
    for s in data["ProjectSyncLogs"]:
        lid = str(s.get("Id", ""))
        if await insert_once("sync_logs", {"legacy_id": lid}, {
                "legacy_id": lid, "started_at": s.get("StartedAt") or utcnow(),
                "finished_at": s.get("FinishedAt"), "found": s.get("Found", 0),
                "added": s.get("Added", 0), "updated": s.get("Updated", 0),
                "ignored": s.get("Ignored", 0), "errors": _j(s.get("ErrorsJson"), [])}):
            n += 1
    counts["sync_logs"] = n

    # WebsiteContents → website_contents (match by key; keep seed if taken)
    n = 0
    for w in data["WebsiteContents"]:
        key = (w.get("Key") or "").strip()
        if key and await db["website_contents"].find_one({"key": key}):
            continue
        await db["website_contents"].insert_one({
            "legacy_id": str(w.get("Id", "")), "key": key, "title": w.get("Title", ""),
            "body_json": w.get("BodyJson", "{}"), "updated_at": w.get("UpdatedAt") or utcnow()})
        n += 1
    counts["website_contents"] = n

    print("Migration complete:")
    for coll, cnt in counts.items():
        print(f"  {coll}: +{cnt}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(2)
    asyncio.run(main(sys.argv[1]))
