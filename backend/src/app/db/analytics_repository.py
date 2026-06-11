"""Analytics repository for querying materialized views."""

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker


class AnalyticsRepository:
    """Repository for reading aggregated analytics data."""

    def __init__(self, session_factory: async_sessionmaker) -> None:
        self.session_factory = session_factory

    async def get_trending_entities(
        self,
        time_window_hours: int = 24,
        entity_type: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Fetch trending entities using recency-weighted exponential decay."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=time_window_hours)

        # We score trends by weighting newer hourly buckets higher.
        # Score = sum(count * exp(-lambda * hours_ago))
        query = """
            SELECT 
                entity,
                entity_type,
                SUM(article_count) as total_mentions,
                SUM(article_count * exp(-0.1 * EXTRACT(EPOCH FROM (now() - time_bucket))/3600)) as trend_score
            FROM hourly_trends_mv
            WHERE time_bucket >= :cutoff
        """
        
        params: dict[str, Any] = {"cutoff": cutoff}
        if entity_type:
            query += " AND entity_type = :entity_type"
            params["entity_type"] = entity_type

        query += """
            GROUP BY entity, entity_type
            ORDER BY trend_score DESC
            LIMIT :limit
        """
        params["limit"] = limit

        async with self.session_factory() as session:
            result = await session.execute(text(query), params)
            rows = result.mappings().all()
            return [dict(row) for row in rows]

    async def get_sentiment_summary(
        self,
        time_window_days: int = 7,
    ) -> list[dict[str, Any]]:
        """Fetch sentiment summaries over a given time window."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=time_window_days)
        
        query = """
            SELECT 
                date_bucket,
                sentiment_label,
                article_count
            FROM sentiment_summaries_mv
            WHERE date_bucket >= :cutoff
            ORDER BY date_bucket ASC, sentiment_label
        """
        
        async with self.session_factory() as session:
            result = await session.execute(text(query), {"cutoff": cutoff})
            rows = result.mappings().all()
            return [dict(row) for row in rows]
