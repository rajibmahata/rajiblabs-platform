"""Server-side GitHub sync (token never leaves backend)."""
import hashlib
import logging
from datetime import datetime, timezone
import httpx

from app.config import get_settings
from app.database import get_db, utcnow

log = logging.getLogger("rajiblabs")
API = "https://api.github.com"
CONFIG_KEY = "github"  # site_settings.key holding the admin-configured token


def mask_token(token: str) -> str:
    """Last-4 display form. The full token is never returned or logged."""
    t = (token or "").strip()
    return ("***" + t[-4:]) if len(t) > 8 else ("***" if t else "")


async def get_stored_config(db=None) -> dict:
    """Admin-configured GitHub settings (token write-only elsewhere)."""
    db = get_db() if db is None else db
    doc = await db["site_settings"].find_one({"key": CONFIG_KEY})
    return (doc or {}).get("value", {}) if isinstance((doc or {}).get("value"), dict) else {}


async def resolve_github_token(db=None) -> str:
    """DB-configured token wins (admin can rotate without redeploy), else env."""
    cfg = await get_stored_config(db)
    token = (cfg.get("token") or "").strip()
    if token:
        return token
    return (get_settings().github_token or "").strip()


async def resolve_github_owner(db=None) -> str:
    cfg = await get_stored_config(db)
    return (cfg.get("owner") or "").strip() or get_settings().github_owner


async def token_status(db=None) -> dict:
    """Masked status for Admin — the full token is never exposed."""
    from app.config import get_settings as _gs
    db = get_db() if db is None else db
    cfg = await get_stored_config(db)
    stored = (cfg.get("token") or "").strip()
    env_tok = (_gs().github_token or "").strip()
    active = stored or env_tok
    return {
        "configured": bool(active),
        "source": "admin" if stored else ("env" if env_tok else "none"),
        "masked": mask_token(active),
        "owner": (cfg.get("owner") or "").strip() or _gs().github_owner,
        "updated_at": cfg.get("updated_at"),
    }


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
            "User-Agent": "RajibLabs-CMS", "X-GitHub-Api-Version": "2022-11-28"}


async def fetch_user(token: str) -> dict:
    """Validate a token + return public account info (for the Admin test)."""
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(f"{API}/user", headers=_headers(token))
        if r.status_code == 401:
            raise RuntimeError("invalid token (GitHub returned 401)")
        r.raise_for_status()
        u = r.json()
        return {"login": u.get("login", ""), "name": u.get("name") or "",
                "avatar_url": u.get("avatar_url") or "",
                "public_repos": u.get("public_repos", 0),
                "followers": u.get("followers", 0)}


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


# ── RAG ingestion helpers (same client/auth as sync — no duplicate client) ──

# Paths never ingested into the knowledge base (§9).
SKIP_PATH_PARTS = (
    ".git/", "node_modules/", "bin/", "obj/", "dist/", "build/",
    "coverage/", ".next/", ".nuxt/", "__pycache__/", ".venv/", "venv/",
)
SKIP_FILENAMES = (
    ".env", ".env.local", ".env.production", "secrets.json", "secrets.yaml",
    "secrets.yml", "secrets.toml", "credentials.json", "id_rsa", "id_dsa",
    "id_ecdsa", "id_ed25519", ".npmrc", ".pypirc", ".htpasswd", ".netrc",
)
SKIP_EXTENSIONS = (
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".svg", ".webp",
    ".mp4", ".mov", ".avi", ".mp3", ".wav", ".ogg", ".zip", ".tar",
    ".gz", ".rar", ".7z", ".exe", ".dll", ".so", ".dylib", ".bin",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".lock", ".map",
    ".pem", ".key", ".p12", ".pfx",
    ".h5", ".hdf5", ".parquet", ".pkl", ".pickle", ".sqlite", ".db",
)
# Small text files worth indexing even without a "docs-like" name.
PRIORITY_NAMES = (
    "readme", "architecture", "arch", "prd", "changelog", "contributing",
    "license", "overview", "design", "adr",
)
PRIORITY_DIRS = ("docs/", "doc/", ".github/", "src/", "app/", "frontend/", "backend/", "lib/")


def is_ingestible_path(path: str, size: int = 0, max_bytes: int = 60000) -> bool:
    """True if a repo file is safe + worthwhile to index. Never binaries/secrets."""
    p = (path or "").lower()
    if not p or size > max_bytes:
        return False
    if any(part in p for part in SKIP_PATH_PARTS):
        return False
    name = p.rsplit("/", 1)[-1]
    if name in SKIP_FILENAMES or name.startswith(".env"):
        return False
    if any(p.endswith(ext) for ext in SKIP_EXTENSIONS):
        return False
    return True


def prioritize_paths(paths: list[dict], max_files: int = 40) -> list[dict]:
    """Order repo files so the most meaningful ones embed first."""
    def rank(f: dict) -> tuple:
        p = (f.get("path") or "").lower()
        name = p.rsplit("/", 1)[-1]
        stem = name.rsplit(".", 1)[0] if "." in name else name
        score = 2
        if any(stem == k or stem.startswith(k + ".") or stem.startswith(k + "_")
               for k in PRIORITY_NAMES):
            score = 0
        elif any(p.startswith(d) for d in PRIORITY_DIRS):
            score = 1
        return (score, len(p))
    return sorted(paths, key=rank)[:max_files]


async def fetch_tree(owner: str, repo: str, token: str, branch: str = "") -> list[dict]:
    """Recursive file tree (blobs only). Empty list on any failure."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            ref = branch or "HEAD"
            r = await client.get(f"{API}/repos/{owner}/{repo}/git/trees/{ref}",
                                 params={"recursive": "1"}, headers=_headers(token))
            if r.status_code != 200:
                return []
            return [t for t in r.json().get("tree", []) if t.get("type") == "blob"]
    except Exception as e:
        log.warning("tree fetch failed %s/%s: %s", owner, repo, e)
        return []


async def fetch_file(owner: str, repo: str, path: str, token: str,
                     branch: str = "", max_bytes: int = 60000) -> str:
    """Raw file content (text only, truncated). Empty string on failure."""
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            params = {"ref": branch} if branch else {}
            r = await client.get(f"{API}/repos/{owner}/{repo}/contents/{path}",
                                 params=params,
                                 headers={**_headers(token),
                                          "Accept": "application/vnd.github.raw"})
            if r.status_code != 200:
                return ""
            text = r.text
            try:
                text.encode("utf-8")
            except Exception:
                return ""  # binary
            if "\x00" in text:
                return ""  # binary
            return text[:max_bytes]
    except Exception as e:
        log.warning("file fetch failed %s/%s %s: %s", owner, repo, path, e)
        return ""


async def fetch_commits(owner: str, repo: str, token: str, limit: int = 10) -> list[dict]:
    """Recent commits (messages only — no code). Empty list on failure."""
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(f"{API}/repos/{owner}/{repo}/commits",
                                 params={"per_page": max(1, min(limit, 30))},
                                 headers=_headers(token))
            if r.status_code != 200:
                return []
            out = []
            for c in r.json():
                commit = c.get("commit", {})
                out.append({
                    "sha": (c.get("sha") or "")[:7],
                    "message": (commit.get("message") or "")[:500],
                    "author": ((commit.get("author") or {}).get("name") or ""),
                    "date": (commit.get("author") or {}).get("date") or "",
                    "url": c.get("html_url", ""),
                })
            return out
    except Exception as e:
        log.warning("commits fetch failed %s/%s: %s", owner, repo, e)
        return []


async def fetch_issues(owner: str, repo: str, token: str, limit: int = 10) -> list[dict]:
    """Recent PUBLIC issues only (caller must verify repo is not private)."""
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(f"{API}/repos/{owner}/{repo}/issues",
                                 params={"per_page": max(1, min(limit, 30)),
                                         "state": "all", "sort": "updated"},
                                 headers=_headers(token))
            if r.status_code != 200:
                return []
            out = []
            for i in r.json():
                if "pull_request" in i:  # skip PRs, keep issues
                    continue
                out.append({"number": i.get("number"), "title": i.get("title", "")[:200],
                            "state": i.get("state", ""), "url": i.get("html_url", ""),
                            "body": (i.get("body") or "")[:2000]})
            return out
    except Exception as e:
        log.warning("issues fetch failed %s/%s: %s", owner, repo, e)
        return []


def classify(name: str, desc: str, lang: str) -> str:
    t = f"{name} {desc}".lower()
    if any(k in t for k in ("ai", "llm", "rag", "gpt", "agent")) or lang == "Python":
        return "ai"
    if "saas" in t or "multi-tenant" in t:
        return "saas"
    return "product"


async def sync_now() -> dict:
    db = get_db()
    token = await resolve_github_token(db)
    owner = await resolve_github_owner(db)
    if not token:
        raise RuntimeError("GITHUB_TOKEN not configured")
    run = await db["github_sync_runs"].insert_one(
        {"started_at": utcnow(), "status": "running", "found": 0, "added": 0, "updated": 0, "errors": []})
    run_id = run.inserted_id
    try:
        repos = await fetch_repos(owner, token)
        found, added, updated = len(repos), 0, 0
        for r in repos:
            gid = r.get("id")
            existing = await db["github_repositories"].find_one({"github_id": gid})
            readme = await fetch_readme(owner, r.get("name", ""), token) if not existing else (existing.get("readme") or "")
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
                doc.update({"sync_status": "new", "is_manually_edited": False,
                            "rag_enabled": True})
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
            await log_error("github_sync", "GitHub sync failed", str(e)[:2000],
                                logger="app.services.github_service")
        except Exception:
            pass
        raise
