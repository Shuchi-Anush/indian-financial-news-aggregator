# System Architecture

## Overview

Single-process FastAPI monolith with PostgreSQL, deployed via Docker Compose on a single host.

```
┌──────────────────────────────────────────────────────┐
│                    Docker Host                        │
│                                                       │
│  ┌─────────────────────┐   ┌───────────────────────┐ │
│  │   finnews-backend    │   │     finnews-db        │ │
│  │                      │   │                       │ │
│  │   FastAPI + Uvicorn  │──▶│   PostgreSQL 16       │ │
│  │   Python 3.12        │   │   Alpine              │ │
│  │   Port: 8000         │   │   Port: 5432          │ │
│  └─────────────────────┘   └───────────────────────┘ │
│           │                          │                │
│           │ exposed                  │ volume          │
│           ▼                          ▼                │
│      host:8000                postgres_data           │
└──────────────────────────────────────────────────────┘
```

## Component Diagram

```
                    ┌─────────────┐
                    │   Client    │
                    │ (curl/UI)   │
                    └──────┬──────┘
                           │ HTTP
                           ▼
                    ┌─────────────┐
                    │  Middleware  │
                    │  - CORS     │
                    │  - Req ID   │
                    │  - Logging  │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   Routes    │
                    │  /api/v1/*  │
                    └──────┬──────┘
                           │ delegates
              ┌────────────┼────────────┐
              ▼            ▼            ▼
       ┌────────────┐ ┌────────┐ ┌──────────┐
       │  Pipeline   │ │Article │ │  Export   │
       │  Service    │ │Service │ │  Service  │
       └──────┬─────┘ └───┬────┘ └────┬─────┘
              │            │           │
    ┌─────────┼─────┐      │           │
    ▼         ▼     ▼      │           ▼
┌────────┐ ┌─────┐ ┌────┐ │    ┌──────────┐
│Collect-│ │Norm-│ │De- │ │    │ Exporters│
│ors     │ │aliz.│ │dup │ │    │ CSV/XLSX │
└────────┘ └─────┘ └────┘ │    └──────────┘
                           │
                    ┌──────▼──────┐
                    │  PostgreSQL │
                    │  (asyncpg)  │
                    └─────────────┘
```

## Request Flow

1. Client sends HTTP request
2. Middleware attaches request ID, starts timing
3. Route handler validates input via Pydantic
4. Route calls service method with typed parameters
5. Service executes business logic + DB queries
6. Service returns Pydantic schema
7. Route serializes response
8. Middleware logs request completion with timing

## Pipeline Flow

1. `POST /api/v1/pipeline/run` triggers `PipelineService.run()`
2. Pipeline loads active `FeedSource` records from DB
3. Collectors run concurrently (`asyncio.gather`) — one per feed
4. Raw articles normalized (HTML strip, date parsing, hash generation)
5. Deduplicator checks URL uniqueness, content hash, and fuzzy title similarity
6. Unique articles bulk-inserted into `articles` table
7. Pipeline returns run summary (counts per stage)

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Runtime | Python 3.12 | Slim Docker image |
| Framework | FastAPI 0.115+ | Async web framework |
| Server | Uvicorn | ASGI server |
| ORM | SQLAlchemy 2.0 | Async database access |
| DB Driver | asyncpg | PostgreSQL async driver |
| Validation | Pydantic v2 | Request/response schemas |
| HTTP | httpx | Async HTTP client |
| RSS | feedparser | RSS/Atom parsing |
| Fuzzy | rapidfuzz | Near-duplicate detection |
| Logging | structlog | Structured JSON logging |
| Export | pandas + openpyxl | CSV/Excel generation |
| Config | pydantic-settings | Typed env var loading |
| Retry | tenacity | HTTP retry with backoff |
| Package | uv | Fast dependency management |
| Deploy | Docker Compose | Container orchestration |
