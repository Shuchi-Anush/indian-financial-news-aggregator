# API Contracts

## Base URL

```
http://localhost:8000/api/v1
```

## Common Patterns

### Pagination

All list endpoints support pagination:

```
?page=1&page_size=20
```

Response wrapper:
```json
{
  "items": [...],
  "total": 142,
  "page": 1,
  "page_size": 20
}
```

### Error Responses

All errors return structured JSON:

```json
{
  "error": "not_found",
  "message": "Article not found",
  "details": {"article_id": "550e8400-..."}
}
```

HTTP status codes:
- `400` — validation error (bad input)
- `404` — entity not found
- `422` — Pydantic validation failure (FastAPI default)
- `500` — internal server error

### Timestamps

All timestamps are ISO 8601 in UTC:
```
"2026-06-07T10:30:00Z"
```

### UUIDs

All entity IDs are UUID v4:
```
"550e8400-e29b-41d4-a716-446655440000"
```

---

## Endpoints

### Health

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Application health check |

**Response:** `200 OK`
```json
{"status": "ok"}
```

---

### Articles

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/articles` | List articles (filtered, paginated) |
| `GET` | `/api/v1/articles/{id}` | Get single article |
| `GET` | `/api/v1/articles/stats` | Aggregated statistics |

#### `GET /api/v1/articles`

Query parameters:
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `page` | int | 1 | Page number |
| `page_size` | int | 20 | Items per page (max 100) |
| `source` | string | — | Filter by source feed name |
| `category` | string | — | Filter by category |
| `start_date` | date | — | Published after this date |
| `end_date` | date | — | Published before this date |
| `search` | string | — | Search in title/summary |

**Response:** `200 OK`
```json
{
  "items": [
    {
      "id": "uuid",
      "title": "Sensex rises 500 points...",
      "url": "https://...",
      "source_feed": "economic-times-markets",
      "author": "ET Bureau",
      "summary": "The BSE Sensex...",
      "published_at": "2026-06-07T10:30:00Z",
      "collected_at": "2026-06-07T10:35:00Z",
      "category": "Markets",
      "tags": ["sensex", "nifty"]
    }
  ],
  "total": 142,
  "page": 1,
  "page_size": 20
}
```

---

### Feed Sources

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/feeds` | List configured feeds |
| `POST` | `/api/v1/feeds` | Add new feed source |
| `PATCH` | `/api/v1/feeds/{id}` | Update feed source |
| `DELETE` | `/api/v1/feeds/{id}` | Remove feed source |

#### `POST /api/v1/feeds`

**Request body:**
```json
{
  "name": "Economic Times - Markets",
  "url": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
  "source_type": "rss",
  "category": "Markets"
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "name": "Economic Times - Markets",
  "url": "https://...",
  "source_type": "rss",
  "category": "Markets",
  "is_active": true,
  "last_fetched_at": null
}
```

---

### Pipeline

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/pipeline/run` | Trigger a pipeline run |

**Response:** `200 OK`
```json
{
  "feeds_processed": 8,
  "articles_collected": 156,
  "articles_normalized": 152,
  "duplicates_found": 89,
  "articles_inserted": 63,
  "errors": ["livemint-markets: HTTP 403"],
  "duration_seconds": 12.4
}
```

---

### Export

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/export/csv` | Export articles as CSV |
| `POST` | `/api/v1/export/excel` | Export articles as Excel |

**Request body** (same filters as article listing):
```json
{
  "source": "economic-times-markets",
  "start_date": "2026-06-01",
  "end_date": "2026-06-07"
}
```

**Response:** File download (`Content-Disposition: attachment`)

- CSV: `text/csv`
- Excel: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
