"""Create first admin from env (never overwrite). Usage: python scripts/create_admin.py"""
import asyncio
import sys
sys.path.insert(0, ".")
from app.config import get_settings
from app.database import get_db, utcnow
from app.auth.utils import hash_password


async def main():
    s = get_settings()
    db = get_db()
    if await db["admins"].count_documents({}) > 0:
        print("Admin already exists — not overwriting.")
        return
    if not s.admin_initial_password:
        print("Set ADMIN_INITIAL_PASSWORD first.")
        raise SystemExit(1)
    await db["admins"].insert_one({
        "emails": s.admin_email_list, "password_hash": hash_password(s.admin_initial_password),
        "created_at": utcnow(), "last_login_at": None})
    print(f"Admin created for: {', '.join(s.admin_email_list)}")


if __name__ == "__main__":
    asyncio.run(main())
