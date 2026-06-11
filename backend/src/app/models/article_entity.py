"""Article entity extraction model.

Maps an article to a deterministic financial entity (Company, Index, Currency, etc).
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Index, String, text, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.article import Article


class ArticleEntity(TimestampMixin, Base):
    """Extracted financial entity from an article."""

    __tablename__ = "article_entities"
    __table_args__ = (
        Index("ix_article_entities_article_id", "article_id"),
        Index("ix_article_entities_entity", "entity"),
        Index("ix_article_entities_type", "entity_type"),
        Index(
            "uq_article_entities_article_entity_type",
            "article_id",
            "entity",
            "entity_type",
            unique=True,
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    article_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("articles.id", ondelete="CASCADE"), nullable=False
    )
    entity: Mapped[str] = mapped_column(String(255), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, server_default="1.0")
    extractor_version: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")

    article: Mapped[Article] = relationship("Article", back_populates="entities")
