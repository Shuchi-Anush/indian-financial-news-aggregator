"""Pipeline service orchestration.

Coordinates the data ingestion lifecycle without coupling directly to
the FastAPI application context, specific persistence mechanisms, or
collector implementations.
"""

import asyncio
from typing import Protocol, Sequence

import structlog

from app.collectors.base import AsyncCollector
from app.domain.articles import CanonicalArticle, RawArticle
from app.domain.collectors import CollectorResult
from app.domain.deduplication import DedupCandidate
from app.domain.pipeline import PipelineRunResult, PipelineRunStatus
from app.processors.deduplicator import Deduplicator
from app.processors.normalizer import ArticleNormalizer

log = structlog.get_logger()


class PersistenceRepository(Protocol):
    """Protocol defining the required persistence contract for the pipeline."""

    async def get_recent_candidates(self) -> Sequence[DedupCandidate]:
        """Fetch candidates to run deduplication against."""
        ...

    async def save_articles(self, articles: Sequence[CanonicalArticle], source_id: str) -> int:
        """
        Persist fully processed canonical articles.
        MUST execute within a per-source transaction boundary.
        MUST implement ON CONFLICT DO NOTHING for content_hash/url.
        Returns the number of rows actually inserted.
        """
        ...

    async def save_run_result(self, result: PipelineRunResult) -> None:
        """Persist the result of a pipeline run."""
        ...


class IngestionPipeline:
    """
    Orchestrates the ingestion workflow:
    Collect -> Normalize -> Deduplicate -> Persist
    """

    def __init__(self, repository: PersistenceRepository) -> None:
        self.repository = repository

    async def _fetch_with_concurrency(
        self, collectors: Sequence[AsyncCollector]
    ) -> list[CollectorResult | BaseException]:
        """
        Isolate gather orchestration for future bounded concurrency (e.g. asyncio.Semaphore).
        """
        from app.core.constants import DEFAULT_PIPELINE_CONCURRENCY

        semaphore = asyncio.Semaphore(DEFAULT_PIPELINE_CONCURRENCY)

        async def _bounded_fetch(collector: AsyncCollector) -> CollectorResult:
            async with semaphore:
                return await collector.fetch_raw()

        fetch_tasks = [_bounded_fetch(collector) for collector in collectors]
        # noinspection PyTypeChecker
        return await asyncio.gather(*fetch_tasks, return_exceptions=True)

    async def run(self, collectors: Sequence[AsyncCollector]) -> PipelineRunResult:
        """
        Execute the ingestion pipeline concurrently across provided collectors.
        """
        from datetime import datetime, timezone

        started_at = datetime.now(timezone.utc)

        log.info("pipeline_started", collector_count=len(collectors))

        # 1. Fetch
        results = await self._fetch_with_concurrency(collectors)

        raw_articles: list[RawArticle] = []
        errors: list[str] = []
        failed_sources: list[str] = []

        for result in results:
            if isinstance(result, BaseException):
                errors.append(str(result))
                continue
            if not result.is_success:
                errors.append(result.error or "Unknown collector error")
                failed_sources.append(result.source_id)
                continue
            raw_articles.extend(result.articles)

        total_fetched = len(raw_articles)
        log.info("collection_completed", total_fetched=total_fetched, error_count=len(errors))

        if not raw_articles:
            return PipelineRunResult(
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
                status=PipelineRunStatus.FAILED if errors else PipelineRunStatus.COMPLETED,
                inserted_count=0,
                duplicate_count=0,
                failed_sources=tuple(failed_sources),
                errors=tuple(errors),
            )

        # 2. Normalize
        canonical_articles: list[CanonicalArticle] = []
        for raw in raw_articles:
            canonical = ArticleNormalizer.normalize(raw)
            if canonical is not None:
                canonical_articles.append(canonical)

        # 3. Deduplicate
        existing_candidates = await self.repository.get_recent_candidates()
        deduplicator = Deduplicator(existing_candidates)

        unique_articles: list[CanonicalArticle] = []
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
            # Group by source for per-feed transaction boundaries
            articles_by_source: dict[str, list[CanonicalArticle]] = {}
            for article in unique_articles:
                articles_by_source.setdefault(article.source_id, []).append(article)

            for source_id, group in articles_by_source.items():
                try:
                    inserted_count = await self.repository.save_articles(group, source_id)
                    total_saved += inserted_count
                    log.info("persistence_completed", source=source_id, saved_count=inserted_count)
                except Exception as e:
                    log.error("persistence_failed", source=source_id, error=str(e))
                    errors.append(f"Persistence failed for {source_id}: {str(e)}")
                    failed_sources.append(source_id)

        status = PipelineRunStatus.COMPLETED
        if errors:
            status = (
                PipelineRunStatus.FAILED
                if total_saved == 0 and total_fetched > 0
                else PipelineRunStatus.PARTIAL_SUCCESS
            )

        result_summary = PipelineRunResult(
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
            status=status,
            inserted_count=total_saved,
            duplicate_count=total_duplicates,
            failed_sources=tuple(set(failed_sources)),
            errors=tuple(errors),
        )

        try:
            await self.repository.save_run_result(result_summary)
        except Exception as e:
            log.error("pipeline_run_persistence_failed", error=str(e))

        log.info("pipeline_finished", summary=result_summary.__dict__)
        return result_summary
