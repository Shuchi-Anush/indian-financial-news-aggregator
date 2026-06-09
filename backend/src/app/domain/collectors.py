"""Immutable domain entities and contracts for collectors.

Defines the interfaces and return types for all external data ingestion.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.domain.articles import RawArticle


@dataclass(frozen=True)
class SourceMetadata:
    """Metadata describing a data source (RSS, API, etc.)."""

    source_id: str
    name: str
    url: str
    source_type: str
    category: Optional[str] = None


@dataclass(frozen=True)
class CollectorResult:
    """Result of a collection attempt from a source."""

    source_id: str
    articles: tuple[RawArticle, ...]
    fetched_at: datetime
    error: Optional[str] = None
    is_success: bool = True


@dataclass(frozen=True)
class CollectorStatus:
    """Current status of a collector."""

    source_id: str
    last_fetched_at: Optional[datetime]
    is_active: bool
