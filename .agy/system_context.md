# AGY System Context — Indian Financial News Aggregator

## Project Goal

Build a production-minded Indian Financial News Aggregator capable of:

* collecting Indian financial news
* normalizing and deduplicating content
* storing structured article data
* exporting filtered datasets
* serving APIs and frontend clients

The system is website-first with future app readiness.

---

# Architecture Philosophy

The project follows:

* modular layered architecture
* production-minded backend design
* async-first I/O
* separation of concerns
* extensibility over shortcuts

Avoid monolithic logic.

---

# Technology Stack

Backend:

* FastAPI
* SQLAlchemy 2.x async
* PostgreSQL
* Pydantic v2
* structlog
* uv package manager

Infrastructure:

* Docker Compose

---

# Repository Structure

src/app/

* api/ → HTTP layer only
* services/ → business orchestration
* collectors/ → external data ingestion only
* processors/ → normalization/deduplication/transformation
* exporters/ → CSV/XLSX/HTML/PDF generation
* models/ → ORM entities
* schemas/ → Pydantic DTOs
* db/ → engine/session/base
* core/ → config/logging/middleware/startup

---

# Architectural Rules

## API Layer

* Thin routes only
* No business logic
* No direct DB logic beyond DI

## Services Layer

* Central orchestration layer
* Coordinates collectors/processors/exporters

## Collectors

* Only fetch raw external data
* No normalization
* No deduplication
* No DB writes

## Processors

* Normalize raw payloads
* Deduplicate articles
* Prepare canonical structures

## Exporters

* Generate downloadable output formats only

---

# Database Principles

* Use SQLAlchemy 2.x typed declarative style
* Async-first engine/session usage
* Prefer explicit relationships
* Add indexes intentionally
* Design models for future scaling

---

# Coding Standards

* Typed Python everywhere
* Avoid circular imports
* Avoid hidden side effects
* Avoid global mutable state
* Prefer composition over inheritance
* Keep modules focused

---

# Logging

* Use structlog
* Structured logs only
* Include request_id where possible

---

# Error Handling

Use centralized domain exceptions.

Avoid leaking raw framework/database exceptions to API responses.

---

# Scope Discipline

Implement only the currently requested phase.

Do not prematurely add:

* authentication
* caching
* Celery
* Kafka
* ML pipelines
* frontend business logic
* websocket systems

---

# Current Progress

Completed:

* runtime foundation
* middleware
* logging
* exception handling
* async DB lifecycle
* FastAPI startup wiring

Upcoming:

* ORM models
* schemas
* collectors
* normalization pipeline
* deduplication engine
* export pipeline

# Pipeline Philosophy

The ingestion pipeline follows a staged architecture:

raw ingestion
→ normalization
→ deduplication
→ persistence
→ export/API serving

Each stage owns a single responsibility.

# Persistence Semantics

Database persistence must be:

* idempotent
* restart-safe
* duplicate-safe
* transactionally isolated
* async-safe

Prefer database-enforced correctness over in-memory assumptions.

Collectors must never:

* compute dedup hashes
* canonicalize articles
* enrich content
* classify articles
* write to the database
