"""Tests for Mailerlite webhook endpoint and ETL backup sync."""
import pytest


class TestMailerliteWebhook:
    """Tests for POST /webhooks/mailerlite/{tenant_id}."""

    @pytest.mark.skip(reason="Stub -- implement after Task 2")
    def test_webhook_creates_journey_event_on_open(self):
        """campaign.open event creates journey_event with event_name='email_opened'."""
        pass

    @pytest.mark.skip(reason="Stub -- implement after Task 2")
    def test_webhook_creates_journey_event_on_click(self):
        """campaign.click event creates journey_event with event_name='email_clicked'."""
        pass

    @pytest.mark.skip(reason="Stub -- implement after Task 2")
    def test_webhook_triggers_score_recalculation(self):
        """Webhook calls lifecycle_service.recalculate_score() after creating event."""
        pass

    @pytest.mark.skip(reason="Stub -- implement after Task 2")
    def test_webhook_ignores_unknown_subscriber(self):
        """Webhook returns 'ignored' for email not matching any customer_profile."""
        pass

    @pytest.mark.skip(reason="Stub -- implement after Task 2")
    def test_webhook_ignores_unsupported_event_type(self):
        """Webhook returns 'ignored' for non-open/click event types."""
        pass


class TestMailerliteEtlSync:
    """Tests for the 6-hour Mailerlite ETL backup sync ARQ task."""

    @pytest.mark.skip(reason="Stub -- implement after Task 2")
    def test_etl_sync_creates_missing_journey_events(self):
        """ETL sync creates journey_events for campaigns not yet recorded."""
        pass

    @pytest.mark.skip(reason="Stub -- implement after Task 2")
    def test_etl_sync_skips_already_recorded_events(self):
        """ETL sync is idempotent -- doesn't duplicate existing journey_events."""
        pass
