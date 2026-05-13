"""Tests for Campaign aggregate root entity invariants."""

from __future__ import annotations

import datetime as dt
from uuid import uuid4

import pytest
from pydantic import ValidationError

from luana_core_campaigns.domain.campaign import Campaign, _FSM_TRANSITIONS
from luana_core_campaigns.domain.enums import CampaignStatus, CampaignType


NOW = dt.datetime.now(dt.timezone.utc)


def make_campaign(**overrides) -> dict:
    """Factory for valid Campaign data."""
    base = {
        "id": uuid4(),
        "tenant_id": uuid4(),
        "name": "Test Campaign",
        "campaign_type": CampaignType.EMAIL_BROADCAST,
        "status": CampaignStatus.DRAFT,
        "created_at": NOW,
        "updated_at": NOW,
    }
    base.update(overrides)
    return base


class TestCampaignBasicInvariants:
    """Test basic invariants on Campaign entity."""

    def test_valid_draft_campaign(self):
        """A minimal draft campaign should be valid."""
        c = Campaign(**make_campaign())
        assert c.status == CampaignStatus.DRAFT
        assert c.deleted_at is None
        assert c.channel_priority == []
        assert c.config == {}

    def test_tenant_id_required(self):
        """tenant_id is mandatory."""
        data = make_campaign()
        del data["tenant_id"]
        with pytest.raises(ValidationError):
            Campaign(**data)

    def test_name_required(self):
        """name is mandatory."""
        data = make_campaign()
        del data["name"]
        with pytest.raises(ValidationError):
            Campaign(**data)

    def test_name_cannot_be_empty(self):
        """Empty name should fail."""
        with pytest.raises(ValidationError):
            Campaign(**make_campaign(name=""))

    def test_name_max_length(self):
        """Name over 255 chars should fail."""
        with pytest.raises(ValidationError):
            Campaign(**make_campaign(name="x" * 256))

    def test_description_max_length(self):
        """Description over 2000 chars should fail."""
        with pytest.raises(ValidationError):
            Campaign(**make_campaign(description="x" * 2001))

    def test_extra_fields_forbidden(self):
        """Extra fields should be forbidden (extra='forbid')."""
        with pytest.raises(ValidationError):
            Campaign(**make_campaign(unknown_field="value"))

    def test_default_status_is_draft(self):
        """Default status should be DRAFT."""
        data = make_campaign()
        data.pop("status", None)
        c = Campaign(**data)
        assert c.status == CampaignStatus.DRAFT

    def test_soft_delete_column_optional(self):
        """deleted_at defaults to None."""
        c = Campaign(**make_campaign())
        assert c.deleted_at is None


class TestCampaignStatusInvariants:
    """Test status-dependent field requirements enforced by model_validator."""

    def test_scheduled_requires_scheduled_at(self):
        """SCHEDULED status requires scheduled_at."""
        with pytest.raises(ValidationError, match="scheduled_at required"):
            Campaign(**make_campaign(status=CampaignStatus.SCHEDULED))

    def test_scheduled_with_scheduled_at_ok(self):
        """SCHEDULED with scheduled_at is valid."""
        c = Campaign(**make_campaign(status=CampaignStatus.SCHEDULED, scheduled_at=NOW))
        assert c.status == CampaignStatus.SCHEDULED

    def test_paused_requires_scheduled_at(self):
        """PAUSED status requires scheduled_at."""
        with pytest.raises(ValidationError, match="scheduled_at required"):
            Campaign(**make_campaign(status=CampaignStatus.PAUSED))

    def test_running_requires_scheduled_at_and_launched_at(self):
        """RUNNING status requires both scheduled_at and launched_at."""
        with pytest.raises(ValidationError):
            Campaign(**make_campaign(status=CampaignStatus.RUNNING, scheduled_at=NOW))

    def test_running_ok(self):
        """RUNNING with both timestamps is valid."""
        c = Campaign(
            **make_campaign(
                status=CampaignStatus.RUNNING,
                scheduled_at=NOW,
                launched_at=NOW,
            )
        )
        assert c.status == CampaignStatus.RUNNING

    def test_completed_requires_completed_at(self):
        """COMPLETED status requires completed_at."""
        with pytest.raises(ValidationError, match="completed_at required"):
            Campaign(
                **make_campaign(
                    status=CampaignStatus.COMPLETED,
                    scheduled_at=NOW,
                    launched_at=NOW,
                )
            )

    def test_canceled_requires_completed_at(self):
        """CANCELED status requires completed_at."""
        with pytest.raises(ValidationError, match="completed_at required"):
            Campaign(**make_campaign(status=CampaignStatus.CANCELED))

    def test_agent_conversation_scheduled_requires_offer_id(self):
        """AGENT_CONVERSATION campaigns from SCHEDULED onward require offer_id."""
        with pytest.raises(ValidationError, match="offer_id required"):
            Campaign(
                **make_campaign(
                    campaign_type=CampaignType.AGENT_CONVERSATION,
                    status=CampaignStatus.SCHEDULED,
                    scheduled_at=NOW,
                )
            )

    def test_agent_conversation_draft_no_offer_ok(self):
        """AGENT_CONVERSATION in DRAFT does not require offer_id."""
        c = Campaign(
            **make_campaign(
                campaign_type=CampaignType.AGENT_CONVERSATION,
                status=CampaignStatus.DRAFT,
            )
        )
        assert c.campaign_type == CampaignType.AGENT_CONVERSATION

    def test_agent_conversation_scheduled_with_offer_ok(self):
        """AGENT_CONVERSATION in SCHEDULED with offer_id is valid."""
        c = Campaign(
            **make_campaign(
                campaign_type=CampaignType.AGENT_CONVERSATION,
                status=CampaignStatus.SCHEDULED,
                scheduled_at=NOW,
                offer_id=uuid4(),
            )
        )
        assert c.offer_id is not None


class TestCampaignTransitionAllowed:
    """Test transition_allowed classmethod."""

    def test_draft_to_scheduled(self):
        """DRAFT -> SCHEDULED is allowed."""
        assert Campaign.transition_allowed(CampaignStatus.DRAFT, CampaignStatus.SCHEDULED)

    def test_draft_to_canceled(self):
        """DRAFT -> CANCELED is allowed."""
        assert Campaign.transition_allowed(CampaignStatus.DRAFT, CampaignStatus.CANCELED)

    def test_draft_to_running_not_allowed(self):
        """DRAFT -> RUNNING is not allowed (must go through SCHEDULED first)."""
        assert not Campaign.transition_allowed(CampaignStatus.DRAFT, CampaignStatus.RUNNING)

    def test_completed_to_running_not_allowed(self):
        """COMPLETED is terminal — no transitions allowed."""
        assert not Campaign.transition_allowed(CampaignStatus.COMPLETED, CampaignStatus.RUNNING)

    def test_canceled_to_running_not_allowed(self):
        """CANCELED is terminal — no transitions allowed."""
        assert not Campaign.transition_allowed(CampaignStatus.CANCELED, CampaignStatus.RUNNING)

    def test_running_to_paused(self):
        """RUNNING -> PAUSED is allowed."""
        assert Campaign.transition_allowed(CampaignStatus.RUNNING, CampaignStatus.PAUSED)

    def test_paused_to_running(self):
        """PAUSED -> RUNNING (resume) is allowed."""
        assert Campaign.transition_allowed(CampaignStatus.PAUSED, CampaignStatus.RUNNING)

    def test_running_to_completed(self):
        """RUNNING -> COMPLETED is allowed."""
        assert Campaign.transition_allowed(CampaignStatus.RUNNING, CampaignStatus.COMPLETED)


class TestCampaignFsmMatrix:
    """Test FSM matrix structure."""

    def test_fsm_transitions_exported(self):
        """FSM transitions should be accessible via classmethod."""
        transitions = Campaign.get_fsm_transitions()
        assert isinstance(transitions, dict)
        assert len(transitions) == len(CampaignStatus)

    def test_terminal_states_have_empty_transitions(self):
        """COMPLETED and CANCELED have no allowed transitions."""
        transitions = Campaign.get_fsm_transitions()
        assert transitions[CampaignStatus.COMPLETED] == frozenset()
        assert transitions[CampaignStatus.CANCELED] == frozenset()

    def test_all_statuses_covered(self):
        """Every CampaignStatus must be a key in _FSM_TRANSITIONS."""
        for status in CampaignStatus:
            assert status in _FSM_TRANSITIONS, f"{status} missing from _FSM_TRANSITIONS"
