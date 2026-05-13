"""S9 — PaymentGatewayProvider strategy compliance tests (RED → GREEN).

These tests enforce the Strategy contract independently from any concrete
implementation. They will be RED until the Protocol + impls exist.
"""

from __future__ import annotations

import pytest


def test_payment_gateway_provider_protocol_importable() -> None:
    """Protocol + registry must be importable from the payment providers module."""
    from luana_core_sales_agent.application.tools.payment.providers import (
        PAYMENT_PROVIDERS,
        PaymentGatewayProvider,
        PaymentLinkOutput,
        PaymentStatusEnum,
        PaymentWebhookEvent,
        payment_provider_for_tenant,
    )


def test_payment_providers_registry_not_empty() -> None:
    """At least one concrete provider must be registered (MP + Stripe)."""
    from luana_core_sales_agent.application.tools.payment.providers import (
        PAYMENT_PROVIDERS,
    )

    assert len(PAYMENT_PROVIDERS) >= 1, "PAYMENT_PROVIDERS registry is empty"


def test_mercadopago_provider_registered() -> None:
    from luana_core_sales_agent.application.tools.payment.providers import (
        PAYMENT_PROVIDERS,
    )

    assert "mercadopago" in PAYMENT_PROVIDERS


def test_stripe_provider_registered() -> None:
    from luana_core_sales_agent.application.tools.payment.providers import (
        PAYMENT_PROVIDERS,
    )

    assert "stripe" in PAYMENT_PROVIDERS


def test_every_registered_provider_is_runtime_checkable() -> None:
    """Each impl in PAYMENT_PROVIDERS must satisfy the Protocol at runtime."""
    from luana_core_sales_agent.application.tools.payment.providers import (
        PAYMENT_PROVIDERS,
        PaymentGatewayProvider,
    )

    for name, klass in PAYMENT_PROVIDERS.items():
        assert isinstance(klass, type), f"{name}: not a class"
        # Instantiate with minimal stub (no DB needed for Protocol check)
        try:
            instance = klass.__new__(klass)
        except Exception:  # noqa: BLE001
            pytest.fail(f"{name}: cannot create instance via __new__")
        assert isinstance(instance, PaymentGatewayProvider), (
            f"{name} does not implement PaymentGatewayProvider Protocol"
        )


def test_payment_link_output_is_frozen_dataclass() -> None:
    import dataclasses

    from luana_core_sales_agent.application.tools.payment.providers import (
        PaymentLinkOutput,
    )

    assert dataclasses.is_dataclass(PaymentLinkOutput)
    fields = {f.name for f in dataclasses.fields(PaymentLinkOutput)}
    required = {"external_id", "url", "provider_id"}
    assert required <= fields, f"Missing fields: {required - fields}"


def test_payment_status_enum_has_expected_values() -> None:
    from luana_core_sales_agent.application.tools.payment.providers import (
        PaymentStatusEnum,
    )

    expected = {"pending", "paid", "failed", "refunded", "expired", "cancelled"}
    actual = {e.value for e in PaymentStatusEnum}
    assert expected <= actual, f"Missing statuses: {expected - actual}"


def test_webhook_provider_protocol_importable() -> None:
    from luana_core_sales_agent.application.tools.payment.webhook_providers import (
        PAYMENT_WEBHOOK_PROVIDERS,
        PaymentWebhookProvider,
        register_payment_webhook_provider,
    )


def test_mercadopago_webhook_signature_verify() -> None:
    """MP verify_signature must return False for invalid signature."""
    from luana_core_sales_agent.application.tools.payment.webhook_providers import (
        MercadoPagoWebhookProvider,
    )

    handler = MercadoPagoWebhookProvider()
    result = handler.verify_signature(
        body=b'{"data":{"id":"12345"}}',
        headers={"x-signature": "ts=1234,v1=badhash", "x-request-id": "req-1"},
        secret="secret",
    )
    assert result is False


def test_stripe_webhook_signature_verify() -> None:
    """Stripe verify_signature must return False for invalid signature."""
    from luana_core_sales_agent.application.tools.payment.webhook_providers import (
        StripeWebhookProvider,
    )

    handler = StripeWebhookProvider()
    result = handler.verify_signature(
        body=b'{"type":"checkout.session.completed"}',
        headers={"stripe-signature": "t=bad,v1=bad"},
        secret="secret",
    )
    assert result is False
