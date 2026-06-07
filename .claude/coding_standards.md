# Coding Standards

## Python Version & Style

- **Python 3.11+** — use modern syntax (`str | None`, `match/case` where appropriate)
- **Line length**: 100 characters (configured in `pyproject.toml` via ruff)
- **Formatter/Linter**: `ruff` for both formatting and linting
- **Type checker**: `mypy` with strict mode as a target

## Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Modules | `snake_case` | `article_service.py` |
| Classes | `PascalCase` | `ArticleService` |
| Functions | `snake_case` | `get_articles()` |
| Constants | `UPPER_SNAKE` | `DEFAULT_PAGE_SIZE` |
| Pydantic models | `PascalCase` with suffix | `ArticleCreate`, `ArticleRead` |
| ORM models | `PascalCase` (singular) | `Article`, `FeedSource` |
| Route paths | `kebab-case` | `/api/v1/feed-sources` |
| Env vars | `UPPER_SNAKE` | `POSTGRES_HOST` |

## Imports

Order (ruff enforces this):
1. Standard library
2. Third-party packages
3. Local application imports

```python
import hashlib
from datetime import datetime, timezone

import httpx
import structlog
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.schemas.article import ArticleRead
```

## Async Patterns

```python
# ✅ Correct: async function with async DB session
async def get_articles(db: AsyncSession, filters: ArticleFilter) -> list[Article]:
    result = await db.execute(select(Article).where(...))
    return list(result.scalars().all())

# ❌ Wrong: synchronous DB call inside async function
def get_articles(db: Session) -> list[Article]:
    return db.query(Article).all()
```

## Logging

Use `structlog` bound loggers. Always include structured context.

```python
import structlog

log = structlog.get_logger()

# ✅ Good: structured key-value pairs
log.info("pipeline_run_complete", articles_collected=42, duplicates=7, source="rss")

# ❌ Bad: unstructured f-string
log.info(f"Collected {count} articles from {source}")
```

## Error Handling

```python
from app.core.exceptions import CollectorError

# ✅ Domain exceptions with context
raise CollectorError(
    message="RSS feed fetch failed",
    source="economic-times-markets",
    details={"status_code": 503, "url": feed_url},
)

# ❌ Bare exceptions
raise Exception("something went wrong")
```

## Pydantic Models

```python
from pydantic import BaseModel, ConfigDict

class ArticleRead(BaseModel):
    """Article response DTO."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    url: str
    published_at: datetime | None
```

## SQLAlchemy Models

```python
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base, TimestampMixin

class Article(TimestampMixin, Base):
    __tablename__ = "articles"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    title: Mapped[str] = mapped_column(String(512))
    url: Mapped[str] = mapped_column(String(2048), unique=True)
    summary: Mapped[str | None] = mapped_column(Text)
```

## Testing

- Use `pytest` with `pytest-asyncio`
- Async test mode set to `auto` in `pyproject.toml`
- Test files: `tests/test_<module>.py`
- Fixtures in `tests/conftest.py`
- Mock external HTTP with `httpx` mock transports, not `unittest.mock.patch`
