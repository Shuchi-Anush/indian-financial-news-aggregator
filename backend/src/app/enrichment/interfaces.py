import abc
from dataclasses import dataclass, field
from typing import Optional

from app.domain.articles import (
    CanonicalArticle,
    EntityExtraction,
    KeywordExtraction,
    SectorClassification,
)


@dataclass
class EnrichmentContext:
    """Mutable context passed through processors to accumulate enrichments."""
    article: CanonicalArticle
    entities: list[EntityExtraction] = field(default_factory=list)
    sectors: list[SectorClassification] = field(default_factory=list)
    keywords: list[KeywordExtraction] = field(default_factory=list)
    sentiment_label: Optional[str] = None
    sentiment_score: Optional[float] = None
    generated_summary: Optional[str] = None


class EnrichmentProcessor(abc.ABC):
    """Base interface for all deterministic enrichment processors.
    
    Designed to be CPU/Memory bounded, operating independently
    so that failures in one do not crash the entire pipeline.
    """

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Name of the processor for logging and metrics."""
        ...

    @abc.abstractmethod
    async def process(self, context: EnrichmentContext) -> None:
        """Mutate the EnrichmentContext in-place with enriched data.
        
        Args:
            context: Holds the canonical article and accumulates results.
        """
        ...
