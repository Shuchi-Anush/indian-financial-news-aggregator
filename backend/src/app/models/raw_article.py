"""RawArticle ORM model — raw payload storage system-of-record."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, String, text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.feed_source import FeedSource
    from app.models.pipeline_run import PipelineRun


class ProcessingStatus(enum.Enum):
    PENDING = "pending"
    NORMALIZED = "normalized"
    FAILED = "failed"


class RawArticle(TimestampMixin, Base):
    """Immutable raw payload storage system-of-record."""

    __tablename__ = "raw_articles"
    __table_args__ = (Index("ix_raw_articles_source_status", "source_id", "processing_status"),)

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    pipeline_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("pipeline_runs.id"))
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("feed_sources.id"))
    external_id: Mapped[str | None] = mapped_column(String(512), nullable=True)
    source_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    fetched_at_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    published_at_raw: Mapped[str | None] = mapped_column(String(256), nullable=True)
    raw_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    transport_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    processing_status: Mapped[ProcessingStatus] = mapped_column(
        SAEnum(ProcessingStatus, native_enum=False, create_constraint=False, length=32),
        nullable=False,
        default=ProcessingStatus.PENDING,
    )
    normalization_attempts: Mapped[int] = mapped_column(nullable=False, default=0)

    # Relationships
    source: Mapped["FeedSource"] = relationship()
    pipeline_run: Mapped["PipelineRun"] = relationship()
