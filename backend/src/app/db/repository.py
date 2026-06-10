"""SQLAlchemy implementation of the persistence repository."""

import uuid
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager

from sqlalchemy import select
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

    async def get_recent_candidates(self) -> Sequence[DedupCandidate]:
        """Fetch candidates to run deduplication against."""
        async with self.session_factory() as session:
            stmt = select(Article.url, Article.content_hash).limit(100000)
            result = await session.execute(stmt)
            return [DedupCandidate(url=row.url, content_hash=row.content_hash) for row in result]

    async def save_articles(self, articles: Sequence[CanonicalArticle], source_id: str) -> int:
        if not articles:
            return 0

        values = []
        for a in articles:
            values.append(
                {
                    "title": a.title,
                    "url": a.url,
                    "feed_source_id": uuid.UUID(a.source_id) if a.source_id else None,
                    "content_hash": a.content_hash,
                    "summary": a.summary,
                    "body": a.content,
                    "author": a.author,
                    "published_at": a.published_at,
                    "quality_score": getattr(a, "quality_score", None),
                }
            )

        stmt = insert(Article).values(values)
        stmt = stmt.on_conflict_do_nothing(index_elements=["url"])

        async with self.session_factory() as session:
            async with session.begin():
                result = await session.execute(stmt)
                return result.rowcount

    async def save_run_result(self, result: PipelineRunResult) -> None:
        pass  # Replaced by update_pipeline_run

    async def create_pipeline_run(self) -> str:
        """Create a new pipeline run."""
        async with self.session_factory() as session:
            from datetime import datetime, timezone
            from app.models.pipeline_run import PipelineRun, PipelineRunStatus

            async with session.begin():
                run = PipelineRun(
                    started_at=datetime.now(timezone.utc),
                    completed_at=datetime.now(timezone.utc),
                    status=PipelineRunStatus.RUNNING,
                    inserted_count=0,
                    duplicate_count=0,
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
                        status=result.status,
                        inserted_count=result.inserted_count,
                        duplicate_count=result.duplicate_count,
                        failed_sources=list(result.failed_sources),
                        errors=list(result.errors),
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
        self, source_id: str, status: str, consecutive_failures: int, error: str | None = None
    ) -> None:
        """Update health indicators on the source."""
        async with self.session_factory() as session:
            from datetime import datetime, timezone
            from sqlalchemy import update
            from app.models.feed_source import FeedSource

            now = datetime.now(timezone.utc)
            values = {
                "health_status": status,
                "consecutive_failures": consecutive_failures,
                "error_type": error,
            }
            if status == "HEALTHY":
                values["last_success_at"] = now
            else:
                values["last_failed_at"] = now

            async with session.begin():
                stmt = (
                    update(FeedSource).where(FeedSource.id == uuid.UUID(source_id)).values(**values)
                )
                await session.execute(stmt)

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
