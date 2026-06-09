"""Immutable domain entities representing news articles.

Defines the core article models used throughout the application. These models
are free of any framework-specific or ORM dependencies.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class RawArticle:
    """Immutable representation of an article exactly as fetched from a source.

    Fields may be missing or unnormalized, directly reflecting what was collected.
    """

    title: str
    url: str
    source_id: str
    content: Optional[str] = None
    summary: Optional[str] = None
    author: Optional[str] = None
    published_at: Optional[datetime] = None
    category: Optional[str] = None
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class CanonicalArticle:
    """Immutable representation of a normalized, canonical article.

    Ready for deduplication and persistence. Contains stable content hashes
    and normalized data structures.
    """

    title: str
    url: str
    source_id: str
    content_hash: str
    collected_at: datetime
    content: Optional[str] = None
    summary: Optional[str] = None
    author: Optional[str] = None
    published_at: Optional[datetime] = None
    category: Optional[str] = None
    tags: tuple[str, ...] = ()

    @property
    def is_complete(self) -> bool:
        """Evaluate whether essential metadata is present."""
        return bool(self.title and self.url and self.published_at)
