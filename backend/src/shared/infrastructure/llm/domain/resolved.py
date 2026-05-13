"""ResolvedModel — in-memory result of LLMConfigService.resolve(role).

PI-2 S4 PR-1 db-registry-admin-ui.

This is a pure Python dataclass (no SQLAlchemy, no Pydantic, no framework
imports). It represents the outcome of the resolution chain and is used
internally by the service and its callers.

Not persisted — ephemeral per-call result.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from luana_core_platform.core.enums import AIProvider

ResolveSource = Literal["db_binding", "env_fallback", "cache_hit"]


@dataclass(frozen=True, slots=True)
class ResolvedModel:
    """In-memory result of LLMConfigService.resolve(role).

    Returned to callers (Settings.get_model wrap, future per-tenant resolvers).
    Not persisted.

    ``source`` allows observability layer to distinguish cache hits from DB
    hits from env fallbacks for latency + reliability monitoring.
    """

    provider: AIProvider
    model: str
    config: dict[str, Any]  # merged: binding.config or {} on env_fallback
    source: ResolveSource
    binding_id: str | None  # UUID str, NULL when source=env_fallback
