"""Application lifespan management.

Provides the async context manager used by FastAPI's ``lifespan`` parameter
to run startup and shutdown logic. Currently handles:

- Startup: log application boot, initialize the async DB engine, create tables
- Shutdown: dispose of the DB engine connection pool

Future phases will add feed seeding, scheduled tasks, etc. here.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from sqlalchemy import text

from app.core.config import get_settings
from app.db.session import dispose_engine, get_engine, initialize_database
from app.orchestration.scheduler import start_scheduler, stop_scheduler

log = structlog.get_logger()


async def _verify_database_health() -> None:
    """Verify actual DB connectivity and session execution capability."""
    engine = get_engine()
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        log.info("database_healthcheck_passed")
    except Exception as e:
        log.error("database_healthcheck_failed", error=str(e))
        raise RuntimeError("Database connectivity failed during startup") from e


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """FastAPI lifespan context manager — startup and shutdown hooks."""
    settings = get_settings()

    log.info(
        "application_startup",
        app_env=settings.app_env,
        log_level=settings.log_level,
        backend_port=settings.backend_port,
        postgres_host=settings.postgres_host,
        postgres_db=settings.postgres_db,
    )

    # Initialize database engine and connection pool
    await initialize_database()
    log.info("database_engine_initialized")

    # Verify database health instead of auto-creating tables
    await _verify_database_health()

    start_scheduler()

    yield

    stop_scheduler()
    
    # Wait for active ingestion to finish, max 15 seconds, then cancel
    from app.orchestration.ingestion_jobs import graceful_shutdown
    await graceful_shutdown(timeout_seconds=15.0)

    # Shutdown: release database connections
    await dispose_engine()
    log.info("application_shutdown")
