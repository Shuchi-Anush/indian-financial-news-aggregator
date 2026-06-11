# Analytics, Enrichment, and Intelligence Layer Plan

This plan details the transformation of the platform from a news aggregation backend into a financial intelligence backend using deterministic, high-performance, and bounded-resource strategies.

## Proposed Changes

### 1. Database Schema Extensions (Phase 1, 2, 3, 4, 5, 6, 8)
We will create a new Alembic migration to add the following tables and fields:
- **`Article` updates**:
  - `sentiment_label` (VARCHAR)
  - `sentiment_score` (FLOAT)
  - `generated_summary` (TEXT)
- **New Tables**:
  - `article_entities` (id, article_id, entity, entity_type, confidence, extractor_version)
    - composite unique index `(article_id, entity, entity_type)`
  - `article_sectors` (id, article_id, sector, score)
    - composite unique index `(article_id, sector)`
  - `article_keywords` (id, article_id, keyword, weight)
    - composite unique index `(article_id, keyword)`
- **Analytics Materialized Views**:
  - `hourly_trends_mv`
  - `sentiment_summaries_mv`
  - Materialized views will use `CONCURRENTLY` refreshes (requires unique index) or standard refreshes based on Postgres compatibility.

### 2. Enrichment Pipeline Architecture (Phase 1)
- Create `src/app/enrichment/` directory.
- `orchestrator.py`: `EnrichmentOrchestrator` that takes a `NormalizedArticle` AFTER deduplication and runs it through isolated, async-safe processor stages.
- The pipeline order will be: RAW → NORMALIZED → DEDUPLICATED → ENRICHED → PERSISTED.
- Processors will be interface-driven, allowing future AI drop-ins.
- If a processor fails, it catches the exception, logs it, and continues. Metrics track processor_name, failure_count, failure_rate, and last_failure_timestamp.

### 3. Deterministic Engines (Phase 2, 3, 4, 5, 6)
- **Entities (`entities.py`)**: Uses optimized regex/dictionaries for major Indian financial entities. Implements strict bounds on memory and regex complexity.
- **Sectors (`sectors.py`)**: Explicit weighted keyword maps instead of ML heuristics.
- **Sentiment (`sentiment.py`)**: A financial lexicon dictionary mapping bullish/bearish words deterministically.
- **Keywords (`keywords.py`)**: Frequency analysis with stopword removal.
- **Summarization (`summaries.py`)**: Extractive summarizer hidden behind a feature flag (`ENABLE_SUMMARIZATION=False` by default). Skips tiny articles and bounds sentence counts.

### 4. Analytics Engine & APIs (Phase 7, 8, 9, 10)
- Create `src/app/analytics/` directory.
- `aggregations.py`: Functions to refresh materialized views asynchronously.
- `src/app/api/routes/analytics.py`: Add `/analytics/trending`, `/analytics/entities`, `/analytics/sectors`, `/analytics/sentiment`, `/analytics/activity`.
- Time windows supported (1h, 6h, 24h, 7d).
- Trending computation uses simple exponential time decay or weighted recent scoring.
- Update `articles.py` to support `?sector=X&sentiment=Y&entity=Z&keyword=W` query parameters using optimized `EXISTS` subqueries to avoid JOIN explosions.

### 5. Performance & Observability (Phase 11, 12)
- Ensure all dictionary lookups are compiled once at module load (O(1) or O(N) regex scanning).
- Use `structlog` for enrichment latency and failure tracking.
- Update `/admin/pipeline/status` and add `/admin/analytics/status` to expose new metrics.
- Track metrics using existing `registry` mechanism.

### 6. Validation (Phase 13, 14)
- Create `docs/analytics_validation.md`.
- Add test coverage in `tests/test_enrichment.py` and `tests/test_analytics.py`.
- Final verification via `mypy`, `ruff`, `pytest`, `compileall`, and Docker.

## Open Questions
- None. User has confirmed the deterministic architecture with 12 critical corrections. Execution will proceed.
