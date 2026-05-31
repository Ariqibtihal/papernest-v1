"""
Shared pytest fixtures.

Database schema bootstrap
─────────────────────────
Tests that use `TestClient(app)` directly (e.g. test_security) hit the app's
real SQLite engine. In a fresh environment (CI checkout) that database has no
tables — they are normally created by Alembic migrations, which the test job
does not run. The `_create_schema` fixture below creates all tables on the
real engine once per session so those tests work anywhere.

Rate-limit isolation
────────────────────
slowapi menyimpan hit-count di in-memory storage yang persist sepanjang
proses pytest. Tanpa reset, test yang sengaja memicu rate limit (mis.
TestRateLimiting yang spam 35 request) akan "membocorkan" state 429 ke
test berikutnya yang memanggil endpoint yang sama (mis. test_search_route).

Fixture autouse di bawah membersihkan storage kedua limiter sebelum tiap
test, sehingga setiap test mulai dari window rate-limit yang kosong.
"""

from __future__ import annotations

import asyncio
import contextlib

import pytest


@pytest.fixture(scope="session", autouse=True)
def _create_schema():
    """Create all ORM tables on the app's real engine before any test runs.

    Idempotent: `create_all` skips tables that already exist, so this is safe
    whether the DB is fresh (CI) or already migrated (local dev).
    """
    from app.db.base import Base
    from app.db.session import engine

    # Import models so they register on Base.metadata.
    from models import paper, saved_paper, search_alert, user  # noqa: F401

    async def _create() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(_create())
    yield


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    """Reset slowapi in-memory storage sebelum tiap test."""
    from app.core.rate_limit import limiter, user_limiter

    for lim in (limiter, user_limiter):
        storage = getattr(lim, "_storage", None)
        if storage is not None:
            # MemoryStorage punya .reset(); storage lain mungkin tidak.
            with contextlib.suppress(Exception):
                storage.reset()

    yield
