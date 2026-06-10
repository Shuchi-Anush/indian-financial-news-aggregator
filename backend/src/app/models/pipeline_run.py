"""PipelineRun ORM model for operational tracking."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, JSON, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin
from app.domain.pipeline import PipelineRunStatus


class PipelineRun(TimestampMixin, Base):
    """Operational persistence for an ingestion run."""

    __tablename__ = "pipeline_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[PipelineRunStatus] = mapped_column(
        SAEnum(PipelineRunStatus, native_enum=False, create_constraint=False, length=32),
        nullable=False,
    )
    inserted_count: Mapped[int] = mapped_column(nullable=False, default=0)
    duplicate_count: Mapped[int] = mapped_column(nullable=False, default=0)
    failed_sources: Mapped[list[str]] = mapped_column(JSON, nullable=False, server_default="[]")
    errors: Mapped[list[str]] = mapped_column(JSON, nullable=False, server_default="[]")
