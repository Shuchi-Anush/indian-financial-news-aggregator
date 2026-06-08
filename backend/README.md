<p align="center">
  <img src="../docs/assets/backend_runtime.png" alt="Backend Runtime Architecture" width="100%"/>
</p>

<h1 align="center">Backend — Indian Financial News Aggregator</h1>

<p align="center">
  Async FastAPI backend engineered around strict ingestion pipeline boundaries,<br/>
  idempotent persistence, and deterministic normalization.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/FastAPI-async-009688?style=flat-square&logo=fastapi&logoColor=white"/>
  <img src="https://img.shields.io/badge/SQLAlchemy-2.x%20async-CC0000?style=flat-square"/>
  <img src="https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat-square&logo=postgresql&logoColor=white"/>
  <img src="https://img.shields.io/badge/Pydantic-v2-E92063?style=flat-square&logo=pydantic&logoColor=white"/>
  <img src="https://img.shields.io/badge/structlog-structured-555555?style=flat-square"/>
  <img src="https://img.shields.io/badge/uv-package%20manager-7C3AED?style=flat-square"/>
  <img src="https://img.shields.io/badge/Architecture-Layered-F5A623?style=flat-square"/>
</p>

---

## Overview

The backend is the core runtime of the Indian Financial News Aggregator. It is designed as a strictly layered async service responsible for:

- Raw external data collection across heterogeneous financial news sources
- Canonical normalization of raw source payloads
- Hash-based deduplication to prevent redundant persistence
- Idempotent article persistence via SQLAlchemy 2.x async ORM
- Structured export generation for downstream consumers

Every design decision prioritizes correctness of boundaries, async-safety of the persistence stack, and operational maintainability over feature velocity.

---

## Runtime Status

### Stable

| Component | Detail |
| --- | --- |
| FastAPI lifecycle | Application startup / shutdown hooks |
| Structured logging | structlog with per-request trace IDs |
| Centralized exception handling | Consistent error response contract |
| Request tracing middleware | UUID-scoped request correlation |
| Async PostgreSQL lifecycle | Engine and session managed via lifespan |
| SQLAlchemy 2.x async ORM | Full async session factory |
| FeedSource model | Source registry with metadata |
| Article model | Dedup-ready canonical article schema |
| Pydantic v2 schemas | Typed DTO contracts for all boundaries |
| Docker Compose environment | Full local stack with PostgreSQL |
| OpenAPI documentation | Auto-generated and served at `/docs` |

### In Progress

| Component | Detail |
| --- | --- |
| Collector contracts | Abstract base and protocol definitions |
| Normalization boundaries | Processor input/output contracts |
| Deduplication pipeline | Hash computation and match strategy |
| Orchestration services | Pipeline execution and transaction coordination |

---

## Architecture

```text
src/app/
│
├── api/                    # HTTP transport layer — routing and serialization only
│   └── routes/
│
├── collectors/             # Raw external ingestion — fetch only, no side effects
│   ├── rss/
│   ├── apis/
│   └── scrapers/
│
├── processors/             # Normalization + deduplication preparation
│
├── services/               # Business orchestration + transaction boundaries
│
├── exporters/              # Output generation — CSV / XLSX / HTML
│
├── models/                 # SQLAlchemy ORM entities
│
├── schemas/                # Pydantic v2 DTOs
│
├── db/                     # Engine / session factory / declarative base
│
├── core/                   # Config / logging / middleware / startup
│
└── main.py                 # Application composition root
```

---

## Layer Boundary Contracts

### Hard Constraints Per Layer

| Layer | Must Handle | Must Never Do |
| --- | --- | --- |
| `api/` | Routing, validation, serialization | Business logic, DB access, orchestration |
| `collectors/` | Raw external fetch, retry, rate-limit awareness | Normalize, hash, deduplicate, persist |
| `processors/` | Normalization, canonical transforms, dedup prep | External I/O, DB writes, side effects |
| `services/` | Orchestration, transaction management, pipeline execution | Transport logic, raw source I/O |
| `exporters/` | Output file generation | Business logic, DB mutations |

These constraints are enforced by convention and documented in architecture governance. Violations are tracked as architectural defects.

---

## Request Lifecycle

```text
HTTP Request
     │
     ▼
Middleware Stack          ← request ID injection, structured logging
     │
     ▼
API Route                 ← input validation via Pydantic v2, dependency injection
     │
     ▼
Service Layer             ← orchestration, transaction boundaries
     │
     ▼
Processor Layer           ← normalization, deduplication preparation
     │
     ▼
SQLAlchemy ORM            ← async session, explicit transaction scope
     │
     ▼
PostgreSQL                ← persistence
     │
     ▼
Structured Response       ← serialized Pydantic output schema
```

---

## Ingestion Pipeline Lifecycle

```text
FeedSource Registry
     │
     ▼
Collector                 ← stateless fetch of raw source payload
     │
     ▼
RawArticle                ← unmodified source data contract
     │
     ▼
Normalizer                ← canonical field mapping, timestamp parsing, content cleanup
     │
     ▼
Deduplicator              ← hash computation, duplicate detection
     │
     ▼
Pipeline Service          ← orchestration, idempotent persistence coordination
     │
     ▼
PostgreSQL                ← Article persistence
     │
     ▼
Export / API Consumers
```

<p align="center">
  <img src="../docs/assets/orchestration_pipeline.png" alt="Ingestion Orchestration Pipeline" width="100%"/>
</p>

---

## Persistence Architecture

<p align="center">
  <img src="../docs/assets/persistence_flow.png" alt="Persistence Flow Diagram" width="100%"/>
</p>

### Persistence Design Principles

| Principle | Implementation |
|---|---|
| **Idempotent writes** | Hash-based upsert strategy prevents duplicate articles |
| **Async-safe sessions** | `AsyncSession` via `async_sessionmaker`, no sync access paths |
| **UUID primary keys** | Stable, collision-free, federation-ready identifiers |
| **Explicit transactions** | No implicit commits; all writes inside bounded `async with session.begin()` |
| **Timestamp lifecycle** | `created_at` / `updated_at` managed automatically by ORM hooks |
| **Dedup-ready schema** | `content_hash` field indexed for efficient duplicate detection |
| **Restart-safe** | Re-ingestion of the same time window is a no-op on existing records |

### Current Schema Bootstrap

During active schema iteration, tables are created via:

```python
async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)
```

This will be replaced by Alembic-managed migrations after schema stabilization.

---

## Async Guarantees

The backend enforces the following async correctness invariants:

- All database access uses `AsyncSession` exclusively — no synchronous session paths exist
- Engine is initialized once at application lifespan startup and shared via dependency injection
- Sessions are request-scoped — no session leakage across request boundaries
- No blocking calls are made within any async execution context
- All ORM queries use `await` — lazy loading of relationships is explicitly disabled where applicable

---

## Collector Philosophy

Collectors are designed to be the simplest possible components in the system. Their contract is narrow by design.

### Collector Invariants

| Property | Requirement |
| --- | --- |
| **Stateless** | No internal state between invocations |
| **Side-effect free** | No writes, no mutations, no cache updates |
| **Retry-safe** | Can be called multiple times without consequence |
| **Orchestration-safe** | Service layer controls when and how often collectors run |
| **Output contract** | Always returns a list of `RawArticle` instances |

### What Collectors Must Never Do

- Normalize field names or content
- Compute deduplication hashes
- Write to or read from the database
- Enrich, classify, or tag articles
- Make decisions about persistence

The service layer orchestrates. The processor layer transforms. The collector only fetches.

---

## Observability

Every request in the system is traceable end-to-end.

| Signal | Implementation |
| --- | --- |
| Request correlation | UUID injected at middleware entry, propagated through all log events |
| Structured logging | structlog with consistent JSON-serializable event schema |
| Exception capture | Centralized handler produces structured error responses with trace context |
| Health endpoint | `GET /health` — returns `{ "status": "ok" }` for liveness probing |

---

## Local Development

### Prerequisites

- Python 3.11+
- [`uv`](https://github.com/astral-sh/uv) package manager
- Docker + Docker Compose (for full stack)

### Activate Environment

```bash
cd backend
```

**Unix / macOS:**

```bash
source .venv/bin/activate
```

**Windows:**

```bash
.venv\Scripts\activate
```

### Install Dependencies

```bash
uv sync
```

### Start Development Server

```bash
uv run uvicorn app.main:app \
  --app-dir src \
  --reload \
  --host 127.0.0.1 \
  --port 8000
```

### Verify Health

```bash
curl http://127.0.0.1:8000/health
```

```json
{ "status": "ok" }
```

### API Documentation

```text
http://127.0.0.1:8000/docs       ← Swagger UI
http://127.0.0.1:8000/openapi.json
```

---

## Docker Workflow

### Start Full Stack (Backend + PostgreSQL)

```bash
docker compose up --build
```

### Start in Detached Mode

```bash
docker compose up -d --build
```

### Stop Stack

```bash
docker compose down
```

### Rebuild Without Cache

```bash
docker compose build --no-cache
docker compose up
```

---

## Development Commands

### Type Check

```bash
uv run mypy src/app/
```

### Lint

```bash
uv run ruff check src/
```

### Format

```bash
uv run ruff format src/
```

### Run Tests

```bash
uv run pytest
```

### Compile Validation

```bash
python -m compileall src
```

---

## Environment Variables

Configured via `.env` (copied from `.env.example`).

| Variable | Purpose |
| --- | --- |
| `APP_ENV` | Runtime environment (`development` / `production`) |
| `LOG_LEVEL` | Logging verbosity (`DEBUG` / `INFO` / `WARNING`) |
| `POSTGRES_HOST` | PostgreSQL host |
| `POSTGRES_PORT` | PostgreSQL port (default: `5432`) |
| `POSTGRES_DB` | Database name |
| `POSTGRES_USER` | Database user |
| `POSTGRES_PASSWORD` | Database password |

---

## Current Non-Goals

The following are explicitly out of scope for the current backend phase:

- Authentication and authorization
- Redis caching layer
- Celery or Kafka messaging infrastructure
- Distributed task scheduling
- WebSocket infrastructure
- ML inference integration

These will be introduced in future phases after ingestion pipeline stabilization.

---

## Related Documentation

| Document | Path |
| --- | --- |
| System Architecture | `../docs/architecture/system_architecture.md` |
| Database Design | `../docs/architecture/db_design.md` |
| Pipeline Flow | `../docs/architecture/pipeline_flow.md` |
| Collector Strategy | `../docs/architecture/collector_strategy.md` |
| API Contracts | `../docs/api/api_contracts.md` |
| Architecture Decisions | `../docs/decisions/` |
| Local Development Guide | `../docs/operations/local_development.md` |
| AI Operating Context | `../.claude/` |

---

<p align="center">
  Built with production-minded backend engineering principles.
</p>
