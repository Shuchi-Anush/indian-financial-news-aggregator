# Chaos Testing

## Intent
External RSS publishers do not adhere strictly to specifications. Feeds will drop nodes, repeat GUIDs, mangle XML, or permanently 404.

## Chaos Script
`backend/scripts/test_ingestion_chaos.py` spawns a synthetic `aiohttp` server exposing toxic feeds:
- `/broken_xml`: Missing closing tags.
- `/500`: Permanent 500 response.
- `/429`: Permanent 429 Too Many Requests.
- `/timeout`: Deliberate 5s delay.
- `/duplicates`: Duplicate GUIDs and URLs within the same payload.

## Expected Behavior
1. `feedparser` swallows the broken XML, attempting a best-effort parse.
2. `httpx` timeouts trigger the retry logic.
3. Persistent 500s trigger the Circuit Breaker (`OPEN` state).
4. Duplicates are silently absorbed by Postgres `ON CONFLICT DO NOTHING`.

## Failure Interpretation
If the chaos test causes a stack trace in `run_ingestion_cycle()`, the exception boundary in `RSSCollector.collect()` is improperly configured. This is a fatal bug that will lead to the APScheduler job failing entirely.
