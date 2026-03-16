"""Tests for GET /metrics/sales endpoint.

VEN-02: /metrics/sales returns grouped revenue with CONVERSION/EXPANSION split.
Wave 0 stubs -- will fail until 08-01 creates production code.
"""
import pytest


class TestSalesEndpointRegistration:
    """Verify the /metrics/sales route is registered."""

    def test_sales_route_exists(self):
        """GET /metrics/sales route is registered on the analytics router."""
        from src.modules.analytics.api.metrics import router
        routes = [r.path for r in router.routes]
        assert "/sales" in routes or any("/sales" in str(r.path) for r in router.routes), (
            "GET /metrics/sales route not found in analytics router"
        )

    def test_sales_endpoint_response_model(self):
        """GET /metrics/sales uses SalesDetailDTO as response_model."""
        from src.modules.analytics.api.metrics import router
        for route in router.routes:
            if hasattr(route, 'path') and "/sales" in str(route.path):
                assert route.response_model is not None, (
                    "GET /metrics/sales must have a response_model"
                )
                break


class TestMetricsServiceSalesMethod:
    """Verify MetricsService has get_sales_metrics method."""

    def test_metrics_service_has_sales_method(self):
        from src.modules.analytics.application.services.metrics_service import MetricsService
        assert hasattr(MetricsService, 'get_sales_metrics'), (
            "MetricsService must have get_sales_metrics method"
        )

    def test_metrics_service_accepts_offer_port(self):
        """MetricsService.__init__ accepts offer_port parameter."""
        import inspect
        from src.modules.analytics.application.services.metrics_service import MetricsService
        sig = inspect.signature(MetricsService.__init__)
        assert 'offer_port' in sig.parameters, (
            "MetricsService.__init__ must accept offer_port parameter"
        )
