# Docker Workflow

## Full Stack

```bash
# Build and start everything
docker compose up --build

# Detached mode
docker compose up --build -d

# Stop everything
docker compose down

# Stop and destroy data (reset DB)
docker compose down -v
```

## Selective Services

```bash
# Database only (for local backend dev)
docker compose up db

# Backend only (assumes DB is already running)
docker compose up backend --build
```

## Logs

```bash
# All services
docker compose logs -f

# Backend only
docker compose logs -f backend

# Database only
docker compose logs -f db

# Last 100 lines
docker compose logs --tail=100 backend
```

## Rebuild

```bash
# Rebuild backend without cache (after dependency changes)
docker compose build --no-cache backend

# Rebuild and restart
docker compose up --build backend
```

## Database Access

```bash
# Interactive psql session
docker compose exec db psql -U postgres -d financial_news

# Run a single query
docker compose exec db psql -U postgres -d financial_news -c "SELECT COUNT(*) FROM articles;"

# Dump database
docker compose exec db pg_dump -U postgres financial_news > backup.sql

# Restore database
cat backup.sql | docker compose exec -T db psql -U postgres financial_news
```

## Container Inspection

```bash
# List running containers
docker compose ps

# Shell into backend container
docker compose exec backend bash

# Shell into db container
docker compose exec db sh

# Check container resource usage
docker stats finnews-backend finnews-db
```

## Volume Management

```bash
# List volumes
docker volume ls | grep finnews

# Inspect volume
docker volume inspect indian-financial-news-aggregator_postgres_data

# Remove all project volumes (destroys data!)
docker compose down -v
```
