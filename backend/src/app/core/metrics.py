"""Database-backed Prometheus-compatible metrics.

Computes exact operational metrics directly from the repository
to guarantee accuracy across isolated script runs and docker containers.
"""

from sqlalchemy import func, select

from app.db.session import get_session_factory
from app.models.failed_article import FailedArticle
from app.models.pipeline_run import PipelineRun


async def export_metrics() -> str:
    """Dynamically compute metrics from the database."""
    session_factory = get_session_factory()
    lines = []

    async with session_factory() as session:
        # Pipeline runs
        stmt_runs = select(func.count(PipelineRun.id))
        runs_count = await session.scalar(stmt_runs) or 0
        lines.append(f"pipeline_runs_total {runs_count}")

        # Ingested and deduplicated
        stmt_sums = select(
            func.sum(PipelineRun.inserted_count), func.sum(PipelineRun.duplicate_count)
        )
        result_sums = await session.execute(stmt_sums)
        inserted_sum, dedup_sum = result_sums.one()
        lines.append(f"articles_ingested_total {inserted_sum or 0}")
        lines.append(f"articles_deduplicated_total {dedup_sum or 0}")

        # Failed articles
        stmt_failed = select(func.count(FailedArticle.id))
        failed_count = await session.scalar(stmt_failed) or 0
        lines.append(f"articles_failed_total {failed_count}")

        # Run durations
        stmt_duration = select(
            func.count(PipelineRun.id),
            func.sum(func.extract("epoch", PipelineRun.completed_at - PipelineRun.started_at)),
        ).where(PipelineRun.completed_at.is_not(None))
        result_duration = await session.execute(stmt_duration)
        duration_count, duration_sum = result_duration.one()

        lines.append(f"pipeline_run_duration_seconds_count {duration_count or 0}")
        lines.append(f"pipeline_run_duration_seconds_sum {duration_sum or 0.0}")

    return "\n".join(lines) + "\n"


class NoOpRegistry:
    """Mock registry to prevent pipeline imports from breaking."""

    def inc(self, *args, **kwargs):
        pass

    def observe(self, *args, **kwargs):
        pass


registry = NoOpRegistry()
