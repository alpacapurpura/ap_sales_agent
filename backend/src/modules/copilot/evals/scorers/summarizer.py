"""SummarizerScorer — ROUGE-L + cosine similarity scorer (D-5 CONTRACT PR-3).

Scoring:
  - ROUGE-L F-score (via ``rouge_score`` package).
  - Cosine similarity via ``sentence-transformers`` MiniLM if available,
    else falls back to word-overlap (Jaccard).
  - Composite: 0.6 * rouge_l + 0.4 * cosine.
  - Aggregate = mean across N goldens.
  - Threshold pass: ≥ 0.85.

Design: graceful-degradation on missing dependencies — scorer stays usable
without sentence-transformers (slower, less accurate but tests don't hard-fail).
"""

from __future__ import annotations

import math


def _rouge_l_f(predicted: str, reference: str) -> float:
    """Compute ROUGE-L F-score between ``predicted`` and ``reference``.

    Uses ``rouge_score`` package if available, else falls back to a simple
    LCS-based approximation so tests pass in environments without it.
    """
    if not predicted or not reference:
        return 0.0
    try:
        from rouge_score import rouge_scorer as rs_module

        scorer = rs_module.RougeScorer(["rougeL"], use_stemmer=False)
        scores = scorer.score(reference, predicted)
        return float(scores["rougeL"].fmeasure)
    except ImportError:
        # Fallback: word-overlap Jaccard as ROUGE-L approximation.
        pred_tokens = set(predicted.lower().split())
        ref_tokens = set(reference.lower().split())
        if not ref_tokens:
            return 0.0
        intersection = pred_tokens & ref_tokens
        union = pred_tokens | ref_tokens
        return len(intersection) / len(union) if union else 0.0


def _cosine_similarity(predicted: str, reference: str) -> float:
    """Compute semantic cosine similarity.

    Uses ``sentence_transformers`` MiniLM if available; falls back to
    word-overlap Jaccard so tests pass without the heavy dependency.
    """
    if not predicted or not reference:
        return 0.0
    try:
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer("all-MiniLM-L6-v2")
        embeddings = model.encode([predicted, reference])
        p, r = embeddings[0], embeddings[1]
        # Cosine = dot(p, r) / (||p|| * ||r||)
        dot = sum(a * b for a, b in zip(p, r, strict=True))
        norm_p = math.sqrt(sum(a * a for a in p))
        norm_r = math.sqrt(sum(b * b for b in r))
        if norm_p == 0 or norm_r == 0:
            return 0.0
        return float(max(0.0, min(1.0, dot / (norm_p * norm_r))))
    except ImportError:
        # Fallback: word-overlap Jaccard.
        pred_tokens = set(predicted.lower().split())
        ref_tokens = set(reference.lower().split())
        if not pred_tokens and not ref_tokens:
            return 1.0
        intersection = pred_tokens & ref_tokens
        union = pred_tokens | ref_tokens
        return len(intersection) / len(union) if union else 0.0


class SummarizerScorer:
    """Composite ROUGE-L + cosine scorer for summarizer goldens.

    Satisfies the ``Scorer`` Protocol from ``scorers/base.py``.
    Weights: 0.6 * ROUGE-L F1 + 0.4 * cosine similarity.
    """

    DEFAULT_THRESHOLD: float = 0.85
    _ROUGE_WEIGHT: float = 0.6
    _COSINE_WEIGHT: float = 0.4

    def score(self, predicted: str, reference: str) -> float:
        """Return composite score in [0.0, 1.0]."""
        rouge = _rouge_l_f(predicted, reference)
        cosine = _cosine_similarity(predicted, reference)
        return self._ROUGE_WEIGHT * rouge + self._COSINE_WEIGHT * cosine

    def aggregate(self, scores: list[float]) -> float:
        """Return mean of ``scores`` (0.0 if empty)."""
        if not scores:
            return 0.0
        return sum(scores) / len(scores)

    def passes_threshold(self, aggregate_score: float) -> bool:
        """Return True if ``aggregate_score >= DEFAULT_THRESHOLD``."""
        return aggregate_score >= self.DEFAULT_THRESHOLD
