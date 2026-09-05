"""Shared test fixtures."""
import pytest


@pytest.fixture(scope="session", autouse=True)
def seed_db_if_available():
    """Seed-if-empty on a reachable Mongo so live tests are deterministic
    on fresh databases (CI). `init_db` never wipes — it only fills empty
    collections. No-op when Mongo is down; live tests then skip
    individually via their per-module mongo guard."""
    async def _main():
        from app.database import get_db, init_db
        await get_db().command("ping")
        await init_db()

    try:
        import asyncio
        asyncio.run(_main())
    except Exception:
        pass
