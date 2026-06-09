"""Pure processor for transforming raw articles into canonical articles.

Ensures deterministic formatting of fields without side-effects or I/O.
"""

import re
from datetime import datetime, timezone
from urllib.parse import urlparse, urlunparse

from app.domain.articles import CanonicalArticle, RawArticle
from app.processors.hashing import compute_content_hash


class ArticleNormalizer:
    """Pure processor for transforming raw articles into canonical articles."""

    @staticmethod
    def normalize(article: RawArticle) -> CanonicalArticle:
        """
        Convert a RawArticle to a CanonicalArticle.
        Operations are deterministic, side-effect free, and perform no I/O.
        """
        clean_url = ArticleNormalizer._normalize_url(article.url)
        clean_title = ArticleNormalizer._normalize_whitespace(article.title)
        clean_content = (
            ArticleNormalizer._normalize_whitespace(article.content) if article.content else None
        )
        clean_summary = (
            ArticleNormalizer._normalize_whitespace(article.summary) if article.summary else None
        )

        pub_date = article.published_at
        if pub_date and pub_date.tzinfo is None:
            pub_date = pub_date.replace(tzinfo=timezone.utc)

        content_hash = compute_content_hash(clean_title, clean_url)

        return CanonicalArticle(
            title=clean_title,
            url=clean_url,
            source_id=article.source_id,
            content_hash=content_hash,
            content=clean_content,
            summary=clean_summary,
            author=article.author.strip() if article.author else None,
            published_at=pub_date,
            collected_at=datetime.now(timezone.utc),
            category=article.category,
            tags=article.tags,
        )

    @staticmethod
    def _normalize_whitespace(text: str) -> str:
        """Remove excessive whitespace and strip."""
        if not text:
            return ""
        return re.sub(r"\s+", " ", text).strip()

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
