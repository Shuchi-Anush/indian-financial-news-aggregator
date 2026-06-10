"""SQLAlchemy implementation of the persistence repository."""

import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.domain.articles import CanonicalArticle
from app.domain.deduplication import DedupCandidate
from app.domain.pipeline import PipelineRunResult
from app.models.article import Article
from app.models.pipeline_run import PipelineRun
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
        """
        Persist fully processed canonical articles.
        MUST execute within a per-source transaction boundary.
        MUST implement ON CONFLICT DO NOTHING for identity fields.
        Returns the number of rows actually inserted.
        """
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
                }
            )

        stmt = insert(Article).values(values)
        stmt = stmt.on_conflict_do_nothing(index_elements=["url"])

        async with self.session_factory() as session:
            async with session.begin():
                result = await session.execute(stmt)
                return result.rowcount

    async def save_run_result(self, result: PipelineRunResult) -> None:
        """Persist the result of a pipeline run for operational monitoring."""
        async with self.session_factory() as session:
            async with session.begin():
                pipeline_run = PipelineRun(
                    started_at=result.started_at,
                    completed_at=result.completed_at,
                    status=result.status,
                    inserted_count=result.inserted_count,
                    duplicate_count=result.duplicate_count,
                    failed_sources=list(result.failed_sources),
                    errors=list(result.errors),
                )
                session.add(pipeline_run)
