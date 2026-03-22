"""Tests for nurture metrics repository and endpoint."""
import pytest
from uuid import uuid4


# --- NurtureMetricsRepository unit tests ---


class TestNurtureMetricsRepository:
    """Tests for NurtureMetricsRepository queries."""

    @pytest.mark.skip(reason="Stub -- implement after Task 1")
    def test_count_new_mqls_returns_distinct_profiles(self):
        """count_new_mqls should count DISTINCT profile_ids that transitioned to MQL."""
        pass

    @pytest.mark.skip(reason="Stub -- implement after Task 1")
    def test_count_new_mqls_filters_by_tenant(self):
        """count_new_mqls must filter by tenant_id (multi-tenant safety)."""
        pass

    @pytest.mark.skip(reason="Stub -- implement after Task 1")
    def test_count_new_mqls_filters_by_date_range(self):
        """Only MQL transitions within start_date..end_date are counted."""
        pass

    @pytest.mark.skip(reason="Stub -- implement after Task 1")
    def test_get_mql_sources_groups_by_lead_source(self):
        """get_mql_sources returns dict mapping lead_source -> count."""
        pass

    @pytest.mark.skip(reason="Stub -- implement after Task 1")
    def test_count_email_events_returns_opens_and_clicks(self):
        """count_email_events returns {'emails_sent': N, 'opens': N, 'clicks': N}."""
        pass


# --- /metrics/nurturing endpoint integration tests ---


class TestNurtureEndpoint:
    """Integration tests for GET /metrics/nurturing."""

    @pytest.mark.skip(reason="Stub -- implement after Task 2")
    def test_nurture_endpoint_returns_nurture_detail_dto(self):
        """GET /metrics/nurturing should return NurtureDetailDTO shape."""
        pass

    @pytest.mark.skip(reason="Stub -- implement after Task 2")
    def test_nurture_endpoint_requires_auth(self):
        """GET /metrics/nurturing without auth returns 401."""
        pass
