"""ORM models package — re-exports all model classes.

Import models here so that ``Base.metadata`` is aware of all tables when
``create_all()`` is called during application startup.
"""

from app.models.article import Article, ArticleCategory, SentimentLabel
from app.models.feed_source import FeedSource, SourceType

__all__ = [
    "Article",
    "ArticleCategory",
    "FeedSource",
    "SentimentLabel",
    "SourceType",
]
