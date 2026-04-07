"""Tests for subscription new vs renewal split logic.

VEN-03: Subscription offers show new_subscriptions vs renewals split.
Wave 0 stubs -- will fail until 08-01 creates production code.
"""


class TestSubscriptionLabels:
    """get_subscription_labels returns correct labels by pricing_type and offer_type."""

    def test_subscription_type_labels(self):
        from src.modules.analytics.application.dto.sales_dto import (
            get_subscription_labels,
        )

        labels = get_subscription_labels("subscription", "self_paced_course")
        assert labels is not None
        assert "new_label" in labels
        assert "renewal_label" in labels
        assert labels["new_label"] == "nuevas suscripciones"
        assert labels["renewal_label"] == "renovaciones"

    def test_payment_plan_labels(self):
        from src.modules.analytics.application.dto.sales_dto import (
            get_subscription_labels,
        )

        labels = get_subscription_labels("payment_plan", "self_paced_course")
        assert labels is not None
        assert labels["new_label"] == "nuevos planes"
        assert labels["renewal_label"] == "cuotas cobradas"

    def test_one_time_returns_none(self):
        from src.modules.analytics.application.dto.sales_dto import (
            get_subscription_labels,
        )

        assert get_subscription_labels("one_time", "self_paced_course") is None

    def test_recurring_service_labels(self):
        """Recurring service types (monthly_retainer, etc.) use 'contratos' labels."""
        from src.modules.analytics.application.dto.sales_dto import (
            get_subscription_labels,
        )

        labels = get_subscription_labels("subscription", "monthly_retainer")
        assert labels is not None
        assert "contratos" in labels["new_label"]

    def test_productized_service_labels(self):
        from src.modules.analytics.application.dto.sales_dto import (
            get_subscription_labels,
        )

        labels = get_subscription_labels("subscription", "productized_service")
        assert labels is not None
        assert "contratos" in labels["new_label"]
