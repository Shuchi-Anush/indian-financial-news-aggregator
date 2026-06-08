"""Application lifespan management.

Provides the async context manager used by FastAPI's ``lifespan`` parameter
to run startup and shutdown logic. Currently handles:

- Startup: log application boot, initialize the async DB engine
- Shutdown: dispose of the DB engine connection pool

Future phases will add feed seeding, scheduled tasks, etc. here.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI

from app.core.config import get_settings
from app.db.session import dispose_engine, init_engine

log = structlog.get_logger()


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
    await init_engine()
    log.info("database_engine_initialized")

    yield

    # Shutdown: release database connections
    await dispose_engine()
    log.info("application_shutdown")
