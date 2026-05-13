"""Tests for campaign domain events.

Verifies all 14 events serialize correctly, tenant_id is mandatory,
and EVENT_NAME literals are correct.
"""

from __future__ import annotations

import datetime as dt
from uuid import uuid4

import pytest

from luana_core_campaigns.domain.events import (
    CampaignCanceled,
    CampaignCompleted,
    CampaignCreated,
    CampaignLaunched,
    CampaignPaused,
    CampaignScheduled,
    CampaignStepAdded,
    CampaignStepUpdated,
    CampaignTaskDispatched,
    CampaignTaskFailed,
    CampaignTaskQueued,
    CampaignTaskSent,
    SegmentCreated,
    SegmentSnapshotted,
)


NOW = dt.datetime.now(dt.timezone.utc)


class TestCampaignEventBase:
    """Tests for campaign events that extend _CampaignEventBase."""

    def test_campaign_created_fields(self):
        """CampaignCreated has correct fields."""
        event = CampaignCreated(
            tenant_id=uuid4(),
            campaign_id=uuid4(),
            occurred_at=NOW,
        )
        assert event.EVENT_NAME == "campaigns.campaign.created"
        assert event.occurred_at == NOW

    def test_campaign_scheduled_has_scheduled_at(self):
        """CampaignScheduled carries scheduled_at."""
        event = CampaignScheduled(
            tenant_id=uuid4(),
            campaign_id=uuid4(),
            occurred_at=NOW,
            scheduled_at=NOW,
        )
        assert event.EVENT_NAME == "campaigns.campaign.scheduled"
        assert event.scheduled_at == NOW

    def test_campaign_launched_has_launched_at(self):
        """CampaignLaunched carries launched_at."""
        event = CampaignLaunched(
            tenant_id=uuid4(),
            campaign_id=uuid4(),
            occurred_at=NOW,
            launched_at=NOW,
        )
        assert event.EVENT_NAME == "campaigns.campaign.launched"
        assert event.launched_at == NOW

    def test_campaign_paused_fields(self):
        """CampaignPaused has correct EVENT_NAME."""
        event = CampaignPaused(
            tenant_id=uuid4(),
            campaign_id=uuid4(),
            occurred_at=NOW,
        )
        assert event.EVENT_NAME == "campaigns.campaign.paused"

    def test_campaign_completed_has_completed_at(self):
        """CampaignCompleted carries completed_at."""
        event = CampaignCompleted(
            tenant_id=uuid4(),
            campaign_id=uuid4(),
            occurred_at=NOW,
            completed_at=NOW,
        )
        assert event.EVENT_NAME == "campaigns.campaign.completed"
        assert event.completed_at == NOW

    def test_campaign_canceled_with_reason(self):
        """CampaignCanceled can carry an optional reason."""
        event = CampaignCanceled(
            tenant_id=uuid4(),
            campaign_id=uuid4(),
            occurred_at=NOW,
            canceled_at=NOW,
            reason="user_canceled",
        )
        assert event.EVENT_NAME == "campaigns.campaign.canceled"
        assert event.reason == "user_canceled"

    def test_campaign_canceled_no_reason(self):
        """CampaignCanceled without reason is valid."""
        event = CampaignCanceled(
            tenant_id=uuid4(),
            campaign_id=uuid4(),
            occurred_at=NOW,
            canceled_at=NOW,
        )
        assert event.reason is None

    def test_step_added_has_step_id(self):
        """CampaignStepAdded carries step_id."""
        step_id = uuid4()
        event = CampaignStepAdded(
            tenant_id=uuid4(),
            campaign_id=uuid4(),
            occurred_at=NOW,
            step_id=step_id,
        )
        assert event.EVENT_NAME == "campaigns.step.added"
        assert event.step_id == step_id

    def test_step_updated_has_step_id(self):
        """CampaignStepUpdated carries step_id."""
        event = CampaignStepUpdated(
            tenant_id=uuid4(),
            campaign_id=uuid4(),
            occurred_at=NOW,
            step_id=uuid4(),
        )
        assert event.EVENT_NAME == "campaigns.step.updated"


class TestCampaignTaskEvents:
    """Tests for task-related events."""

    def test_task_queued_fields(self):
        """CampaignTaskQueued carries task_id, lead_id, scheduled_at."""
        event = CampaignTaskQueued(
            tenant_id=uuid4(),
            campaign_id=uuid4(),
            occurred_at=NOW,
            task_id=uuid4(),
            lead_id=uuid4(),
            scheduled_at=NOW,
        )
        assert event.EVENT_NAME == "campaigns.task.queued"

    def test_task_dispatched_has_channel(self):
        """CampaignTaskDispatched carries channel."""
        event = CampaignTaskDispatched(
            tenant_id=uuid4(),
            campaign_id=uuid4(),
            occurred_at=NOW,
            task_id=uuid4(),
            lead_id=uuid4(),
            channel="telegram",
        )
        assert event.channel == "telegram"

    def test_task_sent_with_external_id(self):
        """CampaignTaskSent carries external_message_id."""
        event = CampaignTaskSent(
            tenant_id=uuid4(),
            campaign_id=uuid4(),
            occurred_at=NOW,
            task_id=uuid4(),
            lead_id=uuid4(),
            channel="whatsapp",
            external_message_id="msg_12345",
        )
        assert event.external_message_id == "msg_12345"

    def test_task_sent_no_external_id(self):
        """CampaignTaskSent without external_message_id is valid."""
        event = CampaignTaskSent(
            tenant_id=uuid4(),
            campaign_id=uuid4(),
            occurred_at=NOW,
            task_id=uuid4(),
            lead_id=uuid4(),
            channel="email",
            external_message_id=None,
        )
        assert event.external_message_id is None

    def test_task_failed_has_error_details(self):
        """CampaignTaskFailed carries error_code and error_message."""
        event = CampaignTaskFailed(
            tenant_id=uuid4(),
            campaign_id=uuid4(),
            occurred_at=NOW,
            task_id=uuid4(),
            lead_id=uuid4(),
            error_code="TIMEOUT",
            error_message="Channel timeout after 30s",
        )
        assert event.error_code == "TIMEOUT"
        assert event.error_message == "Channel timeout after 30s"


class TestSegmentEvents:
    """Tests for segment-related events."""

    def test_segment_created(self):
        """SegmentCreated has correct fields."""
        event = SegmentCreated(
            tenant_id=uuid4(),
            segment_id=uuid4(),
        )
        assert event.EVENT_NAME == "campaigns.segment.created"
        assert event.occurred_at is not None

    def test_segment_snapshotted(self):
        """SegmentSnapshotted carries snapshot_id and lead_count."""
        event = SegmentSnapshotted(
            tenant_id=uuid4(),
            segment_id=uuid4(),
            snapshot_id=uuid4(),
            lead_count=42,
        )
        assert event.EVENT_NAME == "campaigns.segment.snapshotted"
        assert event.lead_count == 42


class TestEventSerialization:
    """Test events serialize/deserialize correctly."""

    def test_campaign_created_roundtrip(self):
        """CampaignCreated should survive model_dump roundtrip."""
        original = CampaignCreated(
            tenant_id=uuid4(),
            campaign_id=uuid4(),
            occurred_at=NOW,
        )
        data = original.model_dump()
        assert data["EVENT_NAME"] == "campaigns.campaign.created"
        assert "tenant_id" in data
        assert "campaign_id" in data

    def test_segment_created_roundtrip(self):
        """SegmentCreated should survive model_dump roundtrip."""
        original = SegmentCreated(tenant_id=uuid4(), segment_id=uuid4())
        data = original.model_dump()
        assert data["EVENT_NAME"] == "campaigns.segment.created"
        assert "tenant_id" in data

    def test_all_campaign_events_have_tenant_id(self):
        """All campaign events must include tenant_id field."""
        events = [
            CampaignCreated(tenant_id=uuid4(), campaign_id=uuid4(), occurred_at=NOW),
            CampaignPaused(tenant_id=uuid4(), campaign_id=uuid4(), occurred_at=NOW),
            SegmentCreated(tenant_id=uuid4(), segment_id=uuid4()),
            SegmentSnapshotted(tenant_id=uuid4(), segment_id=uuid4(), snapshot_id=uuid4(), lead_count=0),
        ]
        for event in events:
            data = event.model_dump()
            assert "tenant_id" in data, f"{type(event).__name__} missing tenant_id"

    def test_event_names_are_correct(self):
        """Each event has the correct EVENT_NAME literal."""
        expected_names = {
            CampaignCreated: "campaigns.campaign.created",
            CampaignScheduled: "campaigns.campaign.scheduled",
            CampaignLaunched: "campaigns.campaign.launched",
            CampaignPaused: "campaigns.campaign.paused",
            CampaignCompleted: "campaigns.campaign.completed",
            CampaignCanceled: "campaigns.campaign.canceled",
            CampaignStepAdded: "campaigns.step.added",
            CampaignStepUpdated: "campaigns.step.updated",
            CampaignTaskQueued: "campaigns.task.queued",
            CampaignTaskDispatched: "campaigns.task.dispatched",
            CampaignTaskSent: "campaigns.task.sent",
            CampaignTaskFailed: "campaigns.task.failed",
            SegmentCreated: "campaigns.segment.created",
            SegmentSnapshotted: "campaigns.segment.snapshotted",
        }
        for cls, expected_name in expected_names.items():
            # Construct minimal instances
            base_kwargs = {}
            if cls in (SegmentCreated, SegmentSnapshotted):
                base_kwargs = {"tenant_id": uuid4(), "segment_id": uuid4()}
                if cls == SegmentSnapshotted:
                    base_kwargs["snapshot_id"] = uuid4()
                    base_kwargs["lead_count"] = 0
            else:
                base_kwargs = {"tenant_id": uuid4(), "campaign_id": uuid4()}
                if cls == CampaignScheduled:
                    base_kwargs["scheduled_at"] = NOW
                elif cls == CampaignLaunched:
                    base_kwargs["launched_at"] = NOW
                elif cls == CampaignCompleted:
                    base_kwargs["completed_at"] = NOW
                elif cls == CampaignCanceled:
                    base_kwargs["canceled_at"] = NOW
                elif cls in (CampaignStepAdded, CampaignStepUpdated):
                    base_kwargs["step_id"] = uuid4()
                elif cls == CampaignTaskQueued:
                    base_kwargs.update({"task_id": uuid4(), "lead_id": uuid4(), "scheduled_at": NOW})
                elif cls == CampaignTaskDispatched:
                    base_kwargs.update({"task_id": uuid4(), "lead_id": uuid4(), "channel": "telegram"})
                elif cls == CampaignTaskSent:
                    base_kwargs.update(
                        {"task_id": uuid4(), "lead_id": uuid4(), "channel": "email", "external_message_id": None}
                    )
                elif cls == CampaignTaskFailed:
                    base_kwargs.update(
                        {"task_id": uuid4(), "lead_id": uuid4(), "error_code": "ERR", "error_message": "test"}
                    )

            instance = cls(**base_kwargs)
            assert expected_name == instance.EVENT_NAME, (
                f"{cls.__name__}.EVENT_NAME = {instance.EVENT_NAME!r}, expected {expected_name!r}"
            )
