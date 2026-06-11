import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.article import ArticleCategory, SentimentLabel


class ArticleListItem(BaseModel):
    """Lightweight projection of an article for listing pages."""

    id: uuid.UUID
    title: str
    url: str
    author: str | None = None
    source_name: str | None = None
    image_url: str | None = None
    published_at: datetime | None = None
    category: ArticleCategory | None = None
    sentiment: SentimentLabel | None = None

    model_config = ConfigDict(from_attributes=True)


class ArticleDetail(ArticleListItem):
    """Full detail of an article including summary and body."""

    summary: str | None = None
    body: str | None = None
    content_hash: str
    quality_score: float | None = None
    feed_source_id: uuid.UUID | None = None


class ArticleFilters(BaseModel):
    """Filters available for querying articles."""

    source_names: list[str] | None = Field(default=None, alias="source")
    published_after: datetime | None = Field(default=None, alias="date_from")
    published_before: datetime | None = Field(default=None, alias="date_to")
    keywords: str | None = None
    search: str | None = Field(default=None, alias="q")
    entity: str | None = Field(default=None, description="Exact entity match from enrichment")
    sector: str | None = Field(default=None, description="Exact sector match from enrichment")
    extracted_keyword: str | None = Field(default=None, description="Exact keyword match from enrichment")
    sentiment: str | None = Field(default=None, description="POSITIVE, NEGATIVE, or NEUTRAL")

    @model_validator(mode="after")
    def validate_dates(self) -> "ArticleFilters":
        if self.published_after and self.published_before:
            if self.published_after > self.published_before:
                raise ValueError("published_after cannot be greater than published_before")
        return self

    @model_validator(mode="after")
    def validate_search(self) -> "ArticleFilters":
        if self.search is not None:
            self.search = self.search.strip()
            if not self.search or len(self.search) < 3:
                raise ValueError("Search query must be at least 3 characters long")
        if self.keywords is not None:
            self.keywords = self.keywords.strip()
            if not self.keywords:
                self.keywords = None
        return self
