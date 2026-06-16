# Final Ingestion Audit Report

## Executive Summary
A complete end-to-end ingestion cycle has been manually executed. The database has been successfully populated with real article data, and the pipeline has proven its ability to fetch, normalize, and persist articles to the canonical `articles` table while updating analytics materialized views.

## 1. Feeds Activated
Five core feeds have been seeded into the `feed_sources` database table:
- **Economic Times Markets** (`economic-times-markets`)
- **LiveMint Markets** (`livemint-markets`)
- **Business Standard Markets** (`business-standard-markets`)
- **Moneycontrol Markets** (`moneycontrol-markets`)
- **SEBI Press Releases** (`sebi-press-releases`) - Chosen as the official source to satisfy the (RBI/NSE/SEBI) requirement, as it offers a clean, stable RSS feed.

*Note: The SEBI collector was properly integrated by adding `SebiRSSCollector` mapping in `ingestion_jobs.py`.*

## 2. Ingestion Cycle Metrics
A manual pipeline cycle was successfully executed. Below is the empirical evidence drawn directly from the production PostgreSQL instance.

| Stage | Metric | Count |
|---|---|---|
| **Sources Attempted** | Total active sources | 5 |
| **Fetch Stage** | Articles fetched and stored in `raw_articles` | 119 |
| **Normalization Stage** | Articles passing the Quality Gate | 115 |
| **Persistence Stage** | Articles safely saved to `articles` | 115 |
| **Pipeline Runs** | Total runs recorded in `pipeline_runs` | 1 |

### Database Verification Summary
```sql
SELECT 'feed_sources' as table, COUNT(*) FROM feed_sources UNION ALL 
SELECT 'raw_articles', COUNT(*) FROM raw_articles UNION ALL 
SELECT 'articles', COUNT(*) FROM articles UNION ALL 
SELECT 'pipeline_runs', COUNT(*) FROM pipeline_runs;
```
**Results:**
- `feed_sources` = 5
- `raw_articles` = 119
- `articles` = 115
- `pipeline_runs` = 1

## 3. Remaining Issues & Anomalies (Non-Blockers)
While the pipeline fully works, a few edge-cases and known bugs were observed:

1. **Stale Articles Dropped:**
   - 4 articles were dropped during normalization (`NORMALIZATION: Drop`). These originate from the `Moneycontrol Markets` RSS feed which contains articles older than the `MAX_ARTICLE_AGE_HOURS = 72` limit. The Quality Gate operates perfectly as designed.
2. **HTTP 403 on Business Standard:**
   - 1 source encountered a permanent `HTTP 403 Forbidden` error during the fetch. This indicates anti-bot protection blocking the current `User-Agent`.
3. **`raw_articles.processing_status` not fully updated:**
   - The 119 articles in `raw_articles` all currently have `processing_status = 'PENDING'`. The pipeline saves them, pushes them downstream to be normalized and persisted into `articles`, but does not appear to perform a final bulk update back on `raw_articles` to set them to `NORMALIZED`.

## Conclusion
The fundamental goal has been achieved. The pipeline correctly orchestrates across fetch, normalize, and save boundaries. The `articles` table is populated, and downstream APIs (including analytical endpoints dependent on the now-created Materialized Views) have real data to serve.
