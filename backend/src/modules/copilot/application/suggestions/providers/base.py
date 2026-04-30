"""Provider port. Concrete providers live alongside in providers/.

[COPILOT-SUGGESTIONS-ENGINE] → docs/domains/copilot/suggestions-engine.md
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from src.modules.copilot.domain.suggestion import Suggestion, SuggestionContext


@runtime_checkable
class SuggestionProvider(Protocol):
    """One module-scoped source of suggestions.

    Implementations MUST:
      - Be tenant-isolated (``ctx.tenant_id`` required by every read).
      - Be best-effort (catch internal exceptions; return ``[]`` on failure).
      - Return ≤``max_per_provider`` suggestions sorted by domain relevance.
      - Set ``source_module`` to a stable id matching ``provider_id`` (e.g. ``"offer"``).
    """

    @property
    def provider_id(self) -> str:
        """Stable id used for telemetry breakdown (matches module_id)."""
        ...

    @property
    def provider_priority(self) -> int:
        """Tie-break weight (Q3 decision). Higher = preferred on equal confidence."""
        ...

    @property
    def applies_to_routes(self) -> tuple[str, ...]:
        """Route prefixes this provider activates on. Empty tuple = always."""
        ...

    def get_suggestions(
        self,
        ctx: SuggestionContext,
        *,
        max_per_provider: int = 5,
    ) -> list[Suggestion]:
        """Compute suggestions for ``ctx``. MUST NOT raise."""
        ...


__all__ = ["SuggestionProvider"]
