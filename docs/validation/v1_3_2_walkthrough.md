# v1.3.2 Production Release Walkthrough & Audit

## 1. Root Cause Report
**Moneycontrol Markets (Zero Persisted Articles):**
*   **Observation**: `success_count = 13`, `health_score = 100`, persisted articles = 0.
*   **Root Cause**: Stale Data Rejection via Quality Gate.
*   **Evidence**: The feed is technically healthy (HTTP 200, valid XML), meaning the `BaseRSSCollector` network fetch succeeds. However, the last recorded item in the `moneycontrol-markets` RSS feed dates back to April 2024.
*   **Execution Trace**: 
    `BaseRSSCollector.collect()` -> `IngestionPipeline.run()` -> `Normalizer.normalize()` -> `if age > timedelta(hours=MAX_ARTICLE_AGE_HOURS): log.info("article_rejected_stale"); return None`.
    The normalizer silently filters the 2-year-old articles by design.

**Business Standard (Circuit Breaker OPEN):**
*   **Observation**: Zero fetched, OPEN state.
*   **Root Cause**: The domain `business-standard.com` has instituted Akamai Bot Manager or Cloudflare WAF protections that block programmatic RSS consumption from standard data center IPs (like GCP/AWS).
*   **Execution Trace**: `BaseRSSCollector` receives an `HTTP 403 Forbidden` response. The pipeline logs `collector_failed` and the circuit breaker increments consecutive failures until it correctly trips `OPEN`.

**High Duplicate Rate:**
*   **Root Cause**: The RSS feeds update infrequently relative to our `APScheduler` cron interval (e.g., fetching every 15 minutes but publishers only post 5 articles a day).
*   **Execution Trace**: `IngestionPipeline.run()` -> `_generate_canonical_hash(title + content)`. The deduplicator correctly identifies articles it has seen in previous cycles. This is expected and correct behavior.

## 2. Architecture Audit Report
**Identified Stale Code / Debt:**
*   `manual_ingestion.py` was hardcoded to rely on `LiveMintRSSCollector`, `EconomicTimesRSSCollector`, etc.
*   The subclass collector `.py` files inside `app/collectors/rss/` are completely dead code now that `ingestion_jobs.py` natively maps everything to `BaseRSSCollector`.

## 3. Feed Expansion Readiness Report
*   **Validation**: The 7 candidate feeds (ET Economy, ET Industry, LiveMint Companies, LiveMint Money, Business Today Markets, Business Today Corporate, NDTV Profit) were pre-validated for standard RSS 2.0 formatting, freshness, and absence of aggressive WAF blocking.
*   **Risk Profile**: Low. The ingestion pipeline handles scale horizontally. The database connection pool handles the negligible insert throughput.

## 4. Exact Files Modified
*   `backend/src/app/tasks/manual_ingestion.py`
*   `backend/v1_3_2_feed_expansion.sql` (Created & Executed)

## 5. Exact Diffs

**`backend/src/app/tasks/manual_ingestion.py`**
```diff
@@ -17,11 +17,7 @@
 
 import structlog
 
-from app.collectors.rss.businessstandard import BusinessStandardRSSCollector
-from app.collectors.rss.cnbctv18 import CNBCTV18RSSCollector
-from app.collectors.rss.economictimes import EconomicTimesRSSCollector
-from app.collectors.rss.livemint import LiveMintRSSCollector
-from app.collectors.rss.moneycontrol import MoneycontrolRSSCollector
+from app.collectors.rss.base_rss import BaseRSSCollector
 from app.core.logging import setup_logging
 from app.db.repository import IngestionRepository
 from app.db.session import dispose_engine, get_session_factory, initialize_database
@@ -33,7 +33,7 @@
     {
         "name": "Moneycontrol Markets",
         "url": "https://www.moneycontrol.com/rss/MCtopnews.xml",
-        "collector_cls": MoneycontrolRSSCollector,
+        "collector_cls": BaseRSSCollector,
     },
     {
         "name": "Economic Times Markets",
@@ -40,4 +40,4 @@
-        "collector_cls": EconomicTimesRSSCollector,
+        "collector_cls": BaseRSSCollector,
     },
     {
         "name": "LiveMint Markets",
@@ -44,4 +44,4 @@
-        "collector_cls": LiveMintRSSCollector,
+        "collector_cls": BaseRSSCollector,
     },
     {
         "name": "Business Standard Markets",
@@ -48,4 +48,4 @@
-        "collector_cls": BusinessStandardRSSCollector,
+        "collector_cls": BaseRSSCollector,
     },
     {
         "name": "CNBC TV18 Markets",
@@ -52,4 +52,4 @@
-        "collector_cls": CNBCTV18RSSCollector,
+        "collector_cls": BaseRSSCollector,
     },
 ]
```

## 6. Validation Commands
To verify the deployment:
```bash
# Check the DB for the new active feeds
docker exec -it finnews-db-prod psql -U postgres -d financial_news -c "SELECT slug, is_active FROM feed_sources;"

# Check live backend ingestion logs to confirm APScheduler runs against new feeds
docker compose logs -f backend | grep "ingestion_cycle"
```

## 7. Rollback Plan
If ingestion CPU spikes or feeds cause massive errors:
```bash
# Deactivate the newly added feeds
docker exec -it finnews-db-prod psql -U postgres -d financial_news -c "
UPDATE feed_sources SET is_active = false 
WHERE slug IN ('et-economy', 'et-industry', 'livemint-companies', 'livemint-money', 'business-today-markets', 'business-today-corporate', 'ndtv-profit');
"
docker restart finnews-backend-prod
```

## 8. Recommended Next Branch
`feature/collector-code-deletion` (To explicitly run `git rm` against the orphaned collector wrappers pending explicit permission, and removing the stale SQL migration file).

## 9. Recommended Next Release Tag
**`v1.3.2-feed-expansion-complete`**
