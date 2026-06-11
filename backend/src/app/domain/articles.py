"""Immutable domain entities representing news articles.

Defines the core article models used throughout the application. These models
are free of any framework-specific or ORM dependencies.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional


@dataclass(frozen=True)
class FailedArticle:
    """Immutable representation of a failed processing item."""

    source_id: str
    failure_stage: str
    error_type: str
    error_message: str
    raw_payload: dict[str, Any] | None = None
    traceback: str | None = None


@dataclass(frozen=True)
class RawArticle:
    """Immutable representation of an article exactly as fetched from a source.

    Fields may be missing or unnormalized, directly reflecting what was collected.
    Normalizer owns all timestamp interpretation.
    """

    title: str
    url: str
    source_id: str
    timezone_hint: str = "UTC"
    content: Optional[str] = None
    summary: Optional[str] = None
    author: Optional[str] = None
    published_at_raw: Optional[str] = None
    category: Optional[str] = None
    tags: tuple[str, ...] = ()
    raw_payload: dict[str, Any] | None = None


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
    quality_score: Optional[float] = None

    @property
    def is_complete(self) -> bool:
        """Evaluate whether essential metadata is present."""
        return bool(self.title and self.url and self.published_at)


@dataclass(frozen=True)
class EntityExtraction:
    entity: str
    entity_type: str
    confidence: float
    extractor_version: int


@dataclass(frozen=True)
class SectorClassification:
    sector: str
    score: float


@dataclass(frozen=True)
class KeywordExtraction:
    keyword: str
    weight: float


@dataclass(frozen=True)
class EnrichedArticle(CanonicalArticle):
    """Immutable representation of an enriched article ready for persistence."""

    entities: tuple[EntityExtraction, ...] = ()
    sectors: tuple[SectorClassification, ...] = ()
    keywords: tuple[KeywordExtraction, ...] = ()
    sentiment_label: Optional[str] = None
    sentiment_score: Optional[float] = None
    generated_summary: Optional[str] = None
