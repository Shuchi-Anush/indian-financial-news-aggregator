# Backend Conventions

## Route Handler Pattern

```python
router = APIRouter(prefix="/articles", tags=["articles"])

@router.get("", response_model=PaginatedResponse[ArticleRead])
async def list_articles(
    filters: Annotated[ArticleFilter, Query()],
    service: Annotated[ArticleService, Depends(get_article_service)],
):
    """List articles with filtering and pagination."""
    return await service.get_articles(filters)
```

Rules:
- Router per domain (articles, feeds, pipeline, export)
- All routers mounted under `/api/v1/` via the v1 router in `api/__init__.py`
- Response models always declared via `response_model=`
- Dependencies via `Annotated[Type, Depends()]`
- Docstrings on every route (used by OpenAPI)

## Service Pattern

```python
class ArticleService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.log = structlog.get_logger().bind(service="article")

    async def get_articles(self, filters: ArticleFilter) -> PaginatedResponse[ArticleRead]:
        query = select(Article)
        # apply filters...
        result = await self.db.execute(query)
        return PaginatedResponse(items=result.scalars().all(), total=total)
```

Rules:
- One service class per domain
- DB session injected via constructor
- Logger bound with service name
- Returns Pydantic schemas, never ORM objects directly

## Collector Pattern

```python
class RSSCollector(BaseCollector):
    def __init__(self, client: httpx.AsyncClient, feeds: list[FeedSource]):
        self.client = client
        self.feeds = feeds

    async def collect(self) -> list[ArticleCreate]:
        tasks = [self._fetch_feed(feed) for feed in self.feeds]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        # flatten successes, log failures
        return articles
```

Rules:
- Implements `BaseCollector` ABC
- Returns `list[ArticleCreate]` — never writes to DB
- Uses `asyncio.gather` with `return_exceptions=True`
- Logs and skips failures per-feed

## Dependency Injection Pattern

```python
# In api/dependencies.py or inline
async def get_article_service(db: Annotated[AsyncSession, Depends(get_db)]) -> ArticleService:
    return ArticleService(db)
```

## Configuration Access

```python
from app.core.config import get_settings

settings = get_settings()  # cached via @lru_cache
database_url = settings.database_url
```

## File Organization Rules

- One model per file in `models/` (e.g., `article.py`, `feed_source.py`)
- One schema module per domain in `schemas/` (e.g., `article.py`, `feed.py`)
- One service per domain in `services/`
- One route module per domain in `api/routes/`
- Shared utilities in `utils/`, but prefer co-location over extraction
