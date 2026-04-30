"""Base Scorer Protocol — D-5 (CONTRACT PR-3)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class Scorer(Protocol):
    """Evaluates one predicted output against one golden reference.

    Implementations must be pure (no side effects) and return a float in [0, 1].
    """

    def score(self, predicted: str, reference: str) -> float:
        """Return a score in [0.0, 1.0] comparing ``predicted`` to ``reference``."""
        ...

    def aggregate(self, scores: list[float]) -> float:
        """Aggregate a list of per-example scores into a single summary score."""
        ...
