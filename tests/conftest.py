"""
Shared pytest fixtures.

Rate-limit isolation
────────────────────
slowapi menyimpan hit-count di in-memory storage yang persist sepanjang
proses pytest. Tanpa reset, test yang sengaja memicu rate limit (mis.
TestRateLimiting yang spam 35 request) akan "membocorkan" state 429 ke
test berikutnya yang memanggil endpoint yang sama (mis. test_search_route).

Akibatnya suite jadi flaky — lulus/gagal tergantung urutan eksekusi.

Fixture autouse di bawah membersihkan storage kedua limiter sebelum tiap
test, sehingga setiap test mulai dari window rate-limit yang kosong.
"""

from __future__ import annotations

import contextlib

import pytest


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
