"""Analytics API endpoints."""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import Any

from app.db.session import get_db_session_factory
from app.db.analytics_repository import AnalyticsRepository
from sqlalchemy.ext.asyncio import async_sessionmaker

router = APIRouter(prefix="/analytics", tags=["analytics"])


def get_analytics_repo(
    session_factory: async_sessionmaker = Depends(get_db_session_factory),
) -> AnalyticsRepository:
    return AnalyticsRepository(session_factory)


class TrendingEntityResponse(BaseModel):
    entity: str
    entity_type: str
    total_mentions: int
    trend_score: float

class SentimentSummaryResponse(BaseModel):
    date_bucket: str
    sentiment_label: str
    article_count: int


@router.get("/trending", response_model=list[TrendingEntityResponse])
async def get_trending_entities(
    time_window_hours: int = Query(24, ge=1, le=168, description="Hours to look back"),
    entity_type: str | None = Query(None, description="Filter by entity type (Company, Regulator, etc)"),
    limit: int = Query(10, ge=1, le=100),
    repo: AnalyticsRepository = Depends(get_analytics_repo),
) -> Any:
    """Get trending entities based on recency-weighted exponential decay."""
    results = await repo.get_trending_entities(
        time_window_hours=time_window_hours,
        entity_type=entity_type,
        limit=limit,
    )
    return results


@router.get("/sentiment", response_model=list[SentimentSummaryResponse])
async def get_sentiment_summaries(
    time_window_days: int = Query(7, ge=1, le=30, description="Days to look back"),
    repo: AnalyticsRepository = Depends(get_analytics_repo),
) -> Any:
    """Get daily sentiment distribution."""
    results = await repo.get_sentiment_summary(time_window_days=time_window_days)
    
    # Convert datetime objects to ISO dates for JSON response
    formatted = []
    for r in results:
        r_dict = dict(r)
        if hasattr(r_dict["date_bucket"], "isoformat"):
            r_dict["date_bucket"] = r_dict["date_bucket"].strftime("%Y-%m-%d")
        formatted.append(r_dict)
        
    return formatted
