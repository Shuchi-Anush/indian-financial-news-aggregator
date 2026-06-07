# Database Design

## Engine Configuration

- **Driver:** asyncpg (async PostgreSQL)
- **Pool:** SQLAlchemy async engine with default pool settings
- **Schema management:** `create_all()` during development, Alembic when schema stabilizes (ADR-002)

## Tables

### `articles`

Primary data store for collected news articles.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | `UUID` | PK, default `gen_random_uuid()` | |
| `title` | `VARCHAR(512)` | NOT NULL | Cleaned title |
| `url` | `VARCHAR(2048)` | NOT NULL, UNIQUE | Canonical article URL |
| `source_feed` | `VARCHAR(256)` | NOT NULL | Feed name (e.g., "economic-times-markets") |
| `author` | `VARCHAR(256)` | NULLABLE | Article author if available |
| `summary` | `TEXT` | NULLABLE | Cleaned snippet/description |
| `content` | `TEXT` | NULLABLE | Full article text if available |
| `published_at` | `TIMESTAMPTZ` | NULLABLE | Original publish date (UTC) |
| `collected_at` | `TIMESTAMPTZ` | NOT NULL, default `now()` | When we fetched it |
| `category` | `VARCHAR(128)` | NULLABLE | e.g., "Markets", "Economy", "Banking" |
| `tags` | `VARCHAR[]` | NULLABLE | PostgreSQL array of tags |
| `content_hash` | `VARCHAR(64)` | NOT NULL | SHA-256 of normalized(title + url) |
| `is_duplicate` | `BOOLEAN` | NOT NULL, default `false` | Flagged by deduplicator |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, default `now()` | Row creation time |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL, auto-update | Row modification time |

**Indexes:**
- `ix_articles_url` — UNIQUE on `url` (dedup + lookup)
- `ix_articles_content_hash` — on `content_hash` (dedup)
- `ix_articles_published_at` — on `published_at` (date range queries)
- `ix_articles_source_feed` — on `source_feed` (filter by source)
- `ix_articles_category` — on `category` (filter by category)

### `feed_sources`

Configuration table for RSS feeds and API sources.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | `UUID` | PK, default `gen_random_uuid()` | |
| `name` | `VARCHAR(256)` | NOT NULL | Human-readable name |
| `url` | `VARCHAR(2048)` | NOT NULL, UNIQUE | Feed/API URL |
| `source_type` | `VARCHAR(32)` | NOT NULL | `rss` or `api` |
| `category` | `VARCHAR(128)` | NULLABLE | Default category for articles from this feed |
| `is_active` | `BOOLEAN` | NOT NULL, default `true` | Enable/disable collection |
| `last_fetched_at` | `TIMESTAMPTZ` | NULLABLE | Last successful fetch time |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, default `now()` | Row creation time |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL, auto-update | Row modification time |

**Indexes:**
- `ix_feed_sources_url` — UNIQUE on `url`
- `ix_feed_sources_is_active` — on `is_active` (active feed queries)

## Relationships

No foreign keys between `articles` and `feed_sources` in the initial design. The `source_feed` column in `articles` is a denormalized string identifier. This keeps the pipeline simple — collectors don't need to resolve FeedSource IDs.

**Rationale:** Adding a FK relationship is a Phase 2 refinement once the pipeline is stable. The current design optimizes for simplicity and insertion speed.

## Mixins

### TimestampMixin

Applied to all models:

```python
class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
```

## Query Patterns

### Paginated article listing
```sql
SELECT * FROM articles
WHERE is_duplicate = false
  AND published_at BETWEEN :start AND :end
  AND source_feed = :source
ORDER BY published_at DESC
LIMIT :page_size OFFSET :offset
```

### Dedup check (batch)
```sql
SELECT url, content_hash FROM articles
WHERE url = ANY(:urls) OR content_hash = ANY(:hashes)
```

### Fuzzy dedup window
```sql
SELECT id, title FROM articles
WHERE published_at >= now() - interval '7 days'
```
