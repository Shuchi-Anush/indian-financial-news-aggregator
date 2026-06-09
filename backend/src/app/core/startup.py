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
from sqlalchemy import MetaData, text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.core.config import get_settings
from app.db.session import dispose_engine, get_engine, init_engine

log = structlog.get_logger()


async def _create_tables() -> None:
    """Create all ORM tables and install database triggers.

    Uses ``Base.metadata.create_all()`` via a sync-compatible ``run_sync``
    call on the async engine's connection. This is safe for development and
    initial production bootstrapping. Alembic will supersede this for
    production migrations in a later phase.
    """
    # Import models package to ensure all models register with Base.metadata
    import app.models  # noqa: F401
    from app.db.base import Base

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await _install_updated_at_triggers(conn, Base.metadata)

    log.info("database_tables_created")


async def _install_updated_at_triggers(
    conn: AsyncConnection,
    metadata: MetaData,
) -> None:
    """Install PostgreSQL BEFORE UPDATE triggers for ``updated_at`` columns.

    Creates a shared PL/pgSQL function and applies it to every table that
    has an ``updated_at`` column (via ``TimestampMixin``). This ensures
    ``updated_at`` is always set by PostgreSQL's ``now()`` — not by ORM-level
    Python hooks — making it correct for bulk updates, raw SQL, and async
    sessions alike.

    Idempotent: safe to run on every startup (CREATE OR REPLACE / DROP IF EXISTS).
    """
    # Shared trigger function — one per database
    await conn.execute(
        text("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """)
    )

    # Apply trigger to each table with an updated_at column
    for table in metadata.tables.values():
        if "updated_at" not in table.columns:
            continue
        trigger_name = f"trg_{table.name}_updated_at"
        await conn.execute(text(f"DROP TRIGGER IF EXISTS {trigger_name} ON {table.name}"))
        await conn.execute(
            text(f"""
            CREATE TRIGGER {trigger_name}
                BEFORE UPDATE ON {table.name}
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column()
        """)
        )

    log.info("updated_at_triggers_installed")


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

    # Create tables and install triggers (idempotent — skips existing)
    await _create_tables()

    yield

    # Shutdown: release database connections
    await dispose_engine()
    log.info("application_shutdown")
