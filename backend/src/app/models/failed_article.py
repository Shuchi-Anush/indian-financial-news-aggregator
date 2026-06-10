"""FailedArticle ORM model — dead letter system."""

from __future__ import annotations

import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum as SAEnum, ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.feed_source import FeedSource
    from app.models.pipeline_run import PipelineRun
    from app.models.raw_article import RawArticle


class FailureStage(enum.Enum):
    COLLECTION = "collection"
    NORMALIZATION = "normalization"
    VALIDATION = "validation"
    PERSISTENCE = "persistence"


class FailedArticle(TimestampMixin, Base):
    """Dead letter queue for failed ingestion operations."""

    __tablename__ = "failed_articles"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    raw_article_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("raw_articles.id"), nullable=True
    )
    pipeline_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("pipeline_runs.id"))
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("feed_sources.id"))

    failure_stage: Mapped[FailureStage] = mapped_column(
        SAEnum(FailureStage, native_enum=False, create_constraint=False, length=32),
        nullable=False,
    )
    error_type: Mapped[str] = mapped_column(String(256), nullable=False)
    error_message: Mapped[str] = mapped_column(Text, nullable=False)
    traceback: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    replayed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Relationships
    source: Mapped["FeedSource"] = relationship()
    pipeline_run: Mapped["PipelineRun"] = relationship()
    raw_article: Mapped["RawArticle | None"] = relationship()
