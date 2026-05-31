from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool, QueuePool

from app.config import get_settings

_settings = get_settings()

# Use QueuePool for production, NullPool for development/testing
if _settings.app_env == "production":
    engine = create_async_engine(
        _settings.database_url,
        echo=False,
        future=True,
        poolclass=QueuePool,
        pool_size=20,  # Number of connections to maintain
        max_overflow=10,  # Additional connections when pool is full
        pool_timeout=30,  # Seconds to wait for connection
        pool_recycle=3600,  # Recycle connections after 1 hour
        pool_pre_ping=True,  # Verify connections before using
    )
else:
    # Use NullPool for development/testing (better for async and testing)
    engine = create_async_engine(
        _settings.database_url,
        echo=False,
        future=True,
        poolclass=NullPool,
    )

SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def init_db() -> None:
    """Initialize database - tables are now created via Alembic migrations."""
    # Import models so SQLAlchemy registers them on Base.metadata.
    from models import paper as _paper  # noqa: F401
    from models import saved_paper as _saved_paper  # noqa: F401
    from models import search_alert as _search_alert  # noqa: F401
    from models import user as _user  # noqa: F401

    # Tables are created via Alembic migrations, not here
    # This function is kept for compatibility


async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session


get_async_session = get_session
