# Anti-Patterns

Patterns that have caused problems in similar projects or that violate this project's principles. Avoid these.

## Architecture Anti-Patterns

### ❌ Business Logic in Routes
```python
# BAD — route handler doing filtering, transformation, DB queries
@router.get("/articles")
async def list_articles(db: AsyncSession = Depends(get_db)):
    articles = await db.execute(select(Article).where(...))
    return [{"title": a.title.strip().upper()} for a in articles.scalars()]
```
```python
# GOOD — route delegates to service
@router.get("/articles")
async def list_articles(service: ArticleService = Depends(get_article_service)):
    return await service.get_articles(filters)
```

### ❌ Collectors Writing to Database
Collectors fetch and return data. They never import `db/` or call `session.add()`. Persistence is the pipeline service's responsibility.

### ❌ ORM Models in API Responses
Never return SQLAlchemy model instances from routes. Always map through Pydantic schemas with `from_attributes=True`.

## Code Anti-Patterns

### ❌ Synchronous I/O in Async Functions
```python
# BAD — requests is synchronous, blocks the event loop
import requests
async def fetch_feed(url):
    response = requests.get(url)  # BLOCKS
```
```python
# GOOD — httpx is async
async def fetch_feed(url):
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
```

### ❌ Bare Exception Handling
```python
# BAD
try:
    await fetch_feed(url)
except Exception:
    pass  # swallowed silently
```
```python
# GOOD
try:
    await fetch_feed(url)
except httpx.HTTPStatusError as exc:
    log.warning("feed_fetch_failed", url=url, status=exc.response.status_code)
except httpx.RequestError as exc:
    log.error("feed_fetch_error", url=url, error=str(exc))
```

### ❌ Unstructured Logging
```python
# BAD
log.info(f"Fetched {len(articles)} articles from {source}")

# GOOD
log.info("articles_fetched", count=len(articles), source=source)
```

### ❌ Pydantic v1 Syntax
```python
# BAD
class ArticleRead(BaseModel):
    class Config:
        orm_mode = True

# GOOD
class ArticleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
```

### ❌ SQLAlchemy 1.x Column Style
```python
# BAD
title = Column(String(512), nullable=False)

# GOOD
title: Mapped[str] = mapped_column(String(512))
```

## Process Anti-Patterns

### ❌ Premature Abstraction
Don't create `BaseExporter`, `BaseProcessor`, or plugin registries until you have 2+ concrete implementations that share real logic. Extract the abstraction after, not before.

### ❌ Speculative Features
Don't scaffold for WebSocket feeds, Kafka consumers, or ML pipelines. Build what's needed now. The implementation plan defines the scope.

### ❌ Empty Ceremony Files
Don't create files that contain only `pass` or a docstring. If a module isn't ready to implement, leave it for the sprint when it is.
