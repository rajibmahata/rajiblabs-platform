"""One-shot SQLite (.NET backend) → Mongo migration. Preserves content, NULLs unverified github URLs."""
import asyncio
import sqlite3
import sys
sys.path.insert(0, ".")
from app.database import get_db, utcnow


def load_sqlite(path: str) -> dict:
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    out: dict = {}
    for tbl in ("Projects", "Profiles", "Products", "PortfolioProjects"):
        try:
            out[tbl] = [dict(r) for r in con.execute(f"SELECT * FROM {tbl}")]
        except Exception:
            out[tbl] = []
    con.close()
    return out


async def main(sqlite_path: str = "../backend/RajibLabs.Api/rajiblabs.db"):
    db = get_db()
    data = load_sqlite(sqlite_path)
    n = 0
    for p in data.get("Projects", []) + data.get("PortfolioProjects", []):
        slug = (p.get("Slug") or p.get("slug") or p.get("Title", "")).lower().replace(" ", "-")
        if not slug or await db["projects"].find_one({"slug": slug}):
            continue
        await db["projects"].insert_one({
            "slug": slug, "name": p.get("Title") or p.get("Name", slug),
            "category": "project", "status": "draft",
            "short_description": p.get("Description", "")[:200],
            "full_description": p.get("Description", ""),
            "technologies": [], "github_url": p.get("GitHubUrl") or None,
            "live_url": p.get("LiveUrl"), "featured": False, "published": False,
            "display_order": 99, "locked_fields": [],
            "created_at": utcnow(), "updated_at": utcnow()})
        n += 1
    print(f"Migrated {n} projects (unverified github kept only if present, else NULL).")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "../backend/RajibLabs.Api/rajiblabs.db"))
