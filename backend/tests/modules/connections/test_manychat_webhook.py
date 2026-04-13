"""Tests for ManyChat webhook handler — subscriber.new → message_received bridge.

Covers:
- subscriber.new creates BOTH manychat_subscriber_created AND message_received events
- tag.applied creates ONLY manychat_tag_applied (no message_received bridge)
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Helpers: mock payloads
# ---------------------------------------------------------------------------


def _subscriber_new_payload(
    channel: str = "instagram",
    ig_username: str = "testuser",
) -> dict:
    return {
        "event_type": "subscriber.new",
        "channel": channel,
        "subscriber_id": "mc_sub_123",
        "email": "lead@example.com",
        "phone": "+5215512345678",
        "first_name": "Test",
        "last_name": "Lead",
        "ig_username": ig_username,
    }


def _tag_applied_payload(
    tag_name: str = "quiz_started",
    channel: str = "instagram",
) -> dict:
    return {
        "event_type": "tag.applied",
        "channel": channel,
        "subscriber_id": "mc_sub_456",
        "email": "tagged@example.com",
        "phone": None,
        "first_name": "Tagged",
        "last_name": "User",
        "ig_username": "taggeduser",
        "tag_name": tag_name,
    }


# ---------------------------------------------------------------------------
# Mock profile helper
# ---------------------------------------------------------------------------


def _mock_profile():
    profile = MagicMock()
    profile.id = uuid.uuid4()
    profile.lead_source = None
    return profile


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_subscriber_new_creates_message_received_event():
    """subscriber.new should create TWO journey_events:
    1. manychat_subscriber_created (existing behaviour)
    2. message_received (bridge for conversation counting)
    """
    tenant_id = uuid.uuid4()
    payload = _subscriber_new_payload()
    profile = _mock_profile()

    mock_db = MagicMock()

    with (
        patch(
            "src.modules.crm.infrastructure.repositories.customer_repository.CustomerRepository.find_by_trait",
            return_value=None,
        ),
        patch(
            "src.modules.crm.application.services.customer_service.CustomerService.identify",
            return_value=profile,
        ),
        patch(
            "src.modules.crm.application.services.lifecycle_service.LifecycleService.recalculate_score",
            return_value=None,
        ),
        patch(
            "src.modules.analytics.application.services.manychat_metrics_promoter.ManyChatMetricsPromoter.promote_event",
            return_value=None,
        ),
        patch(
            "src.modules.connections.api.marketing_webhooks.logger",
        ),
    ):
        from src.modules.connections.api.marketing_webhooks import (
            _handle_manychat_event,
        )

        await _handle_manychat_event(mock_db, tenant_id, payload, "instagram")

    # db.add should be called TWICE: manychat_subscriber_created + message_received
    assert mock_db.add.call_count == 2, f"Expected 2 db.add calls, got {mock_db.add.call_count}"

    # First call: manychat_subscriber_created
    first_event = mock_db.add.call_args_list[0][0][0]
    assert first_event.event_name == "manychat_subscriber_created"

    # Second call: message_received (the bridge)
    bridge_event = mock_db.add.call_args_list[1][0][0]
    assert bridge_event.event_name == "message_received"
    assert bridge_event.properties["channel_slug"] == "manychat-ig"
    assert bridge_event.properties["source"] == "manychat_webhook"
    assert bridge_event.properties["message_direction"] == "inbound"
    assert bridge_event.properties["manychat_subscriber_id"] == "mc_sub_123"
    assert bridge_event.tenant_id == tenant_id
    assert bridge_event.profile_id == profile.id


@pytest.mark.asyncio
async def test_tag_applied_does_not_create_message_received():
    """tag.applied should create only ONE journey_event (manychat_tag_applied).
    No message_received bridge event should be created.
    """
    tenant_id = uuid.uuid4()
    payload = _tag_applied_payload()
    profile = _mock_profile()

    mock_db = MagicMock()

    with (
        patch(
            "src.modules.crm.infrastructure.repositories.customer_repository.CustomerRepository.find_by_trait",
            return_value=None,
        ),
        patch(
            "src.modules.crm.application.services.customer_service.CustomerService.identify",
            return_value=profile,
        ),
        patch(
            "src.modules.crm.application.services.lifecycle_service.LifecycleService.recalculate_score",
            return_value=None,
        ),
        patch(
            "src.modules.analytics.application.services.manychat_metrics_promoter.ManyChatMetricsPromoter.promote_event",
            return_value=None,
        ),
        patch(
            "src.modules.connections.api.marketing_webhooks.logger",
        ),
    ):
        from src.modules.connections.api.marketing_webhooks import (
            _handle_manychat_event,
        )

        await _handle_manychat_event(mock_db, tenant_id, payload, "instagram")

    # db.add should be called ONCE: only manychat_tag_applied
    assert mock_db.add.call_count == 1, f"Expected 1 db.add call, got {mock_db.add.call_count}"

    event = mock_db.add.call_args_list[0][0][0]
    assert event.event_name == "manychat_tag_applied"
