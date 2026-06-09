"""Abstract base class for all asynchronous article collectors.

Provides the foundational contract and structured logging integration
for any source ingestion (RSS, API, scraping).
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone

import structlog

from app.domain.collectors import CollectorResult, SourceMetadata


class AsyncCollector(ABC):
    """Abstract base class for all asynchronous article collectors."""

    def __init__(self, metadata: SourceMetadata) -> None:
        self.metadata = metadata
        self.log = structlog.get_logger().bind(
            source_id=metadata.source_id, source_type=metadata.source_type
        )

    @property
    def source_id(self) -> str:
        """Get the unique identifier for the source."""
        return self.metadata.source_id

    @abstractmethod
    async def fetch_raw(self) -> CollectorResult:
        """
        Fetch raw articles from the source.

        Implementations must be async-safe, stateless, handle their own timeouts,
        and catch source-specific errors to return a failed CollectorResult
        rather than raising exceptions.
        """
        pass

    def _create_success_result(self, articles: tuple) -> CollectorResult:
        """Helper to consistently generate a successful CollectorResult."""
        return CollectorResult(
            source_id=self.source_id,
            articles=articles,
            fetched_at=datetime.now(timezone.utc),
            is_success=True,
        )

    def _create_error_result(self, error_msg: str) -> CollectorResult:
        """Helper to consistently log and generate a failed CollectorResult."""
        self.log.error("collector_fetch_failed", error=error_msg)
        return CollectorResult(
            source_id=self.source_id,
            articles=(),
            fetched_at=datetime.now(timezone.utc),
            error=error_msg,
            is_success=False,
        )
