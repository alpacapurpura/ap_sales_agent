"""Suggestion engine public API.

[COPILOT-SUGGESTIONS-ENGINE] → docs/domains/copilot/suggestions-engine.md
"""

from src.modules.copilot.application.suggestions.engine import SuggestionEngine
from src.modules.copilot.application.suggestions.providers.base import SuggestionProvider
from src.modules.copilot.application.suggestions.registry import (
    get_default_engine,
    register_provider,
)

__all__ = [
    "SuggestionEngine",
    "SuggestionProvider",
    "get_default_engine",
    "register_provider",
]
