"""Database-backed Prometheus-compatible metrics.

Computes exact operational metrics directly from the repository
to guarantee accuracy across isolated script runs and docker containers.
"""

from sqlalchemy import func, select

from app.db.session import get_session_factory
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
            func.sum(PipelineRun.articles_ingested),
            func.sum(PipelineRun.duplicates_detected),
            func.sum(PipelineRun.failures),
        )
        result_sums = await session.execute(stmt_sums)
        inserted_sum, dedup_sum, failures_sum = result_sums.one()
        lines.append(f"articles_ingested_total {inserted_sum or 0}")
        lines.append(f"articles_deduplicated_total {dedup_sum or 0}")
        lines.append(f"articles_failed_total {failures_sum or 0}")

        # Run durations
        stmt_duration = select(
            func.count(PipelineRun.id),
            func.sum(PipelineRun.duration_ms),
        ).where(PipelineRun.duration_ms > 0)
        result_duration = await session.execute(stmt_duration)
        duration_count, duration_sum_ms = result_duration.one()

        lines.append(f"pipeline_run_duration_seconds_count {duration_count or 0}")
        lines.append(f"pipeline_run_duration_seconds_sum {(duration_sum_ms or 0) / 1000.0}")

        # Source metrics
        from app.models.feed_source import FeedSource

        stmt_sources = select(FeedSource.circuit_breaker_state, func.count(FeedSource.id)).group_by(
            FeedSource.circuit_breaker_state
        )
        source_states = await session.execute(stmt_sources)
        for state, count in source_states:
            lines.append(f'source_circuit_breaker_state_total{{state="{state.value}"}} {count}')

    return "\n".join(lines) + "\n"


class NoOpRegistry:
    """Mock registry to prevent pipeline imports from breaking."""

    def inc(self, *args, **kwargs):
        pass

    def observe(self, *args, **kwargs):
        pass


registry = NoOpRegistry()
