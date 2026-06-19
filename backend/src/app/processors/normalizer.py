"""Pure processor for transforming raw articles into canonical articles.

Ensures deterministic formatting of fields without side-effects or I/O.
"""

import html
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse, urlunparse

import structlog
from bs4 import BeautifulSoup

from app.domain.articles import CanonicalArticle, RawArticle
from app.processors.hashing import compute_content_hash
from app.utils.date_parser import parse_article_date

log = structlog.get_logger()


class ArticleNormalizer:
    """Pure processor for transforming raw articles into canonical articles."""

    @staticmethod
    def normalize(article: RawArticle) -> CanonicalArticle | None:
        """
        Convert a RawArticle to a CanonicalArticle.
        Operations are deterministic, side-effect free, and perform no I/O.

        Returns None if normalization fails (e.g. empty title, invalid URL),
        logging a structured warning instead of raising an exception.
        """
        try:
            clean_url = ArticleNormalizer._normalize_url(article.url)
            clean_title = ArticleNormalizer._normalize_whitespace(article.title)

            if not clean_title or not clean_url:
                log.warning("normalization_skipped_empty_fields", url=article.url)
                return None

            clean_title = clean_title[:512]

            clean_content = (
                ArticleNormalizer._normalize_text(article.content) if article.content else None
            )
            clean_summary = (
                ArticleNormalizer._normalize_text(article.summary) if article.summary else None
            )

            pub_date = parse_article_date(article.published_at_raw, article.timezone_hint)

            # Freshness filter
            if pub_date:
                from app.core.constants import MAX_ARTICLE_AGE_HOURS

                age = datetime.now(timezone.utc) - pub_date
                if age > timedelta(hours=MAX_ARTICLE_AGE_HOURS):
                    log.info(
                        "article_rejected_stale",
                        url=article.url,
                        age_hours=age.total_seconds() / 3600,
                    )
                    return None

            content_hash = compute_content_hash(clean_title, clean_summary)

            return CanonicalArticle(
                title=clean_title,
                url=clean_url,
                source_id=article.source_id,
                source_name=article.source_name,
                content_hash=content_hash,
                content=clean_content,
                summary=clean_summary,
                author=article.author.strip()[:256] if article.author else None,
                published_at=pub_date,
                collected_at=datetime.now(timezone.utc),
                category=article.category,
                tags=article.tags,
            )
        except Exception as e:
            log.warning("normalization_unexpected_failure", url=article.url, error=str(e))
            return None

    @staticmethod
    def _normalize_whitespace(text: str) -> str:
        """Remove excessive whitespace and strip."""
        if not text:
            return ""
        # Basic whitespace cleanup for title
        text = html.unescape(text)
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def _normalize_text(text: str) -> str:
        """Safely strip HTML, decode entities, and normalize whitespace."""
        if not text:
            return ""
        # Parse HTML safely
        soup = BeautifulSoup(text, "html.parser")
        
        # Remove script and style tags completely so their contents don't bleed into text
        for script_or_style in soup(["script", "style", "noscript"]):
            script_or_style.decompose()

        # Extract text (which decodes entities and drops tags)
        raw_text = soup.get_text(separator=" ")
        # Clean whitespace
        return re.sub(r"\s+", " ", raw_text).strip()

    @staticmethod
    def _normalize_url(url: str) -> str:
        """Normalize URL by removing fragments."""
        try:
            parsed = urlparse(url)
            return urlunparse(
                (parsed.scheme, parsed.netloc, parsed.path, parsed.params, parsed.query, "")
            )
        except ValueError:
            return url.strip()
