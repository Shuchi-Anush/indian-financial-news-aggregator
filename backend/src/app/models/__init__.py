"""ORM models package — re-exports all model classes.

Import models here so that ``Base.metadata`` is aware of all tables when
``create_all()`` is called during application startup.
"""

from app.models.article import Article, ArticleCategory, SentimentLabel
from app.models.feed_source import FeedSource, SourceType, SourceHealth
from app.models.pipeline_run import PipelineRun
from app.models.raw_article import RawArticle, ProcessingStatus
from app.models.failed_article import FailedArticle, FailureStage

__all__ = [
    "Article",
    "ArticleCategory",
    "FeedSource",
    "SentimentLabel",
    "SourceType",
    "SourceHealth",
    "PipelineRun",
    "RawArticle",
    "ProcessingStatus",
    "FailedArticle",
    "FailureStage",
]
