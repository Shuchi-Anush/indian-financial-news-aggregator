# Analytics & Enrichment Validation Guide

## Overview

The Analytics and Enrichment layer of the Indian Financial News Aggregator is responsible for augmenting raw news data with intelligence, extracting entities, classifying sectors, analyzing sentiment, and generating summaries. This document validates the architecture and demonstrates how to interact with the new capabilities.

## Architecture

1. **Enrichment Orchestrator (`EnrichmentOrchestrator`)**:
   Runs post-deduplication inside the ingestion pipeline. It coordinates deterministic extractors (regex/lexicon-based) and bounds execution using Prometheus metrics to observe latency and failures.

2. **Deterministic Processors**:
   - `EntityExtractor`: Extracts Companies, Regulators, and Individuals using pre-compiled regex bound by max-length inputs.
   - `SectorClassifier`: Maps text into canonical sectors (e.g., Banking, Tech, Real Estate).
   - `SentimentEngine`: Uses a lexicon-based bounded approach to map strings to `POSITIVE`, `NEGATIVE`, or `NEUTRAL`.
   - `KeywordExtractor`: Extracts frequencies and filters stopwords.

3. **Database Materialized Views**:
   - `hourly_trends_mv`: Aggregates hourly entity and sector trends.
   - `sentiment_summaries_mv`: Aggregates daily sentiment summaries.
   These are refreshed automatically at the end of the ingestion pipeline.

## API Validation

### Analytics Endpoints

Query the aggregated analytics data via the following REST endpoints.

**Trending Entities**
```bash
curl "http://localhost:8000/analytics/trending?time_window_hours=24&limit=10"
```
Returns a list of trending entities scored by an exponential time decay function, weighting recent hourly buckets higher.

**Sentiment Summaries**
```bash
curl "http://localhost:8000/analytics/sentiment?time_window_days=7"
```
Returns a list of date buckets and sentiment labels with aggregated counts.

### Search and Filtering Endpoints

The `GET /articles` endpoint has been upgraded to support `EXISTS` subqueries over the normalized enrichment relationships.

**Filter by Entity**
```bash
curl "http://localhost:8000/articles?entity=Reserve%20Bank%20of%20India"
```

**Filter by Sector**
```bash
curl "http://localhost:8000/articles?sector=Banking"
```

**Filter by Sentiment**
```bash
curl "http://localhost:8000/articles?sentiment=POSITIVE"
```

### Operational Metrics (Admin)

Monitor the health of the enrichment layer via Admin APIs.

**Enrichment Status**
```bash
curl "http://localhost:8000/admin/enrichment/status"
```
Returns counts of total extracted entities, sectors, and keywords.

**Analytics Views Status**
```bash
curl "http://localhost:8000/admin/analytics/status"
```
Returns row counts for the materialized views to verify that the aggregation pipeline is successfully saving data.

### Prometheus Metrics

The system exports the following metrics on `/metrics`:

- `enrichment_latency_seconds`: Histogram of processor latencies.
- `enrichment_failures_total`: Counter for failure tracking by stage.
- `analytics_views_refresh_duration_seconds`: Histogram of materialized view refresh latency.

## Next Steps

To manually invoke the entire pipeline and test the aggregation, run the manual ingestion script:

```bash
uv run python scripts/manual_ingestion.py
```
Wait for completion, then query `/admin/analytics/status` to observe the materialized views updating.
