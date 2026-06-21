"""SQLAlchemy implementation of the persistence repository."""

import uuid
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.domain.articles import CanonicalArticle, FailedArticle, RawArticle
from app.domain.deduplication import DedupCandidate
from app.domain.pipeline import PipelineRunResult
from app.models.article import Article
from app.services.pipeline import PersistenceRepository


class IngestionRepository(PersistenceRepository):
    """Production-grade ingestion persistence."""

    def __init__(self, session_factory: async_sessionmaker) -> None:
        self.session_factory = session_factory

    async def get_active_sources(self) -> Sequence[dict]:
        """Fetch all active feed sources."""
        async with self.session_factory() as session:
            from sqlalchemy import select

            from app.models.feed_source import FeedSource

            stmt = select(FeedSource).where(FeedSource.is_active.is_(True))
            result = await session.execute(stmt)
            sources = result.scalars().all()
            return [
                {
                    "id": str(s.id),
                    "slug": s.slug,
                    "name": s.name,
                    "url": s.url,
                    "source_type": s.source_type,
                    "timezone_hint": s.timezone_hint,
                    "circuit_breaker_state": s.circuit_breaker_state,
                    "health_score": s.health_score,
                }
                for s in sources
            ]

    async def get_existing_candidates(self, urls: list[str], hashes: list[str]) -> Sequence[DedupCandidate]:
        """Fetch matching candidates to run deduplication against."""
        if not urls and not hashes:
            return []
            
        async with self.session_factory() as session:
            from sqlalchemy import or_
            
            conditions = []
            if urls:
                conditions.append(Article.url.in_(urls))
            if hashes:
                conditions.append(Article.content_hash.in_(hashes))
                
            stmt = select(Article.url, Article.content_hash).where(or_(*conditions))
            result = await session.execute(stmt)
            return [DedupCandidate(url=row.url, content_hash=row.content_hash) for row in result]

    async def save_articles(self, articles: Sequence[CanonicalArticle], source_id: str) -> int:
        if not articles:
            return 0

        from app.domain.articles import EnrichedArticle
        from app.models.article_entity import ArticleEntity
        from app.models.article_sector import ArticleSector
        from app.models.article_keyword import ArticleKeyword

        values = []
        for a in articles:
            val = {
                "title": a.title,
                "url": a.url,
                "feed_source_id": uuid.UUID(a.source_id) if a.source_id else None,
                "source_name": a.source_name,
                "content_hash": a.content_hash,
                "summary": a.summary,
                "body": a.content,
                "author": a.author,
                "published_at": a.published_at,
                "quality_score": getattr(a, "quality_score", None),
            }
            if isinstance(a, EnrichedArticle):
                val["sentiment_label"] = a.sentiment_label
                val["sentiment_score"] = a.sentiment_score
                val["generated_summary"] = a.generated_summary
            values.append(val)

        stmt = insert(Article).values(values).on_conflict_do_nothing(index_elements=["url"]).returning(Article.id, Article.url)

        async with self.session_factory() as session:
            async with session.begin():
                result = await session.execute(stmt)
                inserted_rows = result.fetchall()
                
                if inserted_rows:
                    url_to_id = {row.url: row.id for row in inserted_rows}
                    
                    entity_values = []
                    sector_values = []
                    keyword_values = []
                    
                    for a in articles:
                        if isinstance(a, EnrichedArticle) and a.url in url_to_id:
                            article_id = url_to_id[a.url]
                            for ent in a.entities:
                                entity_values.append({
                                    "article_id": article_id,
                                    "entity": ent.entity[:255],
                                    "entity_type": ent.entity_type[:50],
                                    "confidence": ent.confidence,
                                    "extractor_version": ent.extractor_version
                                })
                            for sec in a.sectors:
                                sector_values.append({
                                    "article_id": article_id,
                                    "sector": sec.sector[:100],
                                    "score": sec.score
                                })
                            for kw in a.keywords:
                                keyword_values.append({
                                    "article_id": article_id,
                                    "keyword": kw.keyword[:100],
                                    "weight": kw.weight
                                })
                    
                    if entity_values:
                        estmt = insert(ArticleEntity).values(entity_values).on_conflict_do_nothing(index_elements=['article_id', 'entity', 'entity_type'])
                        await session.execute(estmt)
                    if sector_values:
                        sstmt = insert(ArticleSector).values(sector_values).on_conflict_do_nothing(index_elements=['article_id', 'sector'])
                        await session.execute(sstmt)
                    if keyword_values:
                        kstmt = insert(ArticleKeyword).values(keyword_values).on_conflict_do_nothing(index_elements=['article_id', 'keyword'])
                        await session.execute(kstmt)
                        
                return len(inserted_rows)

    async def refresh_analytics_views(self) -> None:
        """Refresh the materialized views for analytics.
        
        This executes a CONCURRENTLY refresh if the view is already populated
        with a unique index. For the first time (or if standard refresh is needed),
        we do a blocking refresh. But SQLAlchemy allows executing the raw SQL.
        """
        from datetime import datetime, timezone
        from app.core.metrics import registry

        start = datetime.now(timezone.utc)
        async with self.session_factory() as session:
            async with session.begin():
                # We use regular REFRESH without CONCURRENTLY since it's simpler
                # and we don't have high read concurrency requirements on MV yet.
                await session.execute(text("REFRESH MATERIALIZED VIEW hourly_trends_mv"))
                await session.execute(text("REFRESH MATERIALIZED VIEW sentiment_summaries_mv"))

        duration = (datetime.now(timezone.utc) - start).total_seconds()
        registry.observe("analytics_views_refresh_duration_seconds", duration)

    async def save_run_result(self, result: PipelineRunResult) -> None:
        pass  # Replaced by update_pipeline_run

    async def create_pipeline_run(self, trigger_type: str = "SCHEDULED") -> str:
        """Create a new pipeline run."""
        async with self.session_factory() as session:
            from datetime import datetime, timezone

            from app.domain.pipeline import PipelineRunStatus
            from app.models.pipeline_run import PipelineRun

            async with session.begin():
                run = PipelineRun(
                    started_at=datetime.now(timezone.utc),
                    status=PipelineRunStatus.RUNNING,
                    trigger_type=trigger_type,
                )
                session.add(run)
                await session.flush()
                return str(run.id)

    async def update_pipeline_run(self, run_id: str, result: PipelineRunResult) -> None:
        """Update existing pipeline run with result."""
        async with self.session_factory() as session:
            from sqlalchemy import update

            from app.models.pipeline_run import PipelineRun

            async with session.begin():
                stmt = (
                    update(PipelineRun)
                    .where(PipelineRun.id == uuid.UUID(run_id))
                    .values(
                        completed_at=result.completed_at,
                        duration_ms=result.duration_ms,
                        articles_ingested=result.articles_ingested,
                        duplicates_detected=result.duplicates_detected,
                        failures=result.failures,
                        source_count=result.source_count,
                        status=result.status,
                        error_summary=result.error_summary,
                        failed_sources=result.failed_sources or [],
                    )
                )
                await session.execute(stmt)

    async def save_raw_articles(self, articles: Sequence[RawArticle], run_id: str) -> None:
        """Persist raw articles as system-of-record."""
        if not articles:
            return

        from datetime import datetime, timezone

        from app.models.raw_article import RawArticle as RawArticleModel

        values = []
        for a in articles:
            values.append(
                {
                    "pipeline_run_id": uuid.UUID(run_id),
                    "source_id": uuid.UUID(a.source_id),
                    "source_url": a.url,
                    "fetched_at_utc": datetime.now(timezone.utc),
                    "published_at_raw": a.published_at_raw,
                    "raw_payload": a.raw_payload or {},
                }
            )

        async with self.session_factory() as session:
            async with session.begin():
                await session.execute(insert(RawArticleModel).values(values))

    async def save_failed_articles(self, articles: Sequence[FailedArticle], run_id: str) -> None:
        """Persist dead letter articles."""
        if not articles:
            return

        from app.models.failed_article import FailedArticle as FailedArticleModel

        values = []
        for a in articles:
            values.append(
                {
                    "pipeline_run_id": uuid.UUID(run_id),
                    "source_id": uuid.UUID(a.source_id),
                    "failure_stage": a.failure_stage,
                    "error_type": a.error_type[:256] if a.error_type else "UNKNOWN",
                    "error_message": a.error_message,
                    "traceback": a.traceback,
                    "raw_payload": a.raw_payload,
                }
            )

        async with self.session_factory() as session:
            async with session.begin():
                await session.execute(insert(FailedArticleModel).values(values))

    async def update_source_health(
        self, source_id: str, is_success: bool, error: str | None = None
    ) -> None:
        """Update health indicators and circuit breaker state on the source."""
        async with self.session_factory() as session:
            from datetime import datetime, timezone

            from sqlalchemy import select

            from app.models.feed_source import CircuitBreakerState, FeedSource

            now = datetime.now(timezone.utc)

            async with session.begin():
                result = await session.execute(
                    select(FeedSource).where(FeedSource.id == uuid.UUID(source_id))
                )
                source = result.scalar_one_or_none()
                if not source:
                    return

                if is_success:
                    source.circuit_breaker_state = CircuitBreakerState.CLOSED
                    source.consecutive_failures = 0
                    source.success_count += 1
                    source.last_success_at = now
                    source.last_error = None
                else:
                    source.consecutive_failures += 1
                    source.failure_count += 1
                    source.last_failure_at = now
                    source.last_error = error
                    if source.consecutive_failures >= 5:
                        source.circuit_breaker_state = CircuitBreakerState.OPEN
                    elif source.circuit_breaker_state == CircuitBreakerState.HALF_OPEN:
                        source.circuit_breaker_state = CircuitBreakerState.OPEN

                total = source.success_count + source.failure_count
                source.health_score = (source.success_count / total * 100.0) if total > 0 else 100.0

    @asynccontextmanager
    async def source_lock(self, source_id: str) -> AsyncIterator[bool]:
        """Acquire a per-source Postgres advisory lock bounded to the session lifecycle."""
        import hashlib

        from sqlalchemy import text

        lock_id = int(hashlib.md5(source_id.encode()).hexdigest()[:15], 16)

        async with self.session_factory() as session:
            locked = False
            try:
                stmt = text("SELECT pg_try_advisory_lock(:id)")
                result = await session.execute(stmt, {"id": lock_id})
                locked = result.scalar() is True
                yield locked
            finally:
                if locked:
                    stmt = text("SELECT pg_advisory_unlock(:id)")
                    await session.execute(stmt, {"id": lock_id})
                    await session.commit()

    @asynccontextmanager
    async def global_advisory_lock(self, lock_name: str) -> AsyncIterator[bool]:
        """Acquire a global Postgres advisory lock to ensure single-pipeline execution across containers."""
        import hashlib
        from sqlalchemy import text

        lock_id = int(hashlib.md5(lock_name.encode()).hexdigest()[:15], 16)

        async with self.session_factory() as session:
            locked = False
            try:
                stmt = text("SELECT pg_try_advisory_lock(:id)")
                result = await session.execute(stmt, {"id": lock_id})
                locked = result.scalar() is True
                yield locked
            finally:
                if locked:
                    stmt = text("SELECT pg_advisory_unlock(:id)")
                    await session.execute(stmt, {"id": lock_id})
                    await session.commit()
