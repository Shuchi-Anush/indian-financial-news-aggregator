# Database Validation Queries

The following queries are production-grade validation queries for verifying the operational state of the Indian Financial News Aggregator ingestion pipeline via `psql`.

## 1. Table Verification
Check the row counts for all critical pipeline tables.
```sql
SELECT
    (SELECT count(*) FROM articles) AS canonical_articles,
    (SELECT count(*) FROM raw_articles) AS raw_articles,
    (SELECT count(*) FROM failed_articles) AS failed_articles,
    (SELECT count(*) FROM pipeline_runs) AS pipeline_runs,
    (SELECT count(*) FROM feed_sources) AS feed_sources;
```

## 2. Dedup Verification
Verify the global duplicate ratio. High deduplication is expected during subsequent ingestion runs.
```sql
SELECT 
    sum(inserted_count) as total_inserted,
    sum(duplicate_count) as total_duplicates,
    ROUND((sum(duplicate_count)::numeric / NULLIF(sum(inserted_count) + sum(duplicate_count), 0)) * 100, 2) as duplicate_percentage
FROM pipeline_runs;
```

## 3. Replayability Verification
Verify that `raw_articles` is consistently acting as the system-of-record. The number of raw articles should roughly equal `canonical_articles + failed_articles + duplicates`.
```sql
SELECT 
    r.pipeline_run_id,
    count(*) as raw_collected,
    pr.inserted_count as canonical_saved,
    pr.duplicate_count as duplicates_skipped,
    (SELECT count(*) FROM failed_articles f WHERE f.pipeline_run_id = r.pipeline_run_id) as failed_items
FROM raw_articles r
JOIN pipeline_runs pr ON pr.id = r.pipeline_run_id
GROUP BY r.pipeline_run_id, pr.inserted_count, pr.duplicate_count
ORDER BY r.pipeline_run_id DESC
LIMIT 10;
```

## 4. Failed Article Inspection
Analyze the distribution of failures by stage and error type.
```sql
SELECT 
    failure_stage,
    error_type,
    count(*) as failure_count,
    MAX(created_at) as latest_failure
FROM failed_articles
GROUP BY failure_stage, error_type
ORDER BY failure_count DESC;
```

## 5. Source Health Inspection
Identify underperforming or blocked RSS feed sources.
```sql
SELECT 
    name, 
    slug, 
    health_status, 
    consecutive_failures, 
    error_type,
    last_success_at,
    last_failed_at
FROM feed_sources
WHERE health_status != 'HEALTHY'
ORDER BY consecutive_failures DESC;
```

## 6. Pipeline Lineage Tracing
Find the exact pipeline run and raw payload that produced a specific canonical article by matching the `url`.
```sql
SELECT 
    a.id as canonical_id,
    r.id as raw_id,
    r.pipeline_run_id,
    a.quality_score,
    r.created_at as raw_collected_at
FROM articles a
JOIN raw_articles r ON r.raw_payload->>'link' = a.url
WHERE a.url LIKE '%your-target-url-here%'
LIMIT 1;
```

## 7. Recent Ingestion Runs
Monitor the most recent pipeline executions and their outcomes.
```sql
SELECT 
    id,
    started_at,
    status,
    inserted_count,
    duplicate_count,
    EXTRACT(EPOCH FROM (completed_at - started_at)) as duration_sec,
    failed_sources
FROM pipeline_runs
ORDER BY started_at DESC
LIMIT 10;
```

## 8. Duplicate URL Checks
Ensure the `UNIQUE(url)` constraint is functioning and no logical duplicates exist.
```sql
SELECT url, count(*) as frequency
FROM articles
GROUP BY url
HAVING count(*) > 1;
```

## 9. Duplicate content_hash Checks
Ensure the `UNIQUE(content_hash)` constraint is functioning, verifying the deduplication processor's integrity.
```sql
SELECT content_hash, count(*) as frequency
FROM articles
GROUP BY content_hash
HAVING count(*) > 1;
```

## 10. Raw vs Canonical Comparison
Visually inspect how the pipeline mutated a raw JSON payload into a canonical article.
```sql
SELECT 
    r.raw_payload->>'title' as raw_title,
    a.title as canonical_title,
    r.raw_payload->>'published' as raw_published,
    a.published_at as canonical_published,
    a.quality_score
FROM articles a
JOIN raw_articles r ON r.raw_payload->>'link' = a.url
ORDER BY a.created_at DESC
LIMIT 5;
```
