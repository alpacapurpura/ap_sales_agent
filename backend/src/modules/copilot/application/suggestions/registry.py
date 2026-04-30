"""Default engine registration — bootstrap providers at module import.

Wired from ``application/discovery.py`` startup hook OR lazy-init on first
``get_default_engine()`` call (tests opt for lazy via ``_reset_for_tests``).

[COPILOT-SUGGESTIONS-ENGINE] -> docs/domains/copilot/suggestions-engine.md
"""

from __future__ import annotations

from threading import Lock
from typing import TYPE_CHECKING

from src.modules.copilot.application.suggestions.engine import SuggestionEngine

if TYPE_CHECKING:
    from src.modules.copilot.application.suggestions.providers.base import SuggestionProvider

# Container to hold the process-wide engine (avoids ``global`` statement).
_state: dict[str, SuggestionEngine | None] = {"engine": None}
_engine_lock = Lock()


def get_default_engine() -> SuggestionEngine:
    """Return the process-wide engine. Lazy-init on first access.

    Bootstrap registers built-in providers (``OfferSuggestionProvider``).
    External plugins register via ``register_provider(...)``.
    """
    if _state["engine"] is None:
        with _engine_lock:
            if _state["engine"] is None:
                engine = SuggestionEngine()
                _bootstrap_builtin(engine)
                _state["engine"] = engine
    return _state["engine"]  # type: ignore[return-value]


def register_provider(provider: SuggestionProvider) -> None:
    """Register a provider on the default engine."""
    get_default_engine().register(provider)


def _bootstrap_builtin(engine: SuggestionEngine) -> None:
    """Register the providers shipped in this PR. Future PRs append here."""
    from src.modules.copilot.application.suggestions.providers.offer import (
        OfferSuggestionProvider,
    )

    engine.register(OfferSuggestionProvider())


def _reset_for_tests() -> None:
    """Test-only -- restart the lazy singleton between tests."""
    with _engine_lock:
        _state["engine"] = None


__all__ = [
    "_reset_for_tests",
    "get_default_engine",
    "register_provider",
]
