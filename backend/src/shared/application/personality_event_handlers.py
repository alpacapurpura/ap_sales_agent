"""Subscribers for ``personality_profile_updated`` domain events.

When a tenant edits their PersonalityProfile in Brand Studio, the sales_agent
``PromptLoader`` cache is invalidated for that tenant so the next turn picks
up the freshly recompiled ``system_instruction`` (BRAND_VOICE slot 5).

Best-effort: subscriber failures NEVER crash the publishing service.
See ``.claude/rules/sales-agent-brand-voice.md``.
"""

from __future__ import annotations

import structlog

from src.modules.sales_agent.infrastructure.prompts.base import prompt_loader
from src.shared.domain.events import DomainEvent, EventBus

logger = structlog.get_logger()


def handle_personality_profile_updated(event: DomainEvent) -> None:
    """Invalidate the per-tenant prompt loader cache.

    Triggered for any of: ``selected``, ``updated``, ``cloned``, ``activated``,
    ``deleted``. The action is informational; we always invalidate.
    """
    try:
        prompt_loader.invalidate_tenant(event.tenant_id)
        logger.info(
            "personality_profile_updated.cache_invalidated",
            tenant_id=str(event.tenant_id),
            profile_id=event.payload.get("profile_id"),
            action=event.payload.get("action"),
        )
    except Exception:
        # Best-effort — never crash the publisher.
        logger.exception(
            "personality_profile_updated.cache_invalidate_failed",
            tenant_id=str(event.tenant_id),
        )


def register_personality_event_handlers() -> None:
    """Idempotent registration. Safe to call multiple times."""
    handlers = EventBus._handlers.get(
        "personality_profile_updated",
        [],
    )
    if handle_personality_profile_updated in handlers:
        return
    EventBus.subscribe(
        "personality_profile_updated",
        handle_personality_profile_updated,
    )
