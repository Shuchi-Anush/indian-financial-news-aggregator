# Query Validation & Benchmarking Guide

## 1. EXPLAIN ANALYZE Validation Queries

### Keyset Pagination (Default Listing)
Ensure keyset pagination utilizes the `ix_articles_published_id_desc` index instead of a full table scan or sort step.

```sql
EXPLAIN ANALYZE
SELECT id, title, source_name, published_at
FROM articles
WHERE (published_at < '2026-06-10 10:00:00+00') 
   OR (published_at = '2026-06-10 10:00:00+00' AND id < '123e4567-e89b-12d3-a456-426614174000')
ORDER BY published_at DESC NULLS LAST, id DESC
LIMIT 51;
```

**Expected behavior:**
- `Index Scan using ix_articles_published_id_desc on articles`
- `Sort` operation must not appear.
- Execution time should be `< 2ms` regardless of total table size.

### Full-Text Search
Ensure search utilizes the `ix_articles_search_vector` GIN index.

```sql
EXPLAIN ANALYZE
SELECT id, title, source_name, published_at, 
       ts_rank(search_vector, websearch_to_tsquery('english', 'market crash')) as rank
FROM articles
WHERE search_vector @@ websearch_to_tsquery('english', 'market crash')
ORDER BY rank DESC, published_at DESC NULLS LAST, id DESC
LIMIT 51;
```

**Expected behavior:**
- `Bitmap Index Scan on ix_articles_search_vector`
- `Bitmap Heap Scan on articles`

## 2. Export Stress Test Procedures

### Memory Safety Check
Run the CSV export on a heavily populated database (e.g., 50k rows).
1. Initialize export: `curl -o test.csv "http://localhost:8000/articles/export/csv"`
2. While running, use `docker stats` to monitor the `finnews-backend` container.
3. **Pass Criteria:** Memory consumption must remain stable (flat-line) during the export process. It must not grow linearly with the export size.

### Maximum Limit Verification
Trigger an export exceeding the maximum allowed size by omitting filters on a large dataset:
```bash
curl -v "http://localhost:8000/articles/export/csv"
```
**Pass Criteria:** System returns an immediate `400 Bad Request` with message `Export too large (X rows). Maximum allowed is 10,000.` The database is not queried for data.

## 3. Streaming Chunk Extraction (Internal workings)
The API leverages SQL keyset pagination internally inside an `async generator`.
- The repository executes a `LIMIT 1000 + 1` query.
- It yields chunks of `1000` to the exporter.
- It captures the `published_at` and `id` (and optionally `rank`) of the 1000th item and feeds it back into the WHERE clause as the cursor for the next chunk.
- This creates an `O(1)` memory footprint in Python and stable sequential `Index Scan` reads in PostgreSQL.
