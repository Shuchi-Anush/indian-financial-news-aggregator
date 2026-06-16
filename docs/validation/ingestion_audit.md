# Ingestion Pipeline End-to-End Audit

## Executive Summary

**The ingestion pipeline has never processed a single article.** Four root-cause blockers were identified through direct code and database inspection.

---

## Diagnostic Checklist

| # | Question | Status | Evidence |
|---|---|---|---|
| 1 | Does `feed_sources` contain records? | ❌ **ZERO rows** | `SELECT count(*) FROM feed_sources` → 0. No seed script exists anywhere. Migration creates schema only. |
| 2 | Are collectors actually fetching feeds? | ❌ **Never invoked** | `_instantiate_collector()` maps slugs to collector classes, but since `get_active_sources()` returns `[]`, no collector is ever instantiated. |
| 3 | Is APScheduler executing jobs? | ⚠️ **Fires but no-ops** | Scheduler fires `run_ingestion_cycle()` → calls `get_active_sources()` → gets `[]` → logs `no_collectors_active` → returns. |
| 4 | Are articles reaching `raw_articles`? | ❌ **No** | Table is empty. Pipeline never reaches `save_raw_articles()`. |
| 5 | Does normalization succeed? | ⚠️ **Partial risk** | `MAX_ARTICLE_AGE_HOURS = 72`. Moneycontrol's RSS feed has dates from **April 2024** — all 4 entries would be rejected by the freshness filter. ET, LiveMint, BS, and NDTV Profit have fresh articles (today's date). |
| 6 | Does deduplication reject everything? | ✅ **Not a blocker** | `Deduplicator` checks URL/hash against existing DB rows. Since `articles` is empty, nothing would be rejected on first run. |
| 7 | Do repositories persist articles? | ⚠️ **Would crash** | `refresh_analytics_views()` calls `REFRESH MATERIALIZED VIEW hourly_trends_mv` and `sentiment_summaries_mv`. Neither view exists — **no CREATE DDL anywhere in the codebase**. This would throw an unhandled SQL error at the end of every pipeline run. |

---

## Root Cause Chain

```
feed_sources table is EMPTY
    ↓
get_active_sources() returns []
    ↓
no collectors are instantiated
    ↓
pipeline.run() is never called
    ↓
no articles fetched, normalized, or persisted
    ↓
Even if above is fixed: REFRESH MATERIALIZED VIEW will crash (views don't exist)
```

## Blockers (Ordered by Severity)

### BLOCKER 1: No Seed Data (Critical)
- **Location:** Alembic migration `21af7d79c2f7_initial_schema.py` creates `feed_sources` table but never inserts rows.
- **Impact:** The entire pipeline is dead. APScheduler fires into the void.
- **Fix:** Insert seed data for the 5 configured source slugs with verified RSS URLs.

### BLOCKER 2: Materialized Views Never Created (Critical)
- **Location:** `repository.py:148-149` executes `REFRESH MATERIALIZED VIEW hourly_trends_mv` and `sentiment_summaries_mv`.
- **Impact:** Even if articles are ingested, the pipeline's final step will crash with `relation "hourly_trends_mv" does not exist`.
- **Fix:** Create the materialized views DDL.

### BLOCKER 3: Moneycontrol Feed is Stale (Low)
- **Location:** RSS feed at `https://www.moneycontrol.com/rss/marketreports.xml` has `lastBuildDate: Tue, 23 Apr 2024`.
- **Impact:** All 4 entries will be rejected by the normalizer's `MAX_ARTICLE_AGE_HOURS = 72` freshness filter. Not a fatal issue since other feeds are fresh.

### BLOCKER 4: CNBC TV18 RSS URL Unknown (Low)
- **Location:** `ingestion_jobs.py` maps slug `cnbc-tv18-markets` to `CNBCTV18RSSCollector`, but no seed data means no URL was ever configured.
- **Impact:** Need to determine a working RSS URL for CNBC TV18.

## RSS Feed Verification Results (Live Probe — June 16, 2026)

| Source | URL | HTTP | Entries | Latest Date | Verdict |
|---|---|---|---|---|---|
| Economic Times | `economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms` | 200 | 50 | Jun 16 2026 | ✅ Fresh |
| LiveMint | `livemint.com/rss/markets` | 200 | 35 | Jun 16 2026 | ✅ Fresh |
| Business Standard | `business-standard.com/rss/markets-106.rss` | 200 | 35 | Jun 16 2026 | ✅ Fresh |
| NDTV Profit | `feeds.feedburner.com/ndtvprofit-latest` | 200 | 20 | Jun 16 2026 | ✅ Fresh |
| Moneycontrol | `moneycontrol.com/rss/marketreports.xml` | 200 | 4 | Apr 23 2024 | ⚠️ Stale |
