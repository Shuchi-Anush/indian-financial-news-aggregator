# Indian Financial News Aggregator

Production-grade Indian financial news aggregation platform with modular collectors, deduplication pipelines, export engines, and Docker-based deployment.

## What It Does

Collects → Normalizes → Deduplicates → Stores → Exports Indian financial news from RSS feeds and APIs.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI, Python 3.11+, SQLAlchemy 2.0 async |
| Database | PostgreSQL 16 |
| Export | CSV, Excel (pandas + openpyxl) |
| Logging | structlog (structured JSON) |
| Deploy | Docker Compose |
| Package Manager | uv |

## Quick Start

```bash
# 1. Configure environment
cp .env.example .env

# 2. Start everything
docker compose up --build

# 3. Verify
curl http://localhost:8000/health

# 4. Seed default Indian financial news feeds
docker compose exec backend uv run python scripts/seed_feeds.py

# 5. Collect news
curl -X POST http://localhost:8000/api/v1/pipeline/run

# 6. Browse articles
curl http://localhost:8000/api/v1/articles
```

For local development (without Docker for the backend), see [docs/operations/local_development.md](docs/operations/local_development.md).

## Project Structure

```
backend/src/app/
├── core/          # Config, logging, exceptions, middleware
├── db/            # Database engine, session, base model
├── models/        # SQLAlchemy ORM models
├── schemas/       # Pydantic request/response DTOs
├── collectors/    # RSS feed and API news collectors
├── processors/    # Normalizer, deduplicator
├── services/      # Business logic, pipeline orchestration
├── exporters/     # CSV, Excel export
├── api/routes/    # Thin REST API handlers
└── main.py        # Application entry point
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/api/v1/articles` | List articles (filtered, paginated) |
| `GET` | `/api/v1/articles/{id}` | Get single article |
| `POST` | `/api/v1/pipeline/run` | Trigger collection pipeline |
| `GET` | `/api/v1/feeds` | List configured feeds |
| `POST` | `/api/v1/export/csv` | Export articles as CSV |
| `POST` | `/api/v1/export/excel` | Export articles as Excel |

Full API docs: [docs/api/api_contracts.md](docs/api/api_contracts.md)

## News Sources

Preconfigured Indian financial RSS feeds:
- Economic Times (Markets, Economy)
- Moneycontrol (Markets, Business)
- LiveMint (Markets, Economy)
- NDTV Profit
- Business Standard (Markets)

## Documentation

| Document | Path |
|----------|------|
| Architecture | [docs/architecture/](docs/architecture/) |
| API Contracts | [docs/api/api_contracts.md](docs/api/api_contracts.md) |
| Pipeline Flow | [docs/architecture/pipeline_flow.md](docs/architecture/pipeline_flow.md) |
| Database Design | [docs/architecture/db_design.md](docs/architecture/db_design.md) |
| Local Dev Setup | [docs/operations/local_development.md](docs/operations/local_development.md) |
| Docker Workflow | [docs/operations/docker_workflow.md](docs/operations/docker_workflow.md) |
| Roadmap | [docs/context/roadmap.md](docs/context/roadmap.md) |
| Contributing | [CONTRIBUTING.md](CONTRIBUTING.md) |

## Status

Phase 1 — Backend infrastructure and ingestion pipeline under active development.

## License

MIT — see [LICENSE](LICENSE)
