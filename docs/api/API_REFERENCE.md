# API Reference

This document maps all REST endpoints currently implemented in the FastAPI application. All routes return JSON unless otherwise specified.

## Articles

### `GET /articles`
Retrieves a paginated list of normalized articles.
**Query Params**:
- `limit` (int): Number of items (max 100, default 50).
- `cursor` (str): Base64 encoded keyset cursor (published_at|id).
- `q` (str): Full-text search query against `search_vector`.
- `source_name` (str): Exact match source filter.
- `category` (ArticleCategory): Enum filter.
- `sentiment` (SentimentLabel): Enum filter.

### `GET /articles/{id}`
Retrieves a single article by UUID.
**Returns**: `ArticleResponse` or `404 Not Found`.

## Analytics

### `GET /analytics/trending`
Reads from `hourly_trends_mv` materialized view.
**Query Params**:
- `time_window_hours` (int): Bounding window for aggregation (max 168).
**Returns**: Array of `TrendingEntityResponse` sorted by momentum.

### `GET /analytics/sentiment`
Reads from `sentiment_summaries_mv` materialized view.
**Query Params**:
- `entity_name` (str, optional): Filters summary strictly to a known entity.
**Returns**: `SentimentSummaryResponse` (positive/neutral/negative counts).

## Pipeline

### `GET /pipeline/runs`
Fetches the historical logs of the ingestion orchestrator.
**Returns**: Array of `PipelineRunResponse` including `duration_ms` and `failed_sources`.

## Admin

### `GET /admin/pipeline/status`
Fetches current state of the backend pipeline mechanism.
**Returns**:
- `is_running` (bool): True if an ingestion cycle is currently active.
- `latest_run`: The most recent `PipelineRunResponse`.

### `GET /admin/enrichment/status`
Fetches counts of deterministic entities extracted.
**Returns**: `EnrichmentMetricsResponse`.

## Exports

### `GET /articles/export/csv`
Returns a streaming text/csv response of articles matching filters.
**Query Params**: Same as `GET /articles`.
**Returns**: CSV file download. Max bounded to 10,000 items to prevent DOS via DB cursor starvation.

## Observability

### `GET /metrics`
Exposes system health.
**Returns**: Plain text Prometheus format strings (`articles_ingested_total`, `pipeline_run_duration_seconds`, etc).
