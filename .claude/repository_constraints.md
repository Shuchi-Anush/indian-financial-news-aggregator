# Repository Constraints

## Technology Constraints

| Allowed | Not Allowed |
|---------|-------------|
| Python 3.11+ | Python 3.10 or older |
| FastAPI | Flask, Django |
| Pydantic v2 | Pydantic v1 syntax |
| SQLAlchemy 2.0 async | SQLAlchemy 1.x, sync sessions |
| PostgreSQL 16 | SQLite, MySQL, MongoDB |
| `asyncpg` driver | `psycopg2` (sync) |
| `httpx` (async HTTP) | `requests` (sync HTTP) |
| `structlog` | stdlib `logging`, `print()` |
| `uv` (package manager) | `pip`, `poetry`, `pipenv` |
| Docker Compose | Kubernetes, Helm |
| `ruff` (lint + format) | `black`, `isort`, `flake8` |

## Architecture Constraints

- **Monolith** — single FastAPI process, no microservices
- **Single database** — PostgreSQL, no polyglot persistence
- **No message queues** — no Celery, RabbitMQ, Kafka, Redis Streams
- **No event sourcing or CQRS** — standard CRUD with services
- **No ORM-level multi-tenancy** — single-tenant design
- **No GraphQL** — REST API only

## Scope Constraints

- **Backend first** — frontend is secondary and must not drive backend design
- **Indian financial news only** — all RSS feeds and API sources target Indian markets/economy
- **No real-time streaming** — batch collection via API trigger or cron
- **No user accounts** — no auth, no user management in current scope
- **No paid API dependencies for core flow** — system must work with RSS feeds alone; paid APIs (NewsData.io, GNews) are optional enrichment

## Deployment Constraints

- **Docker Compose only** — no cloud-managed orchestration
- **Single-host** — no distributed deployment
- **No CI/CD initially** — manual docker compose deployments
