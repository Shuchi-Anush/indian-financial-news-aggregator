# Repository Map

## Root Layout

```
indian-financial-news-aggregator/
├── backend/                 # FastAPI application (primary focus)
│   ├── src/app/             # Application source code
│   ├── tests/               # pytest test suite
│   ├── scripts/             # Operational scripts (seed, migrate)
│   ├── Dockerfile           # Backend container build
│   └── pyproject.toml       # Dependencies and tooling config
├── frontend/                # UI clients (secondary, not yet active)
│   ├── streamlit/           # Streamlit dashboard (phase 2)
│   ├── web/                 # Next.js web client (future)
│   └── mobile/              # Mobile client (future)
├── infra/                   # Infrastructure config
│   ├── docker/              # Additional Docker configs
│   └── nginx/               # Reverse proxy config
├── docs/                    # Engineering documentation
│   ├── architecture/        # System design, DB schema, pipeline
│   ├── api/                 # API contracts and endpoint reference
│   ├── context/             # Scope, roadmap, non-goals
│   ├── decisions/           # Architecture Decision Records
│   └── operations/          # Dev setup, Docker, deployment
├── .agy/                    # AI workspace context (Antigravity)
├── .claude/                 # AI operating context (Claude/LLM)
├── docker-compose.yml       # Full-stack orchestration
├── .env / .env.example      # Environment configuration
└── README.md                # Project entry point
```

## Backend Module Map (`backend/src/app/`)

```
src/app/
├── main.py                  # FastAPI app factory, lifespan, wiring
├── core/                    # Cross-cutting infrastructure
│   ├── config.py            # Settings (pydantic-settings)
│   ├── logging.py           # Structlog configuration
│   ├── exceptions.py        # Domain exception hierarchy + handlers
│   └── middleware.py        # Request ID, logging, CORS
├── db/                      # Database lifecycle
│   ├── base.py              # Declarative base, mixins
│   └── session.py           # Async engine, session factory, get_db()
├── models/                  # SQLAlchemy ORM models
│   └── __init__.py          # Re-exports all models (Alembic discovery)
├── schemas/                 # Pydantic v2 request/response DTOs
│   └── __init__.py          # Re-exports
├── collectors/              # News ingestion layer
│   ├── __init__.py          # BaseCollector ABC
│   ├── rss/                 # RSS feed collectors
│   ├── apis/                # Third-party API collectors
│   └── scrapers/            # HTML scrapers (future)
├── processors/              # Data transformation
│   └── __init__.py          # Normalizer, deduplicator
├── services/                # Business logic / orchestration
│   └── __init__.py          # Article, pipeline, feed services
├── exporters/               # Output formatters
│   └── __init__.py          # CSV, Excel exporters
├── api/                     # HTTP interface
│   ├── __init__.py          # v1 router assembly
│   └── routes/              # Thin route handlers
├── tasks/                   # Background/scheduled tasks (future)
│   └── __init__.py
└── utils/                   # Shared utilities
    └── __init__.py
```

## Data Flow

```
RSS Feeds / APIs
      │
      ▼
  collectors/       ← fetch raw articles
      │
      ▼
  processors/       ← normalize, deduplicate
      │
      ▼
  services/         ← orchestrate pipeline, persist via ORM
      │
      ▼
  db/ + models/     ← PostgreSQL storage
      │
      ▼
  api/routes/       ← serve via REST endpoints
  exporters/        ← CSV / Excel download
```

## Dependency Direction (strict)

```
routes → services → processors → collectors
                  → db/session
                  → models
                  → exporters
core/ ← imported by everything (config, logging, exceptions)
schemas/ ← shared between routes and services
```

Routes never import models or db directly. Services own all DB access.
