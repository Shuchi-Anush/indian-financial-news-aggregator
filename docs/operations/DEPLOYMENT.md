# Deployment & Infrastructure Guide

This document defines the deployment mechanics for the backend.

## Docker Workflow
The system relies on Docker Compose for container orchestration.
```bash
docker compose -f docker-compose.yml up -d --build
```
This mounts:
- `db`: PostgreSQL 16
- `backend`: Uvicorn executing the FastAPI application on port 8000.

## Environment Separation
The deployment context reads from `.env` or `.env.docker`.
- Ensure `DATABASE_URL` uses the `postgresql+asyncpg://` scheme.
- Set `ENV_MODE=production`.

## Startup & Recovery Behaviors

### Docker Recovery
If the FastAPI container dies, Docker Compose `restart: always` triggers a reboot.
1. The container restarts.
2. The lifespan executes.
3. Alembic migrations are NOT auto-executed by default—this is a strict production safety choice. Migrations must be run via discrete deployment pipelines.

### DB Restart Handling
If PostgreSQL bounces or loses connection:
- `asyncpg` pools will invalidate dead connections upon checkout.
- If the DB is unavailable during container boot, `initialize_database()` will fail, terminating the container to allow Docker to restart it via backoff.

## Common Startup Failures
- **ModuleNotFoundError: prometheus-client**: Ensure the container image was rebuilt after dependency locking.
- **ConnectionRefusedError (5432)**: The DB container hasn't finished its init script. Wait 5 seconds.
- **IntegrityError during Migrations**: You attempted an Alembic downgrade on Enum types without specifying the postgresql casting directive.

## Recovery Procedures
If deployment fails, view logs via:
```bash
docker logs finnews-backend --tail 100
```
Rollback migrations explicitly:
```bash
docker exec -it finnews-backend uv run alembic downgrade -1
```
