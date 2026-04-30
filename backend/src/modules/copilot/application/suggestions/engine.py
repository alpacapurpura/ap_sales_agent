"""SuggestionEngine — composes providers, ranks, caps, emits telemetry.

Pure async-friendly orchestration. Heuristic ranking (no LLM call). Latency
target <10ms p99 with N≤6 providers. Best-effort observability — engine NEVER
raises; returns ``[]`` on internal failure and emits structlog warning.

[COPILOT-SUGGESTIONS-ENGINE] → docs/domains/copilot/suggestions-engine.md
"""

from __future__ import annotations

import time
from collections import Counter
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from collections.abc import Iterable

    from src.modules.copilot.application.suggestions.providers.base import SuggestionProvider
    from src.modules.copilot.domain.suggestion import Suggestion, SuggestionContext

logger = structlog.get_logger()

_DEFAULT_MAX_TOTAL = 5  # Mirrors FE locked contract (max 5 chips shown).
_DEFAULT_MAX_PER_PROVIDER = 5


class SuggestionEngine:
    """Composes registered providers into a ranked list of suggestions."""

    def __init__(
        self,
        providers: Iterable[SuggestionProvider] | None = None,
        *,
        max_total: int = _DEFAULT_MAX_TOTAL,
        max_per_provider: int = _DEFAULT_MAX_PER_PROVIDER,
    ) -> None:
        """Initialise with optional pre-loaded providers."""
        self._providers: list[SuggestionProvider] = list(providers or [])
        self._max_total = max_total
        self._max_per_provider = max_per_provider

    def register(self, provider: SuggestionProvider) -> None:
        """Idempotent — registering the same ``provider_id`` twice is a no-op.

        Mirrors ``orchestrator/block_adapters.py::register_block_handler``
        ValueError-on-conflict pattern: same id + different instance = bug.
        """
        existing = next((p for p in self._providers if p.provider_id == provider.provider_id), None)
        if existing is provider:
            return
        if existing is not None:
            msg = f"provider_id={provider.provider_id!r} already registered with a different instance"
            raise ValueError(msg)
        self._providers.append(provider)

    def get_suggestions(
        self,
        ctx: SuggestionContext,
    ) -> tuple[list[Suggestion], dict[str, int], int]:
        """Compose, rank, cap. Returns (suggestions, provider_breakdown, latency_ms).

        Caller is responsible for emitting ``SuggestionShown`` event with the
        returned breakdown + latency. Engine is tenant-isolated through
        ``ctx.tenant_id`` — providers MUST use it on every read.

        Ranking: confidence DESC → provider_priority DESC → registration order.
        """
        t0 = time.monotonic()
        collected: list[Suggestion] = []
        breakdown: Counter[str] = Counter()
        priorities: dict[str, int] = {}  # provider_id -> priority for stable sort

        for provider in self._providers:
            if provider.applies_to_routes and ctx.current_route is not None:
                if not any(ctx.current_route.startswith(p) for p in provider.applies_to_routes):
                    continue
            elif provider.applies_to_routes and ctx.current_route is None:
                # applies_to_routes set but no route provided — skip
                continue

            try:
                items = provider.get_suggestions(ctx, max_per_provider=self._max_per_provider)
            except Exception as exc:  # noqa: BLE001 — best-effort; never break caller
                logger.warning(
                    "suggestion_provider_failed",
                    provider_id=provider.provider_id,
                    tenant_id=str(ctx.tenant_id),
                    error=str(exc),
                )
                continue

            priority = getattr(provider, "provider_priority", 0)
            for item in items:
                priorities[str(item.id)] = priority
            collected.extend(items)
            breakdown[provider.provider_id] += len(items)

        # Heuristic global rank: confidence DESC, then provider_priority DESC, then stable order.
        collected.sort(
            key=lambda s: (s.confidence, priorities.get(str(s.id), 0)),
            reverse=True,
        )
        latency_ms = int((time.monotonic() - t0) * 1000)
        return collected[: self._max_total], dict(breakdown), latency_ms


__all__ = ["SuggestionEngine"]
