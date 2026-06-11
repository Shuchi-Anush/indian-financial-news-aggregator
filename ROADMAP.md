# Engineering Roadmap

This document outlines the evolutionary trajectory of the platform, separating completed, strictly implemented features from future scale-out mechanisms.

## Completed & Validated
- [x] Dockerized PostgreSQL 16 + FastAPI backbone.
- [x] Async SQLAlchemy 2.0 Repository layer.
- [x] Alembic migration strategy and enforcement.
- [x] Concurrent RSS Fetching (bounded asyncio.gather).
- [x] Normalization & Sanitization pipelines.
- [x] SHA-256 Content Hash Deduplication.
- [x] Zero-Offset Keyset Pagination for APIs.
- [x] Materialized View aggregations for analytics.
- [x] GIN-indexed full-text search capability.
- [x] Resilient Embedded Orchestration (`APScheduler`).
- [x] Observability (`prometheus-client` integration).
- [x] Circuit Breaker mechanism for failed sources.

## In-Progress / Stabilization
- [ ] Frontend ingestion connectivity.
- [ ] Grafana dashboard compilation from Prometheus metrics.
- [ ] Backgrounding materialized view refreshes (`REFRESH MATERIALIZED VIEW CONCURRENTLY`).

## Future Infrastructure Roadmap
If dataset scales beyond single-node performance bounds (10M+ articles):
- **DB Partitioning**: Transition the `articles` table to native PostgreSQL Time-Series Partitioning (`PARTITION BY RANGE (published_at)`).
- **Search Offloading**: Deprecate PostgreSQL `tsvector` in favor of pushing `Article` documents to ElasticSearch/OpenSearch.
- **Dedicated Orchestrator**: Migrate from embedded `APScheduler` to a standalone Celery + Redis cluster or Airflow, decoupling ingestion memory usage from API memory usage.

## Future Machine Learning Roadmap
Current enrichment relies on deterministic regex dictionaries. Future evolution:
- **Zero-shot Classification**: Utilize local ONNX models (e.g., `distilbert`) or external LLM API batch jobs to replace coarse regex sentiment matching.
- **Entity Resolution**: Implement real Named Entity Recognition (NER) to map `Reliance` and `RIL` to the same company identifier natively.
- **Embedding Search**: Generate vector embeddings for articles and store in `pgvector` for semantic search rather than lexical `tsvector` search.
