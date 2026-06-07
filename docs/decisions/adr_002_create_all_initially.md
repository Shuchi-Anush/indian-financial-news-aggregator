# ADR-002: create_all() for Initial Development

**Status:** Accepted  
**Date:** 2026-06-07  
**Context:** Database schema management strategy during early development.

## Decision

Use SQLAlchemy's `Base.metadata.create_all()` (via async engine) in the FastAPI lifespan handler for table creation during development. Defer Alembic migration setup until the schema stabilizes.

## Rationale

- Schema is changing rapidly during Phase 1 — running Alembic migrations for every column change adds friction
- `create_all()` is idempotent — safe to run on every startup
- Two-table schema (articles, feed_sources) doesn't warrant migration tooling yet
- Alembic can be introduced with a single "initial" migration once the schema is stable

## Consequences

- No migration history during development
- Schema changes require dropping and recreating tables (acceptable in dev)
- Must introduce Alembic before any production deployment with real data

## Migration Path

1. Implement and stabilize schema with `create_all()`
2. Once schema is stable, initialize Alembic with `--autogenerate`
3. Generate initial migration from current models
4. Replace `create_all()` with `alembic upgrade head` in startup
