# Validation Rules

## Chaos Testing
- Any new component touching the ingestion boundary must be tested against malformed data.
- Do not assume `feedparser` returns expected keys. Always use `.get()` safely.

## Database Validation
- `ON CONFLICT DO NOTHING` is the core of our deduplication strategy. Do not replace it with `SELECT` followed by `INSERT`, as this creates race conditions under concurrent load.

## Test Boundaries
- Tests must clean up their own state (e.g., executing `DELETE FROM feed_sources` after test completion) to prevent subsequent test failures.
