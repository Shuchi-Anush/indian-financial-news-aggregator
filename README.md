<h1 align="center">Indian Financial News Aggregator</h1>

<p align="center">
  An asynchronous, high-throughput backend platform engineered to ingest, normalize, deduplicate, and serve Indian financial market news at scale.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/FastAPI-async-009688?style=flat-square&logo=fastapi&logoColor=white"/>
  <img src="https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat-square&logo=postgresql&logoColor=white"/>
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white"/>
  <img src="https://img.shields.io/badge/License-MIT-lightgrey?style=flat-square"/>
  <img src="https://img.shields.io/badge/Release-v1.3.0-2ECC71?style=flat-square"/>
</p>

---

## Problem Statement

The Indian financial news ecosystem is highly fragmented. Market-moving information is dispersed across heterogeneous sources (e.g., Economic Times, Moneycontrol, LiveMint, Business Standard), each employing disparate XML/RSS schemas, inconsistent datetime formatting, and volatile availability constraints. 

Aggregating this data reliably poses significant engineering challenges:
- **Redundancy**: Aggressive scraping cycles lead to massive duplication without deterministic deduplication strategies.
- **Poison Pills**: Malformed XML payloads and unhandled exceptions can crash synchronous ingestion pipelines.
- **Analytics Bottlenecks**: Performing text search and time-series aggregation directly on raw scraped payloads exhausts database memory.

This platform exists to solve these problems. It is not merely a scraper; it is a decoupled ingestion architecture designed to normalize volatile upstream feeds into structured, indexed, and analytically queryable persistent records.

---

## Platform Overview

The Indian Financial News Aggregator provides a resilient, zero-touch backend pipeline. It autonomously manages the lifecycle of a news article from collection to consumption:

1. **Ingestion Orchestration**: Managed by an embedded `APScheduler` enforcing strict concurrency locks.
2. **Canonical Normalization**: Maps heterogeneous payloads to a strict, typed internal schema.
3. **Idempotent Persistence**: Utilizes cryptographic content hashing alongside native PostgreSQL `UPSERT` constraints.
4. **Analytics Materialization**: Periodically computes trending metrics in the background via materialized views.
5. **High-Speed Serving**: Delivers data to downstream consumers through an asynchronous FastAPI layer utilizing $O(1)$ keyset pagination.

---

## System Architecture

![System Architecture](docs/assets/system_architecture.png)

The system enforces strict execution boundaries. The deployment topology utilizes Docker Compose to orchestrate three primary components:
1. **Nginx Reverse Proxy**: Handles edge routing and rate limiting.
2. **FastAPI Backend**: Acts as a monolithic container handling both background ingestion jobs (via the scheduler thread) and outbound API requests (via the Uvicorn worker pool).
3. **PostgreSQL 16 Engine**: Serves as the persistence layer, storing raw payloads, normalized articles, and materialized analytics views.

---

## End-to-End Data Pipeline

![Pipeline Flow](docs/assets/pipeline_flow.png)

The ingestion pipeline models data transition through explicitly bounded states:

1. **Source Collection**: Circuit-breaker-protected async HTTP requests fetch XML payloads.
2. **Normalization**: HTML entities are stripped, timestamps are standardized, and schema variations are resolved into a `RawArticle` intermediate.
3. **Deduplication**: A deterministic SHA-256 hash is computed from the article's core content, preparing the payload for conflict resolution.
4. **Enrichment**: Configurable heuristics extract sectors (e.g., "Banking", "IT") and named entities.
5. **Persistence**: The async repository boundary writes the payload to PostgreSQL via `ON CONFLICT DO NOTHING`.
6. **Analytics**: Post-ingestion hooks trigger concurrent materialized view refreshes.
7. **Export**: API consumers stream gigabytes of tabular data via the bulk CSV export subsystem without exhausting server memory.

---

## Core Capabilities

| Capability | Engineering Implementation |
|---|---|
| **Asynchronous Orchestration** | Non-blocking `APScheduler` loop running concurrently with API workers. |
| **Idempotent Deduplication** | Hash-based primary collision avoidance pushed to the PostgreSQL storage engine. |
| **Keyset Pagination** | Cursor-based database scanning ensuring $O(1)$ query latency at high offset depths. |
| **Materialized Analytics** | Pre-calculated sentiment and frequency aggregates via `REFRESH MATERIALIZED VIEW CONCURRENTLY`. |
| **Resilient Observability** | Prometheus metric instrumentation and structured UUID-traced logging. |
| **Streaming Export** | Server-side cursors yielding data chunks, preventing out-of-memory (OOM) crashes. |

---

## Operational Metrics

The platform currently executes the following operational features fully autonomously:
- **Automated Bootstrap**: Fresh environments execute Alembic schema migrations natively on boot.
- **Feed Seeding**: Initial source dictionaries are idempotently loaded into the database.
- **Ingestion Execution**: The pipeline natively collects from 5 primary RSS sources at 15-minute intervals.
- **Analytics Serving**: Materialized views reflect fresh data immediately after pipeline cycles.

---

## Technology Stack

### Backend & Orchestration
| Component | Technology |
| --- | --- |
| **Transport / Framework** | FastAPI (Python 3.11+) |
| **Data Validation** | Pydantic v2 |
| **Job Scheduling** | APScheduler (AsyncIOScheduler) |
| **HTTP Client** | `httpx` (Fully Async) |

### Persistence & Data
| Component | Technology |
| --- | --- |
| **Database** | PostgreSQL 16 (JSONB, tsvector) |
| **ORM** | SQLAlchemy 2.x (Async Engine) |
| **Migrations** | Alembic |

### Infrastructure & Tooling
| Component | Technology |
| --- | --- |
| **Containerization** | Docker, Docker Compose |
| **Proxy** | Nginx |
| **Metrics** | Prometheus Client |
| **Package Manager** | `uv` |

---

## Repository Structure

```text
indian-financial-news-aggregator/
├── backend/                  # Monolithic Python backend
│   ├── migrations/           # Alembic revision history
│   ├── src/app/              # Application logic (routers, domains, services)
│   ├── tests/                # Validation suites
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/                 # Temporary operational validation dashboard
├── infra/                    # Reverse proxy configurations
├── docs/                     # Architectural records and operational validations
├── docker-compose.prod.yml   # Production deployment manifest
└── README.md                 # Project landing page
```

---

## Quick Start

### 1. Zero-Touch Docker Deployment
The recommended pathway to validate the platform is via the production Docker manifest, which mimics the target deployment topology.

```bash
git clone https://github.com/Shuchi-Anush/indian-financial-news-aggregator.git
cd indian-financial-news-aggregator

cp .env.example .env

docker compose -f docker-compose.prod.yml up -d --build
```
*Upon execution, the platform will provision the database, migrate schemas, seed feed sources, launch the ingestion scheduler, and expose the API at `localhost:8000`.*

### 2. Local Development Environment
For engineers modifying the ingestion pipeline:

```bash
cd backend
uv sync
alembic upgrade head
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

---

## Validation & Audit Trail

We do not claim "production-readiness" without evidence. The system's robustness has been thoroughly validated through multiple engineering audits:

- **Reproducibility Validation**: [reproducibility_audit.md](docs/validation/reproducibility_audit.md) — Proves zero-touch bootstrapping.
- **Ingestion Audit**: [final_ingestion_audit_report.md](docs/validation/final_ingestion_audit_report.md) — Demonstrates pipeline correctness, parser resiliency, and deduplication logic.
- **Contract Audit**: [frontend_backend_contract_audit.md](docs/validation/frontend_backend_contract_audit.md) — Validates JSON schema boundaries between the API and presentation layers.
- **Release Documentation**: [v1.2.0-demo-ready.md](docs/releases/v1.2.0-demo-ready.md) — Detailed operational metrics from recent release checkpoints.

---

## Roadmap

**Current State (v1.3.0)**: The backend data ingestion platform is fully materialized, idempotent, and heavily observable. The deduplication logic and analytics generation execute flawlessly in production-simulated environments.

**Near-Term**: 
1. **Presentation Layer Migration**: Transitioning from the temporary Streamlit operational dashboard to a highly performant **Next.js** React application.
2. **Distributed Queuing**: Decoupling the embedded `APScheduler` in favor of Celery/Redis to distribute fetch jobs across multiple worker nodes.

**Long-Term**: 
1. **ML Inference Pipeline**: Asynchronous enrichment queues for Named Entity Recognition (NER) and context-aware sentiment analysis.
2. **Federated Streaming**: Exposing Kafka or WebSockets for real-time downstream consumer syndication.

---

## Documentation Index

Deep architectural knowledge and design rationales are maintained internally:

- [System Architecture Walkthrough](docs/README_ARCHITECTURE.md)
- [Backend Engineering Handbook](backend/README.md)
- [Frontend Architecture Roadmap](frontend/README.md)

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
