"""Tests for GET /metrics/sales endpoint and SalesMetricsRepository.

VEN-02: Backend endpoint /metrics/sales with revenue tracking.
"""


class TestSalesMetricsRepository:
    """SalesMetricsRepository uses SQLAlchemy 2.0 syntax."""

    def test_repository_class_exists(self):
        from src.modules.analytics.infrastructure.repositories.sales_metrics_repository import (
            SalesMetricsRepository,
        )

        assert SalesMetricsRepository is not None

    def test_repository_has_get_sales_summary(self):
        from src.modules.analytics.infrastructure.repositories.sales_metrics_repository import (
            SalesMetricsRepository,
        )

        assert hasattr(SalesMetricsRepository, "get_sales_summary")

    def test_repository_has_get_total_conversion_customers(self):
        from src.modules.analytics.infrastructure.repositories.sales_metrics_repository import (
            SalesMetricsRepository,
        )

        assert hasattr(SalesMetricsRepository, "get_total_conversion_customers")

    def test_repository_has_get_total_sql_count(self):
        from src.modules.analytics.infrastructure.repositories.sales_metrics_repository import (
            SalesMetricsRepository,
        )

        assert hasattr(SalesMetricsRepository, "get_total_sql_count")

    def test_repository_uses_select_syntax(self):
        """SalesMetricsRepository must use select() not db.query()."""
        import inspect

        from src.modules.analytics.infrastructure.repositories import (
            sales_metrics_repository,
        )

        source = inspect.getsource(sales_metrics_repository)
        assert "db.query" not in source, "Must use SQLAlchemy 2.0 select() syntax"
        assert "select(" in source


class TestSalesEndpoint:
    """GET /metrics/sales endpoint wiring tests."""

    def test_sales_stage_service_has_get_metrics(self):
        from src.modules.analytics.application.services.stage_services.sales_stage import (
            SalesStageService,
        )

        assert hasattr(SalesStageService, "get_metrics")

    def test_metrics_service_accepts_offer_port(self):
        """MetricsService __init__ accepts offer_port parameter."""
        import inspect

        from src.modules.analytics.application.services.metrics_service import (
            MetricsService,
        )

        sig = inspect.signature(MetricsService.__init__)
        assert "offer_port" in sig.parameters

    def test_endpoint_imports_sales_detail_dto(self):
        """metrics.py imports SalesDetailDTO for response_model."""
        import inspect

        from src.modules.analytics.api import metrics

        source = inspect.getsource(metrics)
        assert "SalesDetailDTO" in source
        assert "OfferReadPortImpl" in source

    def test_no_offer_domain_import_in_analytics(self):
        """Analytics module must NOT import from offer.domain."""
        import inspect

        from src.modules.analytics.application.services import metrics_service

        source = inspect.getsource(metrics_service)
        assert "from src.modules.offer.domain" not in source
