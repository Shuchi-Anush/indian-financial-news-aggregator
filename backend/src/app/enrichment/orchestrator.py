"""Enrichment orchestrator.

Runs a deduplicated article through a sequence of isolated enrichment processors.
"""

from typing import Sequence

from prometheus_client import Counter, Histogram  # type: ignore
import structlog

from app.domain.articles import CanonicalArticle, EnrichedArticle
from app.enrichment.interfaces import EnrichmentContext, EnrichmentProcessor

log = structlog.get_logger(__name__)

# Metrics
ENRICHMENT_LATENCY = Histogram(
    "enrichment_duration_seconds",
    "Time spent in enrichment processors",
    ["processor_name"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0],
)

ENRICHMENT_FAILURES = Counter(
    "enrichment_failures_total",
    "Number of enrichment processor failures",
    ["processor_name"],
)


class EnrichmentOrchestrator:
    """Manages the execution of enrichment processors on canonical articles."""

    def __init__(self, processors: Sequence[EnrichmentProcessor]):
        self.processors = processors

    async def enrich(self, article: CanonicalArticle) -> EnrichedArticle:
        """Run all registered processors on a single article.
        
        Failures in any single processor are caught, logged, and tracked
        via metrics, allowing the pipeline to continue unimpeded.
        """
        context = EnrichmentContext(article=article)
        
        if not self.processors:
            return self._build_enriched(context)

        for processor in self.processors:
            with ENRICHMENT_LATENCY.labels(processor_name=processor.name).time():
                try:
                    await processor.process(context)
                except Exception as e:
                    ENRICHMENT_FAILURES.labels(processor_name=processor.name).inc()
                    log.error(
                        "enrichment_processor_failed",
                        processor_name=processor.name,
                        article_url=article.url,
                        error=str(e),
                        exc_info=True,
                    )
                    
        return self._build_enriched(context)

    def _build_enriched(self, context: EnrichmentContext) -> EnrichedArticle:
        return EnrichedArticle(
            title=context.article.title,
            url=context.article.url,
            source_id=context.article.source_id,
            content_hash=context.article.content_hash,
            collected_at=context.article.collected_at,
            content=context.article.content,
            summary=context.article.summary,
            author=context.article.author,
            published_at=context.article.published_at,
            category=context.article.category,
            tags=context.article.tags,
            quality_score=context.article.quality_score,
            entities=tuple(context.entities),
            sectors=tuple(context.sectors),
            keywords=tuple(context.keywords),
            sentiment_label=context.sentiment_label,
            sentiment_score=context.sentiment_score,
            generated_summary=context.generated_summary,
        )
