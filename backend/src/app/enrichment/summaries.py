"""Article summarization processor.

Implements lightweight, deterministic, extractive summarization.
"""

import os
import re
from collections import Counter

from app.enrichment.interfaces import EnrichmentContext, EnrichmentProcessor

class ExtractiveSummarizer(EnrichmentProcessor):
    """Extracts top sentences to form a summary."""

    def __init__(self) -> None:
        self._enabled = os.getenv("ENABLE_SUMMARIZATION", "False").lower() in ("true", "1", "yes")
        self._sentence_pattern = re.compile(r"([^.!?]+[.!?]+)")
        self._word_pattern = re.compile(r"\b[a-zA-Z]{3,}\b")
        
        # Stopwords for scoring
        self._stopwords = {
            "the", "and", "a", "to", "of", "in", "is", "that", "it", "on", "for", "with",
            "as", "was", "at", "by", "an", "be", "this", "which", "or", "from", "but", "not"
        }

    @property
    def name(self) -> str:
        return "extractive_summarizer"

    async def process(self, context: EnrichmentContext) -> None:
        if not self._enabled or not context.article.content:
            return

        text = context.article.content
        if len(text) < 200:
            # Too short to summarize
            return

        if len(text) > 50000:
            # Bound memory and CPU
            text = text[:50000]

        sentences = [s.strip() for s in self._sentence_pattern.findall(text) if len(s.strip()) > 20]
        if len(sentences) <= 3:
            return

        # Score sentences based on word frequencies
        words = self._word_pattern.findall(text.lower())
        filtered = [w for w in words if w not in self._stopwords]
        word_freq = Counter(filtered)

        max_freq = max(word_freq.values()) if word_freq else 1.0
        word_scores = {w: count / max_freq for w, count in word_freq.items()}

        sentence_scores = []
        for i, sentence in enumerate(sentences):
            s_words = self._word_pattern.findall(sentence.lower())
            score = sum(word_scores.get(w, 0) for w in s_words)
            # Penalize very long or very short sentences
            if len(s_words) > 30 or len(s_words) < 5:
                score *= 0.5
            
            # Boost first sentence
            if i == 0:
                score *= 1.5

            sentence_scores.append((score, i, sentence))

        # Take top 2-3 sentences, sorted by original order
        top_sentences = sorted(sentence_scores, key=lambda x: x[0], reverse=True)[:3]
        top_sentences.sort(key=lambda x: x[1])

        summary = " ".join(s[2] for s in top_sentences)
        
        # Cap length
        if len(summary) > 1000:
            summary = summary[:997] + "..."
            
        context.generated_summary = summary
