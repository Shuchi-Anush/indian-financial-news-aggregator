from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import get_db
from app.models.failed_article import FailedArticle
from app.models.feed_source import FeedSource
from app.models.pipeline_run import PipelineRun

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)

async def verify_admin_key(api_key: str = Security(api_key_header)):
    settings = get_settings()
    if api_key != settings.admin_api_key:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return api_key

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(verify_admin_key)])


@router.get("/pipeline/status")
async def get_pipeline_status(session: AsyncSession = Depends(get_db)):
    stmt = select(PipelineRun).order_by(desc(PipelineRun.started_at)).limit(1)
    result = await session.execute(stmt)
    latest = result.scalar_one_or_none()
    return {"is_running": latest and latest.status.value == "running", "latest_run": latest}


@router.get("/pipeline/runs")
async def get_pipeline_runs(limit: int = 10, session: AsyncSession = Depends(get_db)):
    stmt = select(PipelineRun).order_by(desc(PipelineRun.started_at)).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()


@router.get("/sources/health")
async def get_sources_health(session: AsyncSession = Depends(get_db)):
    stmt = select(FeedSource).order_by(FeedSource.health_score)
    result = await session.execute(stmt)
    return result.scalars().all()


@router.get("/sources/failures")
async def get_sources_failures(limit: int = 20, session: AsyncSession = Depends(get_db)):
    stmt = select(FailedArticle).order_by(desc(FailedArticle.created_at)).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()


@router.get("/enrichment/status")
async def get_enrichment_status(session: AsyncSession = Depends(get_db)):
    from sqlalchemy import func
    from app.models.article_entity import ArticleEntity
    from app.models.article_sector import ArticleSector
    from app.models.article_keyword import ArticleKeyword
    
    entities_count = await session.scalar(select(func.count(ArticleEntity.id)))
    sectors_count = await session.scalar(select(func.count(ArticleSector.id)))
    keywords_count = await session.scalar(select(func.count(ArticleKeyword.id)))
    
    return {
        "total_entities_extracted": entities_count,
        "total_sectors_extracted": sectors_count,
        "total_keywords_extracted": keywords_count,
    }


@router.get("/analytics/status")
async def get_analytics_status(session: AsyncSession = Depends(get_db)):
    from sqlalchemy import text
    
    # We check the row count of the materialized views
    trends_count = await session.scalar(text("SELECT count(*) FROM hourly_trends_mv"))
    sentiment_count = await session.scalar(text("SELECT count(*) FROM sentiment_summaries_mv"))
    
    return {
        "hourly_trends_rows": trends_count,
        "sentiment_summaries_rows": sentiment_count,
    }
