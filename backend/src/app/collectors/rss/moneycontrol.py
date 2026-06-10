"""Moneycontrol Markets RSS Collector."""

import feedparser  # type: ignore[import-untyped]
import httpx
import structlog

from app.collectors.base import AsyncCollector
from app.core.constants import DEFAULT_RSS_TIMEOUT_SECONDS
from app.domain.articles import RawArticle
from app.domain.collectors import CollectorResult
from app.utils.url import normalize_url

log = structlog.get_logger()


class MoneycontrolRSSCollector(AsyncCollector):
    """
    Production-grade RSS collector for Moneycontrol feeds.
    """

    async def fetch_raw(self) -> CollectorResult:
        """Fetch and parse the RSS feed asynchronously."""
        try:
            async with httpx.AsyncClient(timeout=DEFAULT_RSS_TIMEOUT_SECONDS) as client:
                response = await client.get(self.metadata.url)
                response.raise_for_status()
                feed_content = response.text

        except httpx.TimeoutException as e:
            return self._create_error_result(f"Timeout fetching RSS feed: {str(e)}")
        except httpx.RequestError as e:
            return self._create_error_result(f"Request error fetching RSS feed: {str(e)}")
        except Exception as e:
            return self._create_error_result(f"Unexpected error fetching RSS feed: {str(e)}")

        # Parse RSS deterministically
        try:
            # feedparser handles malformed XML gracefully
            parsed_feed = feedparser.parse(feed_content)

            if parsed_feed.bozo and parsed_feed.entries == []:
                return self._create_error_result(
                    f"Failed to parse feed: {parsed_feed.bozo_exception}"
                )

            raw_articles = []
            for entry in parsed_feed.entries:
                try:
                    title = entry.get("title", "").strip()
                    link = entry.get("link", "").strip()

                    if not title or not link:
                        self.log.warning("skipping_malformed_entry", title=title, link=link)
                        continue

                    clean_url = normalize_url(link)

                    # feedparser provides 'published' or 'updated' string
                    published_at_raw = entry.get("published", entry.get("updated"))

                    summary = entry.get("summary", entry.get("description"))

                    # Optional author and category
                    author = entry.get("author")
                    category = None
                    if "tags" in entry and entry.tags:
                        category = entry.tags[0].get("term")

                    article = RawArticle(
                        title=title,
                        url=clean_url,
                        source_id=self.source_id,
                        timezone_hint=self.metadata.timezone_hint,
                        content=None,  # RSS typically only provides summary
                        summary=summary,
                        author=author,
                        published_at_raw=published_at_raw,
                        category=category,
                        tags=tuple(
                            tag.get("term") for tag in entry.get("tags", []) if tag.get("term")
                        ),
                    )
                    raw_articles.append(article)
                except Exception as e:
                    self.log.warning(
                        "error_processing_entry", entry_link=entry.get("link"), error=str(e)
                    )
                    continue

            return self._create_success_result(tuple(raw_articles))

        except Exception as e:
            return self._create_error_result(f"Error parsing RSS feed: {str(e)}")
