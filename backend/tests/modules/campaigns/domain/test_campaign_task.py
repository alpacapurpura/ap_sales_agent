"""Tests for CampaignTask domain entity invariants."""

from __future__ import annotations

import datetime as dt
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.modules.campaigns.domain.campaign_task import CampaignTask
from src.modules.campaigns.domain.enums import TaskStatus


NOW = dt.datetime.now(dt.timezone.utc)


def make_task(**overrides) -> dict:
    """Factory for valid CampaignTask data."""
    base = {
        "id": uuid4(),
        "tenant_id": uuid4(),
        "campaign_id": uuid4(),
        "lead_id": uuid4(),
        "scheduled_at": NOW,
        "idempotency_key": f"task:{uuid4()}:single",
        "created_at": NOW,
        "updated_at": NOW,
    }
    base.update(overrides)
    return base


class TestCampaignTaskBasicInvariants:
    """Test basic invariants on CampaignTask entity."""

    def test_valid_pending_task(self):
        """A minimal pending task should be valid."""
        task = CampaignTask(**make_task())
        assert task.status == TaskStatus.PENDING
        assert task.attempt_count == 0
        assert task.deleted_at is None
        assert task.step_id is None

    def test_tenant_id_required(self):
        """tenant_id is mandatory."""
        data = make_task()
        del data["tenant_id"]
        with pytest.raises(ValidationError):
            CampaignTask(**data)

    def test_lead_id_required(self):
        """lead_id is mandatory."""
        data = make_task()
        del data["lead_id"]
        with pytest.raises(ValidationError):
            CampaignTask(**data)

    def test_scheduled_at_required(self):
        """scheduled_at is mandatory."""
        data = make_task()
        del data["scheduled_at"]
        with pytest.raises(ValidationError):
            CampaignTask(**data)

    def test_idempotency_key_required(self):
        """idempotency_key is mandatory."""
        data = make_task()
        del data["idempotency_key"]
        with pytest.raises(ValidationError):
            CampaignTask(**data)

    def test_idempotency_key_cannot_be_empty(self):
        """Empty idempotency_key should fail."""
        with pytest.raises(ValidationError):
            CampaignTask(**make_task(idempotency_key=""))

    def test_idempotency_key_max_length(self):
        """Idempotency key over 256 chars should fail."""
        with pytest.raises(ValidationError):
            CampaignTask(**make_task(idempotency_key="x" * 257))

    def test_attempt_count_non_negative(self):
        """attempt_count must be >= 0."""
        with pytest.raises(ValidationError):
            CampaignTask(**make_task(attempt_count=-1))

    def test_attempt_count_zero_default(self):
        """attempt_count defaults to 0."""
        task = CampaignTask(**make_task())
        assert task.attempt_count == 0

    def test_extra_fields_forbidden(self):
        """Extra fields should be forbidden."""
        with pytest.raises(ValidationError):
            CampaignTask(**make_task(unknown_field="value"))

    def test_status_default_pending(self):
        """Default status is PENDING."""
        task = CampaignTask(**make_task())
        assert task.status == TaskStatus.PENDING


class TestCampaignTaskOptionalFields:
    """Test optional field behavior."""

    def test_step_id_optional(self):
        """step_id can be None for single-step campaigns."""
        task = CampaignTask(**make_task(step_id=None))
        assert task.step_id is None

    def test_step_id_set(self):
        """step_id can be a UUID."""
        step_id = uuid4()
        task = CampaignTask(**make_task(step_id=step_id))
        assert task.step_id == step_id

    def test_channel_used_max_length(self):
        """channel_used over 32 chars should fail."""
        with pytest.raises(ValidationError):
            CampaignTask(**make_task(channel_used="x" * 33))

    def test_external_message_id_max_length(self):
        """external_message_id over 255 chars should fail."""
        with pytest.raises(ValidationError):
            CampaignTask(**make_task(external_message_id="x" * 256))

    def test_last_error_max_length(self):
        """last_error over 2000 chars should fail."""
        with pytest.raises(ValidationError):
            CampaignTask(**make_task(last_error="x" * 2001))

    def test_compliance_check_optional(self):
        """compliance_check defaults to None."""
        task = CampaignTask(**make_task())
        assert task.compliance_check is None

    def test_compliance_check_dict(self):
        """compliance_check can be a dict."""
        cc = {"failed_policy": "waba_24h", "reason": "outside window"}
        task = CampaignTask(**make_task(compliance_check=cc))
        assert task.compliance_check == cc


class TestCampaignTaskStatuses:
    """Test all TaskStatus values are accepted."""

    @pytest.mark.parametrize("status", list(TaskStatus))
    def test_all_statuses_valid(self, status):
        """All TaskStatus enum values should be accepted."""
        task = CampaignTask(**make_task(status=status))
        assert task.status == status
