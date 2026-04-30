"""Tests for CampaignStep DAG validation."""

from __future__ import annotations

import datetime as dt
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.modules.campaigns.domain.campaign_step import CampaignStep
from src.modules.campaigns.domain.enums import StepType


NOW = dt.datetime.now(dt.timezone.utc)


def make_step(**overrides) -> dict:
    """Factory for valid CampaignStep data."""
    step_id = uuid4()
    base = {
        "id": step_id,
        "tenant_id": uuid4(),
        "campaign_id": uuid4(),
        "step_type": StepType.SEND_MESSAGE,
        "step_index": 0,
        "created_at": NOW,
        "updated_at": NOW,
    }
    base.update(overrides)
    return base


class TestCampaignStepBasicInvariants:
    """Test basic field constraints on CampaignStep."""

    def test_valid_send_message_step(self):
        """A minimal send_message step should be valid."""
        step = CampaignStep(**make_step())
        assert step.step_type == StepType.SEND_MESSAGE
        assert step.next_step_ids == []
        assert step.step_config == {}

    def test_tenant_id_required(self):
        """tenant_id is mandatory."""
        data = make_step()
        del data["tenant_id"]
        with pytest.raises(ValidationError):
            CampaignStep(**data)

    def test_campaign_id_required(self):
        """campaign_id is mandatory."""
        data = make_step()
        del data["campaign_id"]
        with pytest.raises(ValidationError):
            CampaignStep(**data)

    def test_step_index_non_negative(self):
        """step_index must be >= 0."""
        with pytest.raises(ValidationError):
            CampaignStep(**make_step(step_index=-1))

    def test_step_index_zero_ok(self):
        """step_index=0 is valid."""
        step = CampaignStep(**make_step(step_index=0))
        assert step.step_index == 0

    def test_label_max_length(self):
        """label over 128 chars should fail."""
        with pytest.raises(ValidationError):
            CampaignStep(**make_step(label="x" * 129))

    def test_extra_fields_forbidden(self):
        """Extra fields should be forbidden."""
        with pytest.raises(ValidationError):
            CampaignStep(**make_step(unknown_field="value"))

    def test_soft_delete_optional(self):
        """deleted_at defaults to None."""
        step = CampaignStep(**make_step())
        assert step.deleted_at is None


class TestCampaignStepDagNoCycles:
    """Test DAG no-self-loop invariant."""

    def test_self_loop_rejected(self):
        """A step referencing itself in next_step_ids should be rejected."""
        step_id = uuid4()
        with pytest.raises(ValidationError, match="cannot reference itself"):
            CampaignStep(**make_step(id=step_id, next_step_ids=[step_id]))

    def test_multiple_next_steps_ok(self):
        """Branching with multiple next_step_ids is allowed."""
        next_ids = [uuid4(), uuid4()]
        step = CampaignStep(**make_step(next_step_ids=next_ids))
        assert len(step.next_step_ids) == 2

    def test_empty_next_step_ids_ok(self):
        """Empty next_step_ids is valid (terminal step in DAG)."""
        step = CampaignStep(**make_step(next_step_ids=[]))
        assert step.next_step_ids == []

    def test_different_step_ids_ok(self):
        """Referencing other steps (not self) is allowed."""
        step_id = uuid4()
        other_id = uuid4()
        step = CampaignStep(**make_step(id=step_id, next_step_ids=[other_id]))
        assert other_id in step.next_step_ids


class TestCampaignStepTypes:
    """Test all StepType values are accepted."""

    @pytest.mark.parametrize("step_type", list(StepType))
    def test_all_step_types_valid(self, step_type):
        """All StepType enum values should create valid steps."""
        step = CampaignStep(**make_step(step_type=step_type))
        assert step.step_type == step_type

    def test_wait_delay_step_config(self):
        """WAIT_DELAY step accepts delay_seconds in config."""
        config = {"delay_seconds": 3600}
        step = CampaignStep(**make_step(step_type=StepType.WAIT_DELAY, step_config=config))
        assert step.step_config["delay_seconds"] == 3600

    def test_mark_complete_step_empty_config(self):
        """MARK_COMPLETE step with empty config is valid."""
        step = CampaignStep(**make_step(step_type=StepType.MARK_COMPLETE, step_config={}))
        assert step.step_config == {}

    def test_send_message_step_with_template(self):
        """SEND_MESSAGE step can carry template_slug in config."""
        config = {"template_slug": "welcome-message"}
        step = CampaignStep(**make_step(step_type=StepType.SEND_MESSAGE, step_config=config))
        assert step.step_config["template_slug"] == "welcome-message"
