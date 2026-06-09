"""Pipeline service orchestration.

Coordinates the data ingestion lifecycle without coupling directly to
the FastAPI application context, specific persistence mechanisms, or
collector implementations.
"""

import asyncio
from dataclasses import dataclass
from typing import Protocol, Sequence

import structlog

from app.collectors.base import AsyncCollector
from app.domain.articles import CanonicalArticle, RawArticle
from app.domain.deduplication import DedupCandidate
from app.processors.deduplicator import Deduplicator
from app.processors.normalizer import ArticleNormalizer

log = structlog.get_logger()


class PersistenceRepository(Protocol):
    """Protocol defining the required persistence contract for the pipeline."""

    async def get_recent_candidates(self) -> Sequence[DedupCandidate]:
        """Fetch candidates to run deduplication against."""
        ...

    async def save_articles(self, articles: Sequence[CanonicalArticle]) -> None:
        """Persist fully processed canonical articles."""
        ...


@dataclass(frozen=True)
class PipelineSummary:
    """Summary of a pipeline execution run."""

    total_fetched: int
    total_normalized: int
    total_duplicates: int
    total_saved: int
    errors: tuple[str, ...]


class IngestionPipeline:
    """
    Orchestrates the ingestion workflow:
    Collect -> Normalize -> Deduplicate -> Persist
    """

    def __init__(self, repository: PersistenceRepository) -> None:
        self.repository = repository

    async def run(self, collectors: Sequence[AsyncCollector]) -> PipelineSummary:
        """
        Execute the ingestion pipeline concurrently across provided collectors.
        """
        log.info("pipeline_started", collector_count=len(collectors))

        # 1. Fetch
        fetch_tasks = [collector.fetch_raw() for collector in collectors]
        results = await asyncio.gather(*fetch_tasks, return_exceptions=True)

        raw_articles: list[RawArticle] = []
        errors: list[str] = []

        for result in results:
            if isinstance(result, BaseException):
                errors.append(str(result))
                continue
            if not result.is_success:
                errors.append(result.error or "Unknown collector error")
                continue
            raw_articles.extend(result.articles)

        total_fetched = len(raw_articles)
        log.info("collection_completed", total_fetched=total_fetched, error_count=len(errors))

        if not raw_articles:
            return PipelineSummary(0, 0, 0, 0, tuple(errors))

        # 2. Normalize
        canonical_articles = []
        for raw in raw_articles:
            try:
                canonical = ArticleNormalizer.normalize(raw)
                canonical_articles.append(canonical)
            except Exception as e:
                log.warning("normalization_failed", url=raw.url, error=str(e))
                errors.append(f"Normalization failed for {raw.url}")

        total_normalized = len(canonical_articles)

        # 3. Deduplicate
        existing_candidates = await self.repository.get_recent_candidates()
        deduplicator = Deduplicator(existing_candidates)

        unique_articles = []
        total_duplicates = 0

        for article in canonical_articles:
            dedup_result = deduplicator.check_duplicate(article)
            if dedup_result.is_duplicate:
                total_duplicates += 1
            else:
                unique_articles.append(article)

        # 4. Persist
        total_saved = 0
        if unique_articles:
            try:
                await self.repository.save_articles(unique_articles)
                total_saved = len(unique_articles)
                log.info("persistence_completed", saved_count=total_saved)
            except Exception as e:
                log.error("persistence_failed", error=str(e))
                errors.append(f"Persistence failed: {str(e)}")

        summary = PipelineSummary(
            total_fetched=total_fetched,
            total_normalized=total_normalized,
            total_duplicates=total_duplicates,
            total_saved=total_saved,
            errors=tuple(errors),
        )

        log.info("pipeline_finished", summary=summary.__dict__)
        return summary
