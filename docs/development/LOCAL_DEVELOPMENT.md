# Local Development Guide

## Environment Setup
1. **uv setup**: Install `uv` (the fast Rust-based Python package manager).
   ```bash
   uv venv
   # On windows:
   .venv\Scripts\activate
   # On unix:
   source .venv/bin/activate
   uv sync
   ```
2. **Environment Variables**: Copy `.env.example` to `.env.local` and configure your local Postgres connection string.

## Docker Workflow
For a full local stack replication:
```bash
docker compose up -d
```
If you change `pyproject.toml`, you must rebuild:
```bash
docker compose up -d --build
```

## Migration Workflow
If you edit SQLAlchemy models in `app/models/`:
1. Generate the migration script:
   ```bash
   uv run alembic revision --autogenerate -m "Add new column"
   ```
2. **Review the script manually.** Alembic cannot reliably detect Enum changes or index drops. Fix any missing `postgresql_using` casts for downgrades.
3. Apply to local DB:
   ```bash
   uv run alembic upgrade head
   ```

## Test Workflow
We employ aggressive validation scripts located in `backend/scripts/`.
Run all tests:
```bash
uv run pytest
uv run python scripts/test_db_validation.py
uv run python scripts/test_ingestion_chaos.py
uv run python scripts/test_api_brutalization.py
```

## Debugging Workflow
- **APScheduler not triggering?**: Verify you are running within the allowed Cron window defined in `app.orchestration.scheduler` (IST Timezone).
- **Alembic Timeout?**: Your DB is locked. Ensure you don't have a DBeaver or pgAdmin transaction hung open on the table you are trying to alter.

## Common Startup Failures
- `asyncpg.exceptions.InvalidPasswordError`: Your local `.env` DB password doesn't match the `docker-compose.yml` DB password.
- `ModuleNotFoundError: No module named 'app'`: You forgot to execute `uv sync` or activate your virtual environment. All backend code expects `app` to be installed/available in the Python path.
