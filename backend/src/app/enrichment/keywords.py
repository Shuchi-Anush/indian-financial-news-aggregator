"""Keyword extraction processor.

Extracts top words based on frequency and basic stopword removal.
"""

import re
from collections import Counter
from typing import ClassVar

from app.domain.articles import KeywordExtraction
from app.enrichment.interfaces import EnrichmentContext, EnrichmentProcessor

class KeywordExtractor(EnrichmentProcessor):
    """Deterministic term frequency extractor."""

    _STOPWORDS: ClassVar[set[str]] = {
        "the", "and", "a", "to", "of", "in", "i", "is", "that", "it", "on", "you",
        "this", "for", "but", "with", "are", "have", "be", "at", "or", "as", "was",
        "so", "if", "out", "not", "said", "will", "has", "from", "by", "an", "its",
        "they", "we", "he", "she", "it", "which", "about", "more", "their", "up",
        "one", "were", "what", "there", "all", "when", "can", "would", "who",
        "been", "into", "also", "new", "after", "year", "two", "time", "first",
        "over", "just", "like", "could", "than", "now", "some", "other", "how",
        "only", "do", "them", "these", "most", "any", "no", "because", "back",
        "us", "through", "such", "rs", "crore", "lakh", "per", "cent", "percent"
    }

    def __init__(self) -> None:
        self._word_pattern = re.compile(r"\b[a-zA-Z]{3,}\b")

    @property
    def name(self) -> str:
        return "keyword_extractor"

    async def process(self, context: EnrichmentContext) -> None:
        text = f"{context.article.title} {context.article.content or ''}"
        
        if len(text) > 100000:
            text = text[:100000]

        words = self._word_pattern.findall(text.lower())
        filtered = [w for w in words if w not in self._STOPWORDS]
        
        counts = Counter(filtered)
        
        # Take top 5 keywords
        top_keywords = counts.most_common(5)
        
        max_count = top_keywords[0][1] if top_keywords else 1.0
        
        for kw, count in top_keywords:
            weight = round(count / max_count, 4)
            context.keywords.append(KeywordExtraction(keyword=kw, weight=weight))
