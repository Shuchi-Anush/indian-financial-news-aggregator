# Pipeline Flow

## Overview

The ingestion pipeline is the core value delivery mechanism. It runs as a single synchronous operation triggered by an API call.

```
Trigger (POST /api/v1/pipeline/run)
         │
         ▼
┌─────────────────┐
│  Load Active    │  Read feed_sources WHERE is_active = true
│  Feed Sources   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Collect      │  Fetch all feeds concurrently (asyncio.gather)
│  (per source)   │  Return list[ArticleCreate] per feed
│                 │  Log + skip failures per-feed
└────────┬────────┘
         │ list[ArticleCreate] (raw, unvalidated)
         ▼
┌─────────────────┐
│   Normalize     │  For each article:
│                 │  - Strip HTML from summary/content
│                 │  - Normalize unicode + whitespace
│                 │  - Parse dates → UTC
│                 │  - Trim/clean title
│                 │  - Generate content_hash (SHA-256)
│                 │  - Validate required fields
└────────┬────────┘
         │ list[ArticleCreate] (cleaned, hashed)
         ▼
┌─────────────────┐
│  Deduplicate    │  Three-layer dedup:
│                 │  1. URL exact match against DB
│                 │  2. content_hash exact match against DB
│                 │  3. Title fuzzy match (rapidfuzz, threshold 90%)
│                 │  Returns (unique_articles, duplicate_count)
└────────┬────────┘
         │ list[ArticleCreate] (unique only)
         ▼
┌─────────────────┐
│    Persist      │  Bulk insert unique articles
│                 │  Update feed_source.last_fetched_at
│                 │  Commit transaction
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Return Result  │  PipelineRunResult:
│                 │  - feeds_processed: int
│                 │  - articles_collected: int
│                 │  - articles_normalized: int
│                 │  - duplicates_found: int
│                 │  - articles_inserted: int
│                 │  - errors: list[str]
│                 │  - duration_seconds: float
└─────────────────┘
```

## Error Handling Strategy

| Failure Point | Behavior | Impact |
|---------------|----------|--------|
| Single feed HTTP timeout | Log warning, skip feed, continue | Partial collection |
| Single feed parse error | Log error, skip feed, continue | Partial collection |
| All feeds fail | Return result with 0 articles, errors populated | No data, but no crash |
| Normalizer fails on one article | Log error, skip article, continue | Partial normalization |
| DB connection error | Raise, return 500 | Full pipeline failure |
| Dedup DB query fails | Raise, return 500 | Full pipeline failure |

**Core principle:** Network/parse errors are recoverable (skip and continue). Database errors are not (fail the run).

## Deduplication Detail

### Layer 1: URL Exact Match
```sql
SELECT url FROM articles WHERE url IN (:urls)
```
Fastest check. Catches republished articles at the same URL.

### Layer 2: Content Hash Match
```sql
SELECT content_hash FROM articles WHERE content_hash IN (:hashes)
```
Catches same content published at different URLs (syndication).

### Layer 3: Fuzzy Title Match
```python
from rapidfuzz import fuzz
# Compare against titles from last 7 days (windowed)
ratio = fuzz.ratio(new_title, existing_title)
if ratio >= 90:
    mark_as_duplicate()
```
Catches near-duplicates with minor title variations (e.g., added/removed stock ticker).

## Concurrency Model

```python
# All feeds fetched concurrently
results = await asyncio.gather(
    *[collector.collect_feed(feed) for feed in active_feeds],
    return_exceptions=True,
)

# Separate successes from failures
for result in results:
    if isinstance(result, Exception):
        errors.append(str(result))
    else:
        all_articles.extend(result)
```

Each feed is an independent task. No feed blocks another.
