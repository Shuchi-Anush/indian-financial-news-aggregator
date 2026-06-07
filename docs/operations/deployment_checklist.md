# Deployment Checklist

Pre-deployment checklist for deploying the system to a new host.

## Prerequisites

- [ ] Docker and Docker Compose installed on host
- [ ] Git installed
- [ ] Sufficient disk space for PostgreSQL data volume
- [ ] Port 8000 (backend) and 5432 (DB) available

## Deployment Steps

### 1. Clone Repository

```bash
git clone <repo-url>
cd indian-financial-news-aggregator
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env`:
- [ ] Set `APP_ENV=production`
- [ ] Set `LOG_LEVEL=WARNING`
- [ ] Set a strong `POSTGRES_PASSWORD` (not the default `postgres`)
- [ ] Set `POSTGRES_HOST=db` (Docker internal networking)
- [ ] Optionally set API keys for NewsData.io / GNews

### 3. Build and Start

```bash
docker compose up --build -d
```

### 4. Verify Health

```bash
curl http://localhost:8000/health
# Expected: {"status": "ok"}
```

### 5. Seed Feed Sources

```bash
docker compose exec backend uv run python scripts/seed_feeds.py
```

### 6. Trigger First Pipeline Run

```bash
curl -X POST http://localhost:8000/api/v1/pipeline/run
```

### 7. Verify Data

```bash
curl http://localhost:8000/api/v1/articles
# Expected: paginated list of articles
```

### 8. (Optional) Set Up Cron for Automated Collection

```bash
# Run pipeline every 30 minutes
crontab -e
*/30 * * * * curl -s -X POST http://localhost:8000/api/v1/pipeline/run >> /var/log/finnews-pipeline.log 2>&1
```

## Post-Deployment Verification

- [ ] `/health` returns `200`
- [ ] Pipeline run completes without errors
- [ ] Articles appear in `GET /api/v1/articles`
- [ ] CSV export downloads successfully
- [ ] Structured JSON logs visible in `docker compose logs backend`
- [ ] PostgreSQL data persists across `docker compose restart`

## Rollback

```bash
# Stop current deployment
docker compose down

# Revert to previous version
git checkout <previous-tag>

# Rebuild
docker compose up --build -d
```

Database data is preserved in the `postgres_data` volume unless you explicitly `docker compose down -v`.
