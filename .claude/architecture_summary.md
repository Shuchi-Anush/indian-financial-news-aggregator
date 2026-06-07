# Architecture Overview

## System Context

A news aggregation platform that collects Indian financial news from multiple RSS feeds and APIs, normalizes and deduplicates the content, stores it in PostgreSQL, and serves it through a REST API with CSV/Excel export.

```
┌─────────────────────────────────────────────────────────────┐
│                   External Sources                          │
│  Economic Times │ Moneycontrol │ LiveMint │ NDTV Profit │...│
└────────────┬────────────────────────────────────────────────┘
             │ RSS/HTTP
             ▼
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Backend                           │
│                                                             │
│  ┌──────────┐  ┌───────────┐  ┌──────────┐  ┌──────────┐  │
│  │Collectors│→ │Processors │→ │ Services │→ │  Models  │  │
│  │(RSS/API) │  │(norm/dedup)│  │(pipeline)│  │  (ORM)   │  │
│  └──────────┘  └───────────┘  └──────────┘  └────┬─────┘  │
│                                                    │        │
│  ┌──────────┐  ┌───────────┐                      │        │
│  │  Routes  │← │ Services  │←─────────────────────┘        │
│  │ (API v1) │  │ (query)   │                                │
│  └──────────┘  └───────────┘                                │
│                                                             │
│  ┌──────────┐                                               │
│  │Exporters │← CSV / Excel generation                       │
│  └──────────┘                                               │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │  PostgreSQL  │
                    │   (Docker)   │
                    └──────────────┘
```

## Layer Responsibilities

| Layer | Location | Responsibility |
|-------|----------|---------------|
| **HTTP** | `api/routes/` | Request validation, response serialization, thin delegation |
| **Services** | `services/` | Business logic, DB queries, pipeline orchestration |
| **Collectors** | `collectors/` | Fetch raw articles from RSS/APIs, return DTOs |
| **Processors** | `processors/` | Normalize text, parse dates, deduplicate content |
| **Exporters** | `exporters/` | Generate CSV/Excel from article data |
| **Models** | `models/` | SQLAlchemy ORM table definitions |
| **Schemas** | `schemas/` | Pydantic DTOs for all data boundaries |
| **Core** | `core/` | Config, logging, exceptions, middleware |
| **DB** | `db/` | Engine, session factory, base class |

## Key Design Decisions

1. **Manual pipeline trigger** — no built-in scheduler; pipeline runs via `POST /api/v1/pipeline/run` or external cron (see ADR-001)
2. **`create_all()` for initial development** — Alembic introduced when schema stabilizes (see ADR-002)
3. **Script-based feed seeding** — default feeds loaded via `scripts/seed_feeds.py`, not auto-seeded on startup (see ADR-003)

## Technology Choices

| Concern | Choice | Why |
|---------|--------|-----|
| Web framework | FastAPI | Async-native, Pydantic integration, auto OpenAPI |
| ORM | SQLAlchemy 2.0 async | Industry standard, mature async support |
| Database | PostgreSQL 16 | ARRAY types, full-text search, production-grade |
| HTTP client | httpx | Async, connection pooling, timeout control |
| RSS parsing | feedparser | Battle-tested, handles malformed RSS gracefully |
| Fuzzy matching | rapidfuzz | C-extension speed for title deduplication |
| Logging | structlog | Structured JSON logs, context binding |
| Validation | Pydantic v2 | Fast, typed, excellent FastAPI integration |
| Export | pandas + openpyxl | DataFrame operations, Excel formatting |
