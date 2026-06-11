from typing import Any, Sequence

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pipeline_run import PipelineRun


class PipelineRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_runs(
        self, limit: int, cursor_data: dict[str, Any] | None = None
    ) -> Sequence[PipelineRun]:
        """Fetch pipeline runs with keyset pagination."""
        stmt = select(PipelineRun).order_by(PipelineRun.started_at.desc(), PipelineRun.id.desc())

        if cursor_data:
            c_pub = cursor_data["published_at"]  # We map started_at to published_at in cursor
            c_id = cursor_data["id"]
            if c_pub:
                stmt = stmt.where(
                    or_(
                        PipelineRun.started_at < c_pub,
                        and_(PipelineRun.started_at == c_pub, PipelineRun.id < c_id),
                    )
                )

        stmt = stmt.limit(limit + 1)
        result = await self.session.execute(stmt)
        return result.scalars().all()
