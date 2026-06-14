"""Base RSS Collector for Indian Financial News Aggregator."""

import asyncio
import random
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

    async def _fetch_with_retry(self, client: httpx.AsyncClient) -> httpx.Response:
        """Fetch URL with intelligent retry policies (TRANSIENT, RATE_LIMITED, PERMANENT)."""
        max_retries = 3
        base_delay = 2.0

        for attempt in range(max_retries + 1):
            try:
                response = await client.get(self.metadata.url)
                response.raise_for_status()
                return response
            except httpx.HTTPStatusError as e:
                status = e.response.status_code
                if status == 429:  # RATE_LIMITED
                    retry_after = e.response.headers.get("Retry-After")
                    delay = (
                        int(retry_after)
                        if retry_after and retry_after.isdigit()
                        else base_delay * (2**attempt)
                    )
                    self.log.warning("rate_limited", status=status, attempt=attempt, delay=delay)
                elif status in (500, 502, 503, 504):  # TRANSIENT
                    delay = base_delay * (2**attempt) + random.uniform(0, 1)
                    self.log.warning(
                        "transient_http_error", status=status, attempt=attempt, delay=delay
                    )
                else:
                    # PERMANENT
                    raise e
            except (httpx.TimeoutException, httpx.ConnectError) as e:
                # TRANSIENT
                delay = base_delay * (2**attempt) + random.uniform(0, 1)
                self.log.warning(
                    "transient_connection_error", error=str(e), attempt=attempt, delay=delay
                )

            if attempt == max_retries:
                raise Exception(f"Max retries exceeded fetching {self.metadata.url}")

            await asyncio.sleep(delay)
        raise Exception("Unreachable")

    async def fetch_raw(self) -> CollectorResult:
        """Fetch and parse the RSS feed asynchronously."""
        try:
            headers = {"User-Agent": self._get_user_agent()}
            async with httpx.AsyncClient(
                timeout=DEFAULT_RSS_TIMEOUT_SECONDS, headers=headers, follow_redirects=True
            ) as client:
                response = await self._fetch_with_retry(client)
                feed_content = response.text

        except httpx.HTTPStatusError as e:
            self._record_failure("http_status_error")
            return self._create_error_result(f"Permanent HTTP error: {e.response.status_code}")
        except httpx.TimeoutException as e:
            self._record_failure("timeout")
            return self._create_error_result(f"Fetch timeout: {str(e)}")
        except Exception as e:
            self._record_failure("unknown_fetch_error")
            return self._create_error_result(f"Fetch failed: {str(e)}")

        try:
            # Prevent feedparser from hanging on giant payloads by limiting processing time?
            # Feedparser is synchronous. If payload is massive, it might block. 
            # We already rely on httpx timeout, but we should also catch bozo accurately.
            parsed_feed = feedparser.parse(feed_content)

            if parsed_feed.bozo and not parsed_feed.entries:
                self._record_failure("malformed_xml")
                return self._create_error_result(
                    f"Failed to parse feed: {getattr(parsed_feed, 'bozo_exception', 'Unknown')}"
                )

            raw_articles = []
            for entry in parsed_feed.entries:
                article = self._map_entry(entry)
                if article:
                    raw_articles.append(article)

            from app.core.metrics import ARTICLES_FETCHED_TOTAL
            ARTICLES_FETCHED_TOTAL.inc(len(raw_articles))

            self.log.info("collector_fetch_success", articles_count=len(raw_articles))
            return self._create_success_result(tuple(raw_articles))

        except Exception as e:
            self._record_failure("xml_parsing_exception")
            return self._create_error_result(f"Error parsing RSS feed: {str(e)}")

    def _record_failure(self, error_type: str) -> None:
        """Helper to increment Prometheus failure metrics."""
        from app.core.metrics import SOURCE_HEALTH_FAILURES_TOTAL
        SOURCE_HEALTH_FAILURES_TOTAL.labels(
            source_slug=self.source_id,
            error_type=error_type
        ).inc()

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
