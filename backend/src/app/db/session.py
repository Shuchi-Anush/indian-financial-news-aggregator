"""Async database engine and session management.

Provides:
- ``init_engine`` / ``dispose_engine`` — engine lifecycle (called from startup.py)
- ``get_db`` — async generator yielding an ``AsyncSession`` for FastAPI DI
"""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

# Module-level engine and session factory — initialized once at startup
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


async def initialize_database() -> None:
    """Create the async engine and session factory.

    Called once during application startup or script initialization.
    """
    global _engine, _session_factory  # noqa: PLW0603

    settings = get_settings()
    _engine = create_async_engine(
        settings.database_url,
        echo=(not settings.is_production),
        pool_pre_ping=True,
    )
    _session_factory = async_sessionmaker(
        bind=_engine,
        expire_on_commit=False,
    )


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return the current async session factory."""
    if _session_factory is None:
        raise RuntimeError("Session factory not initialized. Call initialize_database() first.")
    return _session_factory


async def dispose_engine() -> None:
    """Dispose of the engine connection pool.

    Called during application shutdown (see ``core/startup.py``).
    """
    global _engine, _session_factory  # noqa: PLW0603

    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None


def get_engine() -> AsyncEngine:
    """Return the current async engine (must be initialized first)."""
    if _engine is None:
        raise RuntimeError("Database engine not initialized. Call initialize_database() first.")
    return _engine


async def get_db() -> AsyncIterator[AsyncSession]:
    """Yield an async database session for FastAPI dependency injection.

    Usage in services::

        async def get_article_service(
            db: Annotated[AsyncSession, Depends(get_db)],
        ) -> ArticleService:
            return ArticleService(db)
    """
    if _session_factory is None:
        raise RuntimeError("Session factory not initialized. Call initialize_database() first.")

    async with _session_factory() as session:
        yield session
