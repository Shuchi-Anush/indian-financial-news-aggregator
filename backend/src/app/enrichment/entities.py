"""Entity extraction processor.

Uses bounded regex and dictionaries to deterministically extract
financial entities (companies, indices, regulators, etc).
"""

import re
from typing import ClassVar

from app.domain.articles import EntityExtraction
from app.enrichment.interfaces import EnrichmentContext, EnrichmentProcessor

class EntityExtractor(EnrichmentProcessor):
    """Extracts known entities using optimized regexes."""

    _VERSION: ClassVar[int] = 1

    # Bounded dictionary for Indian financial entities
    _COMPANIES = {
        "Reliance", "TCS", "Infosys", "HDFC Bank", "ICICI Bank", "SBI",
        "State Bank of India", "Bajaj Finance", "L&T", "Larsen & Toubro",
        "Wipro", "HCL Tech", "ITC", "Kotak Mahindra", "Axis Bank",
        "Tata Motors", "Maruti Suzuki", "Sun Pharma", "NTPC",
        "Tata Steel", "Adani", "Adani Enterprises", "Adani Ports"
    }

    _REGULATORS = {
        "RBI", "SEBI", "IRDAI", "PFRDA", "Reserve Bank of India"
    }

    _INDICES = {
        "Nifty", "Nifty 50", "Sensex", "BSE Sensex", "Bank Nifty", "Nifty IT"
    }

    _CURRENCIES = {
        "Rupee", "INR", "USD", "Dollar", "Euro", "Yen"
    }

    def __init__(self) -> None:
        # Precompile bounded regexes using word boundaries.
        # This keeps the search strictly O(N) where N is text length.
        self._patterns = {
            "Company": self._build_pattern(self._COMPANIES),
            "Regulator": self._build_pattern(self._REGULATORS),
            "Index": self._build_pattern(self._INDICES),
            "Currency": self._build_pattern(self._CURRENCIES),
        }

    @property
    def name(self) -> str:
        return "entity_extractor"

    def _build_pattern(self, items: set[str]) -> re.Pattern[str]:
        # Sort by length descending to match longest first
        sorted_items = sorted(items, key=len, reverse=True)
        escaped = [re.escape(item) for item in sorted_items]
        pattern_str = r"\b(" + "|".join(escaped) + r")\b"
        return re.compile(pattern_str, re.IGNORECASE)

    async def process(self, context: EnrichmentContext) -> None:
        text = f"{context.article.title} {context.article.content or ''}"
        
        # Bounded token limits to prevent regex DoS
        if len(text) > 100000:
            text = text[:100000]

        extracted = set()

        for entity_type, pattern in self._patterns.items():
            matches = pattern.finditer(text)
            for match in matches:
                # Normalize case to match dictionary capitalization
                matched_str = match.group(1).title() if entity_type != "Regulator" else match.group(1).upper()
                
                # Special cases for acronyms
                if matched_str.upper() in {"RBI", "SEBI", "IRDAI", "PFRDA", "INR", "USD", "TCS", "SBI", "NTPC", "ITC"}:
                    matched_str = matched_str.upper()
                elif matched_str.upper() == "L&T":
                    matched_str = "L&T"

                key = (matched_str, entity_type)
                if key not in extracted:
                    extracted.add(key)
                    context.entities.append(
                        EntityExtraction(
                            entity=matched_str,
                            entity_type=entity_type,
                            confidence=1.0,
                            extractor_version=self._VERSION,
                        )
                    )
