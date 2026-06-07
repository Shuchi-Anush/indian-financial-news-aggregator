# Backend

FastAPI backend for the Indian Financial News Aggregator.

## Quick Start

```bash
# Install dependencies
uv sync

# Run locally (requires PostgreSQL on localhost:5432)
POSTGRES_HOST=localhost uv run uvicorn src.app.main:app --reload

# Or run everything via Docker
docker compose up --build
```

## Module Structure

```
src/app/
├── main.py          # App factory, lifespan, wiring
├── core/            # Config, logging, exceptions, middleware
├── db/              # Engine, session factory, base model
├── models/          # SQLAlchemy ORM models (one file per table)
├── schemas/         # Pydantic DTOs (one file per domain)
├── collectors/      # News source collectors
│   ├── rss/         # RSS feed collector
│   ├── apis/        # Third-party API collectors (optional)
│   └── scrapers/    # HTML scrapers (future)
├── processors/      # Normalizer, deduplicator
├── services/        # Business logic, pipeline orchestration
├── exporters/       # CSV, Excel generation
├── api/routes/      # REST endpoint handlers
├── tasks/           # Background tasks (future)
└── utils/           # Shared utilities
```

## Key Commands

```bash
# Test
uv run pytest tests/ -v

# Lint
uv run ruff check src/ --fix

# Format
uv run ruff format src/

# Type check
uv run mypy src/app/
```

## Architecture

See [../docs/architecture/](../docs/architecture/) for system design, pipeline flow, and database schema.
