# Collector Template

Use this pattern when adding a new news source collector.

## File Location

- RSS feeds: `backend/src/app/collectors/rss/{source_name}.py`
- API sources: `backend/src/app/collectors/apis/{source_name}.py`

## Template

```python
"""Collector for {SourceName} financial news."""

import structlog
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.collectors import BaseCollector
from app.schemas.article import ArticleCreate

log = structlog.get_logger()


class SourceNameCollector(BaseCollector):
    """Collects articles from {SourceName}."""

    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    async def collect(self) -> list[ArticleCreate]:
        """Fetch and parse articles from {SourceName}."""
        articles: list[ArticleCreate] = []
        try:
            raw_data = await self._fetch()
            articles = self._parse(raw_data)
            log.info("collector_complete", source="{source_name}", count=len(articles))
        except Exception as exc:
            log.error("collector_failed", source="{source_name}", error=str(exc))
        return articles

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def _fetch(self) -> bytes:
        """Fetch raw content with retry."""
        response = await self.client.get(
            "https://...",
            timeout=30.0,
        )
        response.raise_for_status()
        return response.content

    def _parse(self, raw_data: bytes) -> list[ArticleCreate]:
        """Parse raw response into ArticleCreate DTOs."""
        # Implementation specific to source format
        return []
```

## Rules

1. **Always implement `BaseCollector`** with `async def collect() -> list[ArticleCreate]`
2. **Never write to the database** — return DTOs only
3. **Use tenacity for retries** — network calls are unreliable
4. **Log failures, don't raise** — one source failing must not crash the pipeline
5. **Use httpx.AsyncClient** — passed in from the pipeline service
6. **Return an empty list on total failure** — not None, not an exception

## Checklist

- [ ] Implements `BaseCollector` ABC
- [ ] Returns `list[ArticleCreate]`
- [ ] Uses `httpx.AsyncClient` (injected, not created)
- [ ] Has retry logic via tenacity
- [ ] Logs success count and failure details with structlog
- [ ] Handles all exceptions internally
