"""S7 — PersonalityProfileUpdatedEvent + cache invalidation subscriber tests.

Verifies that mutations to a PersonalityProfile publish the domain event so
the sales_agent ``PromptLoader`` cache is invalidated for that tenant before
the next turn renders. Without this, ``state['brand_voice']`` would serve a
stale system_instruction until the in-process cache organically expired.
"""

from __future__ import annotations

import uuid
from unittest.mock import patch

from src.shared.application.personality_event_handlers import (
    handle_personality_profile_updated,
    register_personality_event_handlers,
)
from src.shared.domain.events import EventBus, PersonalityProfileUpdatedEvent

TENANT_ID = uuid.UUID("aaaa0000-0000-0000-0000-000000000001")
PROFILE_ID = uuid.UUID("bbbb0000-0000-0000-0000-000000000002")


class TestPersonalityProfileUpdatedEvent:
    def test_event_create_carries_tenant_profile_action(self) -> None:
        """Factory populates event_name, tenant_id, and full payload."""
        event = PersonalityProfileUpdatedEvent.create(
            tenant_id=TENANT_ID,
            profile_id=PROFILE_ID,
            action="updated",
        )
        assert event.event_name == "personality_profile_updated"
        assert event.tenant_id == TENANT_ID
        assert event.payload["profile_id"] == str(PROFILE_ID)
        assert event.payload["action"] == "updated"


class TestPersonalityCacheInvalidator:
    def test_subscriber_invalidates_prompt_loader_cache(self) -> None:
        """The subscriber clears the per-tenant cache via PromptLoader.invalidate_tenant."""
        with patch(
            "src.shared.application.personality_event_handlers.prompt_loader",
        ) as mock_loader:
            event = PersonalityProfileUpdatedEvent.create(
                tenant_id=TENANT_ID,
                profile_id=PROFILE_ID,
                action="selected",
            )
            handle_personality_profile_updated(event)
            mock_loader.invalidate_tenant.assert_called_once_with(TENANT_ID)

    def test_subscriber_swallows_invalidate_exceptions(self) -> None:
        """Best-effort: a cache-invalidate failure must NOT propagate to the publisher."""
        with patch(
            "src.shared.application.personality_event_handlers.prompt_loader",
        ) as mock_loader:
            mock_loader.invalidate_tenant.side_effect = RuntimeError("cache down")
            event = PersonalityProfileUpdatedEvent.create(
                tenant_id=TENANT_ID,
                profile_id=PROFILE_ID,
                action="updated",
            )
            # Must not raise.
            handle_personality_profile_updated(event)


class TestRegistration:
    def test_register_personality_event_handlers_is_idempotent(self) -> None:
        """Calling register twice should not duplicate the subscriber."""
        register_personality_event_handlers()
        register_personality_event_handlers()
        handlers = EventBus._handlers.get("personality_profile_updated", [])
        assert handlers.count(handle_personality_profile_updated) == 1
