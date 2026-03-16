import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4


class TestCaptureMetricsRepository:
    """Tests for CRM-based lead count aggregation."""

    @pytest.mark.skip(reason="Wave 0 stub -- implement after Task 1")
    def test_count_leads_by_source_filters_by_tenant(self):
        """Lead counts must be isolated by tenant_id."""
        pass

    @pytest.mark.skip(reason="Wave 0 stub -- implement after Task 1")
    def test_count_leads_by_source_filters_by_date_range(self):
        """Only profiles with first_seen_at in range are counted."""
        pass

    @pytest.mark.skip(reason="Wave 0 stub -- implement after Task 1")
    def test_count_leads_by_source_excludes_soft_deleted(self):
        """Profiles with deleted_at set are excluded."""
        pass

    @pytest.mark.skip(reason="Wave 0 stub -- implement after Task 1")
    def test_count_leads_by_source_groups_by_lead_source(self):
        """Returns dict mapping lead_source slug to count."""
        pass
