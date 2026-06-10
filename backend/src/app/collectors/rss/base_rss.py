"""Base RSS Collector for Indian Financial News Aggregator."""

from typing import Any, Optional

import feedparser  # type: ignore[import-untyped]
import httpx

from app.collectors.base import AsyncCollector
from app.core.constants import DEFAULT_RSS_TIMEOUT_SECONDS
from app.domain.articles import RawArticle
from app.domain.collectors import CollectorResult
from app.utils.url import normalize_url


class BaseRSSCollector(AsyncCollector):
    """
    Shared production-grade RSS collector logic.
    Handles httpx lifecycle, timeout, parsing, and error mapping.
    """

    def _get_user_agent(self) -> str:
        """Return a standardized User-Agent to prevent 403 blocks."""
        return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    async def fetch_raw(self) -> CollectorResult:
        """Fetch and parse the RSS feed asynchronously."""
        try:
            headers = {"User-Agent": self._get_user_agent()}
            async with httpx.AsyncClient(
                timeout=DEFAULT_RSS_TIMEOUT_SECONDS, headers=headers, follow_redirects=True
            ) as client:
                response = await client.get(self.metadata.url)
                response.raise_for_status()
                feed_content = response.text

        except httpx.TimeoutException as e:
            return self._create_error_result(f"Timeout fetching RSS feed: {str(e)}")
        except httpx.RequestError as e:
            return self._create_error_result(f"Request error fetching RSS feed: {str(e)}")
        except Exception as e:
            return self._create_error_result(f"Unexpected error fetching RSS feed: {str(e)}")

        try:
            parsed_feed = feedparser.parse(feed_content)

            if parsed_feed.bozo and not parsed_feed.entries:
                return self._create_error_result(
                    f"Failed to parse feed: {getattr(parsed_feed, 'bozo_exception', 'Unknown')}"
                )

            raw_articles = []
            for entry in parsed_feed.entries:
                article = self._map_entry(entry)
                if article:
                    raw_articles.append(article)

            self.log.info("collector_fetch_success", articles_count=len(raw_articles))
            return self._create_success_result(tuple(raw_articles))

        except Exception as e:
            return self._create_error_result(f"Error parsing RSS feed: {str(e)}")

    def _map_entry(self, entry: Any) -> Optional[RawArticle]:
        """
        Map a feedparser entry to a RawArticle.
        Override in subclasses if custom source-specific mapping is needed.
        """
        try:
            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()

            if not title or not link:
                self.log.warning("skipping_malformed_entry", title=title, link=link)
                return None

            clean_url = normalize_url(link)
            published_at_raw = entry.get("published", entry.get("updated"))

            summary = entry.get("summary", entry.get("description"))

            author = entry.get("author")
            category = None
            if "tags" in entry and entry.tags:
                category = entry.tags[0].get("term")

            return RawArticle(
                title=title,
                url=clean_url,
                source_id=self.source_id,
                timezone_hint=self.metadata.timezone_hint,
                content=None,
                summary=summary,
                author=author,
                published_at_raw=published_at_raw,
                category=category,
                tags=tuple(tag.get("term") for tag in entry.get("tags", []) if tag.get("term")),
                raw_payload=dict(entry),
            )
        except Exception as e:
            self.log.warning("error_processing_entry", entry_link=entry.get("link"), error=str(e))
            return None
