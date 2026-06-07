# Engineering Commands

Reusable commands for development, testing, and operations.

## Development

```bash
# Install dependencies (from backend/)
uv sync

# Run backend locally (from backend/)
uv run uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000

# Run with specific log level
LOG_LEVEL=DEBUG uv run uvicorn src.app.main:app --reload
```

## Docker

```bash
# Start full stack (PostgreSQL + backend)
docker compose up --build

# Start only PostgreSQL (for local backend dev)
docker compose up db

# Rebuild backend only
docker compose up --build backend

# View logs
docker compose logs -f backend
docker compose logs -f db

# Stop and remove volumes (reset DB)
docker compose down -v
```

## Database

```bash
# Connect to PostgreSQL in Docker
docker compose exec db psql -U postgres -d financial_news

# Quick article count
docker compose exec db psql -U postgres -d financial_news -c "SELECT COUNT(*) FROM articles;"

# Check feed sources
docker compose exec db psql -U postgres -d financial_news -c "SELECT name, is_active, last_fetched_at FROM feed_sources;"
```

## Testing

```bash
# Run all tests (from backend/)
uv run pytest tests/ -v

# Run with coverage
uv run pytest tests/ -v --cov=src/app

# Run specific test file
uv run pytest tests/test_normalizer.py -v

# Run tests matching a pattern
uv run pytest tests/ -k "test_dedup" -v
```

## Linting & Type Checking

```bash
# Lint (from backend/)
uv run ruff check src/

# Lint and fix
uv run ruff check src/ --fix

# Format
uv run ruff format src/

# Type check
uv run mypy src/app/
```

## API Testing (with curl)

```bash
# Health check
curl http://localhost:8000/health

# Trigger pipeline
curl -X POST http://localhost:8000/api/v1/pipeline/run

# List articles
curl "http://localhost:8000/api/v1/articles?page=1&page_size=10"

# Get article by ID
curl http://localhost:8000/api/v1/articles/{article_id}

# Export CSV
curl -X POST http://localhost:8000/api/v1/export/csv --output articles.csv

# Export Excel
curl -X POST http://localhost:8000/api/v1/export/excel --output articles.xlsx

# List feeds
curl http://localhost:8000/api/v1/feeds
```

## Seed Data

```bash
# Seed default Indian financial news feeds (from backend/)
uv run python scripts/seed_feeds.py
```
