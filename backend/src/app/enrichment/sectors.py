"""Sector classification processor.

Uses deterministic keyword matching with bounded scoring limits.
"""

import re
from typing import ClassVar

from app.domain.articles import SectorClassification
from app.enrichment.interfaces import EnrichmentContext, EnrichmentProcessor

class SectorClassifier(EnrichmentProcessor):
    """Classifies articles into sectors based on explicit keyword mapping."""

    _SECTOR_KEYWORDS: ClassVar[dict[str, list[str]]] = {
        "Banking": ["bank", "rbi", "lending", "loan", "npa", "hdfc", "icici", "sbi", "repo rate"],
        "IT": ["tcs", "infosys", "wipro", "hcl", "tech", "software", "ai", "cloud"],
        "Pharma": ["pharma", "fda", "sun pharma", "lupin", "dr reddy", "medicine", "drug"],
        "Energy": ["oil", "gas", "coal", "power", "solar", "reliance", "ntpc", "adani green"],
        "FMCG": ["fmcg", "itc", "hindustan unilever", "nestle", "consumer", "retail"],
        "Auto": ["auto", "maruti", "tata motors", "mahindra", "ev", "vehicle"],
        "Telecom": ["telecom", "jio", "airtel", "vodafone", "5g", "spectrum"],
        "Markets": ["nifty", "sensex", "bse", "nse", "stock", "shares", "equity", "bull", "bear"],
        "Economy": ["gdp", "inflation", "cpi", "fiscal", "deficit", "export", "import"],
        "Policy": ["sebi", "budget", "finance minister", "tax", "gst", "tariff", "subsidy"]
    }

    def __init__(self) -> None:
        self._compiled_patterns = {
            sector: re.compile(r"\b(" + "|".join(re.escape(kw) for kw in keywords) + r")\b", re.IGNORECASE)
            for sector, keywords in self._SECTOR_KEYWORDS.items()
        }

    @property
    def name(self) -> str:
        return "sector_classifier"

    async def process(self, context: EnrichmentContext) -> None:
        text = f"{context.article.title} {context.article.content or ''}"
        
        # Bounded token limits
        if len(text) > 100000:
            text = text[:100000]

        sector_scores = {}
        for sector, pattern in self._compiled_patterns.items():
            matches = pattern.findall(text)
            if matches:
                # Basic scoring: count of matching keywords
                score = min(float(len(matches)), 10.0) # Cap score at 10.0
                sector_scores[sector] = score

        # Take top 3 sectors
        sorted_sectors = sorted(sector_scores.items(), key=lambda x: x[1], reverse=True)[:3]

        for sector, score in sorted_sectors:
            context.sectors.append(SectorClassification(sector=sector, score=score))
