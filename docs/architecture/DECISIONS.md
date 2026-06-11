# Architectural Decisions

This document logs critical architectural choices, the reasoning behind them, and the alternatives rejected.

## 1. Keyset Pagination over OFFSET
**Decision**: Use `published_at, id` cursors.
**Reasoning**: `OFFSET 50000 LIMIT 50` requires the database to scan and discard 50,000 rows before returning 50. Keyset pagination ensures $O(1)$ constant time lookup via B-Tree index traversal regardless of depth.
**Trade-offs**: Prevents the frontend from offering "Page 10" buttons; must use "Next Page" continuous scrolling.

## 2. APScheduler over Celery/Redis
**Decision**: Embed `AsyncIOScheduler` inside the FastAPI lifespan.
**Reasoning**: Minimizes infrastructure overhead (no Redis/RabbitMQ requirement).
**Trade-offs**: Ties the ingestion loop lifespan to the API lifespan. To scale APIs independently of ingestion, this must eventually be decoupled. Protected from horizontal overlap via `pg_try_advisory_lock`.

## 3. Deterministic Enrichment over LLM/Transformers
**Decision**: Use regex and dictionary lookups for `category` and `sentiment`.
**Reasoning**: Fetching 1,000 articles an hour and piping them through an LLM API or local `transformers` model causes a massive CPU/Latency bottleneck.
**Trade-offs**: Lower accuracy in sentiment detection.

## 4. PostgreSQL Materialized Views over Application-Level Aggregation
**Decision**: Aggregate metrics (`trending_sectors`, `sentiment_summary`) using DB materialized views.
**Reasoning**: Running `GROUP BY` counts over millions of text rows per HTTP request is impossible.
**Trade-offs**: Requires an explicit `REFRESH MATERIALIZED VIEW` command, which causes data to lag slightly behind real-time.
