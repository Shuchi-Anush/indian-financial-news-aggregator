# Architecture Context

## System Boundary
This codebase is a modular monolith containing:
- **FastAPI**: Frontend REST API ingress.
- **APScheduler**: Background job orchestration embedded inside FastAPI's lifespan.
- **Asyncpg/SQLAlchemy**: Direct interaction with PostgreSQL 16.

## Forbidden Patterns
- **Sync DB Drivers**: You cannot use `psycopg2`. You must use `asyncpg`.
- **Database Triggers**: Avoid implicit DB triggers for domain logic. Enforce logic in the Service layer.

## Database Access Boundaries
- **Routers** (`app.api.routes`): Can invoke Services or Repositories. Cannot construct raw SQL or touch `AsyncSession`.
- **Services** (`app.services`, `app.orchestration`): Coordinate domain logic. They call Repositories.
- **Repositories** (`app.db.repository`): The ONLY layer allowed to `import sqlalchemy` or touch `AsyncSession`.

## Operational Significance
If you suggest changes that bleed `AsyncSession` into `app.api.routes`, you violate the core domain boundary.
