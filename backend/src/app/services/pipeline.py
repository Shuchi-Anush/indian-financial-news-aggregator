"""Pipeline service orchestration.

Coordinates the data ingestion lifecycle without coupling directly to
the FastAPI application context, specific persistence mechanisms, or
collector implementations.
"""

import asyncio
from typing import AsyncContextManager, Protocol, Sequence

import structlog

from app.collectors.base import AsyncCollector
from app.core.metrics import registry
from app.domain.articles import CanonicalArticle, FailedArticle, RawArticle, EnrichedArticle
from app.domain.collectors import CollectorResult
from app.domain.deduplication import DedupCandidate
from app.domain.pipeline import PipelineRunResult, PipelineRunStatus
from app.enrichment.entities import EntityExtractor
from app.enrichment.keywords import KeywordExtractor
from app.enrichment.orchestrator import EnrichmentOrchestrator
from app.enrichment.sectors import SectorClassifier
from app.enrichment.sentiment import SentimentEngine
from app.enrichment.summaries import ExtractiveSummarizer
from app.processors.deduplicator import Deduplicator
from app.processors.normalizer import ArticleNormalizer
from app.processors.quality_gate import QualityGate

log = structlog.get_logger()


class PersistenceRepository(Protocol):
    """Protocol defining the required persistence contract for the pipeline."""

    async def get_active_sources(self) -> Sequence[dict]: ...

    async def get_recent_candidates(self) -> Sequence[DedupCandidate]: ...

    async def save_articles(self, articles: Sequence[CanonicalArticle], source_id: str) -> int: ...

    async def create_pipeline_run(self, trigger_type: str = "SCHEDULED") -> str: ...

    async def update_pipeline_run(self, run_id: str, result: PipelineRunResult) -> None: ...

    async def save_raw_articles(self, articles: Sequence[RawArticle], run_id: str) -> None: ...

    async def save_failed_articles(
        self, articles: Sequence[FailedArticle], run_id: str
    ) -> None: ...

    async def update_source_health(
        self, source_id: str, is_success: bool, error: str | None = None
    ) -> None: ...

    def source_lock(self, source_id: str) -> AsyncContextManager[bool]: ...

    async def refresh_analytics_views(self) -> None: ...


class IngestionPipeline:
    """
    Orchestrates the ingestion workflow:
    Collect -> Persist Raw -> Normalize -> Quality Gate -> Deduplicate -> Persist Canonical
    """

    def __init__(self, repository: PersistenceRepository) -> None:
        self.repository = repository
        self._enrichment_orchestrator = EnrichmentOrchestrator(
            processors=[
                EntityExtractor(),
                SectorClassifier(),
                SentimentEngine(),
                KeywordExtractor(),
                ExtractiveSummarizer(),
            ]
        )

    async def _fetch_with_concurrency(
        self, collectors: Sequence[AsyncCollector]
    ) -> list[tuple[str, CollectorResult | BaseException | None]]:
        from app.core.constants import DEFAULT_PIPELINE_CONCURRENCY

        semaphore = asyncio.Semaphore(DEFAULT_PIPELINE_CONCURRENCY)

        async def _bounded_fetch(
            collector: AsyncCollector,
        ) -> tuple[str, CollectorResult | BaseException | None]:
            async with semaphore:
                async with self.repository.source_lock(collector.source_id) as locked:
                    if not locked:
                        log.warning("source_lock_failed_skipping", source_id=collector.source_id)
                        return collector.source_id, None
                    try:
                        return collector.source_id, await collector.fetch_raw()
                    except Exception as e:
                        return collector.source_id, e

        fetch_tasks = [_bounded_fetch(collector) for collector in collectors]
        return await asyncio.gather(*fetch_tasks, return_exceptions=False)

    async def run(self, collectors: Sequence[AsyncCollector]) -> PipelineRunResult:
        """Execute the ingestion pipeline concurrently across provided collectors."""
        from datetime import datetime, timezone

        started_at = datetime.now(timezone.utc)
        run_id = await self.repository.create_pipeline_run()
        registry.inc("pipeline_runs_total")

        log.info("pipeline_started", run_id=run_id, collector_count=len(collectors))

        # 1. Fetch
        results = await self._fetch_with_concurrency(collectors)

        raw_articles: list[RawArticle] = []
        errors: list[str] = []
        failed_sources: list[str] = []

        # Analyze transport success and locks
        for source_id, collector_result in results:
            if collector_result is None:
                errors.append(f"Lock failed for {source_id}")
                failed_sources.append(source_id)
                registry.inc(
                    "source_health_failures_total",
                    labels={"source_slug": source_id, "error_type": "lock_failed"},
                )
                continue
            if isinstance(collector_result, BaseException):
                errors.append(f"Transport crash for {source_id}: {str(collector_result)}")
                failed_sources.append(source_id)
                registry.inc(
                    "source_health_failures_total",
                    labels={"source_slug": source_id, "error_type": "exception"},
                )
                await self.repository.update_source_health(source_id, False, str(collector_result))
                continue
            if not collector_result.is_success:
                error_msg = collector_result.error or "Unknown collector error"
                errors.append(error_msg)
                failed_sources.append(source_id)

                await self.repository.update_source_health(source_id, False, error_msg)
                registry.inc(
                    "source_health_failures_total",
                    labels={"source_slug": source_id, "error_type": "http_error"},
                )
                continue

            raw_articles.extend(collector_result.articles)
            if not collector_result.articles:
                # Zero article run
                await self.repository.update_source_health(source_id, False, "zero_articles")
            else:
                await self.repository.update_source_health(source_id, True)

        total_fetched = len(raw_articles)
        log.info("collection_completed", total_fetched=total_fetched, error_count=len(errors))
        registry.inc("articles_fetched_total", amount=total_fetched)

        # 1a. Persist Raw Payloads BEFORE Normalization
        if raw_articles:
            try:
                await self.repository.save_raw_articles(raw_articles, run_id)
            except Exception as e:
                log.error("raw_persistence_failed", error=str(e))

        # 2. Normalize and Quality Gate
        canonical_articles: list[CanonicalArticle] = []
        failed_articles: list[FailedArticle] = []
        normalized_counts: dict[str, int] = {}

        current_utc = datetime.now(timezone.utc)

        for raw in raw_articles:
            try:
                canonical = ArticleNormalizer.normalize(raw)
            except Exception as e:
                canonical = None
                failed_articles.append(
                    FailedArticle(
                        source_id=raw.source_id,
                        failure_stage="NORMALIZATION",
                        error_type="Exception",
                        error_message=str(e),
                        raw_payload=raw.raw_payload,
                    )
                )

            if canonical is None:
                if not any(f.raw_payload == raw.raw_payload for f in failed_articles):
                    failed_articles.append(
                        FailedArticle(
                            source_id=raw.source_id,
                            failure_stage="NORMALIZATION",
                            error_type="Drop",
                            error_message="Normalizer rejected article",
                            raw_payload=raw.raw_payload,
                        )
                    )
                registry.inc("normalization_errors_total", labels={"source_slug": raw.source_id})
                registry.inc(
                    "articles_failed_total",
                    labels={"source_slug": raw.source_id, "stage": "normalization"},
                )
                continue

            # 3. Quality Gate
            validation = QualityGate.validate(canonical, current_utc)
            if not validation.is_valid:
                failed_articles.append(
                    FailedArticle(
                        source_id=raw.source_id,
                        failure_stage="VALIDATION",
                        error_type="QualityGateRejected",
                        error_message=f"Violations: {', '.join(validation.violations)} (Score: {validation.quality_score})",
                        raw_payload=raw.raw_payload,
                    )
                )
                registry.inc(
                    "articles_failed_total",
                    labels={"source_slug": raw.source_id, "stage": "validation"},
                )
                continue

            # Update canonical score
            # We must use object.__setattr__ since it's frozen, or just recreate.
            canonical = CanonicalArticle(
                title=canonical.title,
                url=canonical.url,
                source_id=canonical.source_id,
                content_hash=canonical.content_hash,
                collected_at=canonical.collected_at,
                content=canonical.content,
                summary=canonical.summary,
                author=canonical.author,
                published_at=canonical.published_at,
                category=canonical.category,
                tags=canonical.tags,
                quality_score=validation.quality_score,
            )

            canonical_articles.append(canonical)
            normalized_counts[raw.source_id] = normalized_counts.get(raw.source_id, 0) + 1

        if failed_articles:
            try:
                await self.repository.save_failed_articles(failed_articles, run_id)
            except Exception as e:
                log.error("failed_articles_persistence_failed", error=str(e))

        # 4. Deduplicate
        existing_candidates = await self.repository.get_recent_candidates()
        deduplicator = Deduplicator(existing_candidates)

        unique_articles: list[CanonicalArticle] = []
        total_duplicates = 0

        for article in canonical_articles:
            dedup_result = deduplicator.check_duplicate(article)
            if dedup_result.is_duplicate:
                total_duplicates += 1
                registry.inc(
                    "articles_deduplicated_total", labels={"source_slug": article.source_id}
                )
            else:
                unique_articles.append(article)
                
        # 4b. Enrich ONLY the unique new articles
        enriched_articles: list[EnrichedArticle] = []
        for article in unique_articles:
            enriched = await self._enrichment_orchestrator.enrich(article)
            enriched_articles.append(enriched)

        # 5. Persist
        total_saved = 0
        if enriched_articles:
            articles_by_source: dict[str, list[EnrichedArticle]] = {}
            for article in enriched_articles:
                articles_by_source.setdefault(article.source_id, []).append(article)

            for source_id, group in articles_by_source.items():
                try:
                    inserted_count = await self.repository.save_articles(group, source_id)
                    total_saved += inserted_count
                    registry.inc(
                        "articles_ingested_total",
                        amount=inserted_count,
                        labels={"source_slug": source_id},
                    )
                except Exception as e:
                    log.error("persistence_failed", source=source_id, error=str(e))
                    errors.append(f"Persistence failed for {source_id}: {str(e)}")
                    failed_sources.append(source_id)

        status = PipelineRunStatus.SUCCESS
        # 5. Record Run Result
        end_utc = datetime.now(timezone.utc)
        duration_ms = int((end_utc - started_at).total_seconds() * 1000)

        if not errors and not failed_articles:
            status = PipelineRunStatus.SUCCESS
        elif len(normalized_counts) > 0:
            status = PipelineRunStatus.PARTIAL_SUCCESS
        else:
            status = PipelineRunStatus.FAILED

        error_summary = None
        if errors or failed_articles:
            err_texts = errors + [f"{f.failure_stage}: {f.error_type}" for f in failed_articles]
            error_summary = "; ".join(err_texts[:10])

        pipeline_result = PipelineRunResult(
            started_at=started_at,
            completed_at=end_utc,
            duration_ms=duration_ms,
            articles_ingested=sum(normalized_counts.values()),
            duplicates_detected=total_duplicates,
            failures=len(failed_articles) + len(errors),
            source_count=len(collectors),
            status=status,
            trigger_type="UNKNOWN", # Should be passed, but let db handle default or we overwrite
            error_summary=error_summary,
            failed_sources=failed_sources,
        )

        try:
            await self.repository.update_pipeline_run(run_id, pipeline_result)
        except Exception as e:
            log.error("pipeline_run_persistence_failed", error=str(e))

        fetch_duration = (datetime.now(timezone.utc) - started_at).total_seconds()
        registry.observe("pipeline_run_duration_seconds", fetch_duration)

        log.info(
            "pipeline_finished",
            status=pipeline_result.status.value,
            duration_sec=fetch_duration,
            total_fetched=total_fetched,
            total_saved=total_saved,
            total_duplicates=total_duplicates,
            failed_sources=pipeline_result.failed_sources,
        )
        try:
            await self.repository.refresh_analytics_views()
        except Exception as e:
            log.error("analytics_views_refresh_failed", error=str(e))

        return pipeline_result
