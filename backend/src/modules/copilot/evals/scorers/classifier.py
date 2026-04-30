"""ClassifierScorer — exact-match tier scorer (D-5 CONTRACT PR-3).

Scoring:
  - Exact match: predicted_tier == expected_tier → 1.0 else 0.0.
  - Aggregate score = mean across N goldens.
  - Threshold pass: ≥ 0.95.
"""

from __future__ import annotations


class ClassifierScorer:
    """Exact-match scorer for tier classification goldens.

    Satisfies the ``Scorer`` Protocol from ``scorers/base.py``.
    """

    DEFAULT_THRESHOLD: float = 0.95

    def score(self, predicted: str, reference: str) -> float:
        """Return 1.0 if ``predicted == reference`` (normalized), else 0.0."""
        return 1.0 if predicted.strip().lower() == reference.strip().lower() else 0.0

    def aggregate(self, scores: list[float]) -> float:
        """Return the mean of ``scores`` (0.0 if empty)."""
        if not scores:
            return 0.0
        return sum(scores) / len(scores)

    def passes_threshold(self, aggregate_score: float) -> bool:
        """Return True if ``aggregate_score >= DEFAULT_THRESHOLD``."""
        return aggregate_score >= self.DEFAULT_THRESHOLD
