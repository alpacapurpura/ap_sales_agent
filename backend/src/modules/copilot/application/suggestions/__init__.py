"""Suggestion engine public API.

[COPILOT-SUGGESTIONS-ENGINE] → docs/domains/copilot/suggestions-engine.md
"""

from luana_core_copilot.application.suggestions.engine import SuggestionEngine
from luana_core_copilot.application.suggestions.providers.base import SuggestionProvider
from luana_core_copilot.application.suggestions.registry import (
    get_default_engine,
    register_provider,
)

__all__ = [
    "SuggestionEngine",
    "SuggestionProvider",
    "get_default_engine",
    "register_provider",
]
