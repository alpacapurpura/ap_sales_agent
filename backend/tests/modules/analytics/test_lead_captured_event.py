import pytest
from uuid import uuid4


class TestLeadCapturedEvent:
    """Tests for LeadCapturedEvent creation and emission."""

    @pytest.mark.skip(reason="Wave 0 stub -- implement after Task 1")
    def test_event_create_sets_event_name(self):
        """LeadCapturedEvent.create() sets event_name='lead_captured'."""
        pass

    @pytest.mark.skip(reason="Wave 0 stub -- implement after Task 1")
    def test_event_payload_contains_required_fields(self):
        """Payload must include profile_id, channel_slug, extracted_field."""
        pass

    @pytest.mark.skip(reason="Wave 0 stub -- implement after Task 2")
    def test_channel_type_to_capture_slug_mapping(self):
        """CHANNEL_TYPE_TO_CAPTURE_SLUG maps instagram->ig-dm, facebook->fb-messenger, etc."""
        pass
