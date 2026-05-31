from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.routes_alert import router as alert_router
from app.api.routes_auth import router as auth_router
from app.api.routes_export import router as export_router
from app.api.routes_saved import router as saved_router
from app.api.routes_search import router as search_router
from app.config import get_settings
from app.core.http import HTTPClientManager
from app.core.logging import setup_logging
from app.core.rate_limit import limiter, user_limiter
from app.core.security_headers import SecurityHeadersMiddleware
from app.db.session import init_db
from workers.alert_worker import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    setup_logging()
    settings = get_settings()

    # Validate critical settings in production
    if settings.app_env == "production":
        logger.info("Running production environment checks...")
        # JWT secret validation is handled by pydantic validator
        # Database validation is handled by pydantic validator

    logger.info("Starting PaperLens", env=settings.app_env)

    # Warn if SQLite is used outside of development — it doesn't support concurrent writes
    if settings.database_url.startswith("sqlite") and settings.app_env != "development":
        logger.warning(
            "SQLite detected in non-development environment. "
            "Switch to PostgreSQL for staging/production to avoid write conflicts."
        )
    HTTPClientManager.init_client()
    await init_db()

    # Initialize journal quality service
    from services.journal_quality_service import get_journal_quality_service

    jq_service = get_journal_quality_service()
    stats = await jq_service.load_data()
    logger.info(
        f"Journal quality data loaded: {stats.total_journals} journals "
        f"(Q1={stats.q1_count}, Q2={stats.q2_count}, Q3={stats.q3_count}, Q4={stats.q4_count})"
    )

    start_scheduler()
    yield
    stop_scheduler()
    await HTTPClientManager.close_client()
    logger.info("Shutting down PaperLens")


app = FastAPI(
    title="PaperNest API",
    version="0.1.0",
    description="Multi-source academic paper search, deduplication, and ranking.",
    lifespan=lifespan,
)

# Add rate limit exception handlers for both limiters
app.state.limiter = limiter
app.state.user_limiter = user_limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Compress responses ≥1 KB. Static assets (JS bundle, CSS) typically
# shrink ~70%. Adds ~5ms CPU per response which is well worth it.
app.add_middleware(GZipMiddleware, minimum_size=1024, compresslevel=6)

# Configure CORS with environment-based settings
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
    max_age=3600,  # Cache preflight requests for 1 hour
)


@app.get("/healthz", tags=["meta"])
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", tags=["meta"], include_in_schema=False)
async def root() -> dict[str, str]:
    """API metadata. Only reached when frontend/dist is not mounted."""
    return {
        "name": "PaperNest",
        "version": "0.1.0",
        "docs": "/docs",
    }


app.include_router(auth_router, prefix="/api/v1", tags=["auth"])
app.include_router(search_router, prefix="/api/v1", tags=["search"])
app.include_router(saved_router, prefix="/api/v1", tags=["saved"])
app.include_router(export_router, prefix="/api/v1", tags=["export"])
app.include_router(alert_router, prefix="/api/v1", tags=["alerts"])

# Serve React static files if the dist folder exists (production build).
#
# StaticFiles(html=True) sudah menangani SPA fallback: kalau path tidak
# match file, akan fallback ke index.html. Tidak perlu route handler
# tambahan (yang malah tidak akan kepanggil karena Mount catch dulu).
static_dir = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.isdir(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
