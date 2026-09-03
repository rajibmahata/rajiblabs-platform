"""Server-side GitHub sync (token never leaves backend)."""
import hashlib
import logging
from datetime import datetime, timezone
import httpx

from app.config import get_settings
from app.database import get_db, utcnow

log = logging.getLogger("rajiblabs")
API = "https://api.github.com"


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
            "User-Agent": "RajibLabs-CMS", "X-GitHub-Api-Version": "2022-11-28"}


async def fetch_repos(owner: str, token: str, per_page: int = 100) -> list[dict]:
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(f"{API}/users/{owner}/repos",
                             params={"per_page": per_page, "sort": "updated"},
                             headers=_headers(token))
        r.raise_for_status()
        return r.json()


async def fetch_readme(owner: str, repo: str, token: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(f"{API}/repos/{owner}/{repo}/readme",
                                 headers={**_headers(token), "Accept": "application/vnd.github.raw"})
            if r.status_code == 200:
                return r.text[:8000]
    except Exception as e:
        log.warning("readme fetch failed %s: %s", repo, e)
    return ""


def classify(name: str, desc: str, lang: str) -> str:
    t = f"{name} {desc}".lower()
    if any(k in t for k in ("ai", "llm", "rag", "gpt", "agent")) or lang == "Python":
        return "ai"
    if "saas" in t or "multi-tenant" in t:
        return "saas"
    return "product"


async def sync_now() -> dict:
    s = get_settings()
    if not s.is_github_configured():
        raise RuntimeError("GITHUB_TOKEN not configured")
    db = get_db()
    run = await db["github_sync_runs"].insert_one(
        {"started_at": utcnow(), "status": "running", "found": 0, "added": 0, "updated": 0, "errors": []})
    run_id = run.inserted_id
    try:
        repos = await fetch_repos(s.github_owner, s.github_token)
        found, added, updated = len(repos), 0, 0
        for r in repos:
            gid = r.get("id")
            existing = await db["github_repositories"].find_one({"github_id": gid})
            readme = await fetch_readme(s.github_owner, r.get("name", ""), s.github_token) if not existing else (existing.get("readme") or "")
            doc = {
                "github_id": gid, "name": r.get("name", ""), "full_name": r.get("full_name", ""),
                "html_url": r.get("html_url", ""), "description": r.get("description") or "",
                "language": r.get("language") or "", "topics": r.get("topics", []),
                "stars": r.get("stargazers_count", 0), "default_branch": r.get("default_branch", "main"),
                "is_private": bool(r.get("private")), "readme": readme,
                "readme_hash": hashlib.sha256(readme.encode()).hexdigest()[:16],
                "pushed_at": r.get("pushed_at"), "classification": classify(r.get("name", ""), r.get("description") or "", r.get("language") or ""),
                "last_synced_at": utcnow(),
            }
            if not existing:
                doc.update({"sync_status": "new", "is_manually_edited": False})
                await db["github_repositories"].insert_one(doc)
                added += 1
            elif not existing.get("is_manually_edited"):
                await db["github_repositories"].update_one({"_id": existing["_id"]}, {"$set": doc})
                updated += 1
            else:
                updated += 0  # preserve manual edits
        await db["github_sync_runs"].update_one({"_id": run_id}, {"$set": {
            "status": "success", "finished_at": utcnow(), "found": found, "added": added, "updated": updated}})
        await db["notifications"].insert_one({
            "type": "GITHUB_UPDATE", "title": "GitHub sync complete",
            "message": f"Found {found}, added {added}, updated {updated}",
            "is_read": False, "created_at": utcnow()})
        return {"found": found, "added": added, "updated": updated}
    except Exception as e:
        await db["github_sync_runs"].update_one({"_id": run_id}, {"$set": {
            "status": "failed", "finished_at": utcnow(), "errors": [str(e)]}})
        try:
            from app.services.notify import log_error
            await log_error("github_sync", "GitHub sync failed", str(e)[:2000])
        except Exception:
            pass
        raise
