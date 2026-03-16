"""Tests for evangelization metrics endpoint and DTO assembly."""
import pytest


class TestEvangelizationMetrics:
    """Evangelization metrics endpoint tests."""

    @pytest.mark.skip(reason="Wave 0 stub — implement after Plan 10-02 Task 2")
    def test_get_evangelization_metrics_returns_dto(self):
        """GET /metrics/evangelization returns EvangelizationDetailDTO."""
        pass

    @pytest.mark.skip(reason="Wave 0 stub — implement after Plan 10-02 Task 2")
    def test_evangelization_metrics_includes_header_kpis(self):
        """Response includes k_factor, referral_conversions, nps_score, referral_revenue, active_evangelists."""
        pass

    @pytest.mark.skip(reason="Wave 0 stub — implement after Plan 10-02 Task 1")
    def test_evangelization_repository_queries_with_tenant_isolation(self):
        """All repository queries filter by tenant_id."""
        pass

    @pytest.mark.skip(reason="Wave 0 stub — implement after Plan 10-02 Task 2")
    def test_bottleneck_detection_low_k_factor(self):
        """K-Factor < 0.5 triggers critical bottleneck, < 1.0 triggers warning."""
        pass

    @pytest.mark.skip(reason="Wave 0 stub — implement after Plan 10-02 Task 2")
    def test_bottleneck_detection_low_nps_response_rate(self):
        """NPS response rate < 15% triggers critical, < 30% triggers warning."""
        pass
