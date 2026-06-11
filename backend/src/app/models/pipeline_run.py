"""PipelineRun ORM model for operational tracking."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, String, Text, text
from sqlalchemy import Enum as SAEnum
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
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[int] = mapped_column(nullable=False, default=0)
    articles_ingested: Mapped[int] = mapped_column(nullable=False, default=0)
    duplicates_detected: Mapped[int] = mapped_column(nullable=False, default=0)
    failures: Mapped[int] = mapped_column(nullable=False, default=0)
    source_count: Mapped[int] = mapped_column(nullable=False, default=0)
    status: Mapped[PipelineRunStatus] = mapped_column(
        SAEnum(PipelineRunStatus, native_enum=False, create_constraint=False, length=32),
        nullable=False,
        default=PipelineRunStatus.RUNNING,
    )
    trigger_type: Mapped[str] = mapped_column(String(64), nullable=False, server_default="MANUAL")
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    failed_sources: Mapped[list[str]] = mapped_column(JSON, nullable=False, server_default="[]")
