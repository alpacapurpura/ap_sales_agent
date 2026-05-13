"""Payment lifecycle tools — S9.

Three tools:
- tool_create_payment_link: create a provider payment link for a lead's offer.
- tool_verify_payment_status: poll provider for current payment status.
- tool_grant_access: saga — deliver digital access after confirmed payment.

All follow the dict-style tool signature:
    def tool_xxx(state: dict, db: Session | None) -> dict

No @tool decorator. Mirrors scheduling/tools.py pattern.
"""

from __future__ import annotations

import contextlib
from typing import Any
from uuid import UUID

import structlog
from luana_core_events.outbox.application.event_bus_adapter import (
    adapter_bus as EventBus,  # noqa: N812
)
from luana_core_platform.domain.events import AccessGrantedEvent, PaymentLinkCreatedEvent
from luana_core_sales_agent.application.services.payment_state_service import (
    PaymentEntryStatus,
    PaymentStateService,
)
from luana_core_sales_agent.application.tools.payment.providers import (
    payment_provider_for_tenant,
)
from luana_core_sales_agent.infrastructure.models.payment_grant_audit_model import (
    PaymentGrantAuditModel,
)
from luana_core_sales_agent.infrastructure.models.payment_link_model import (
    PaymentLinkModel,
)
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

logger = structlog.get_logger()


# ─────────────────────────────────────────────────────────────
# Tool registry (mirrors SCHEDULING_TOOL_REGISTRY pattern)
# ─────────────────────────────────────────────────────────────

# Defined here (not at module bottom) so imports of PAYMENT_TOOL_REGISTRY
# work without all tool functions being defined yet.
# Registry is populated at the module bottom after all tool definitions.


# ─────────────────────────────────────────────────────────────
# Stubs — overridable in tests
# ─────────────────────────────────────────────────────────────


def access_provider_for_offer(offer_id: UUID) -> Any:  # noqa: ANN401
    """Return a stub AccessProvider for the given offer.

    Replaced by concrete EmailAccessProvider/ManychatAccessProvider adapters
    once the connections module exposes them (post-S9 DEFERRED).
    """
    from unittest.mock import MagicMock

    stub = MagicMock()
    stub.channel = "email"
    stub.deliver.return_value = {"channel": "email", "delivered": True}
    return stub


# ─────────────────────────────────────────────────────────────
# tool_create_payment_link
# ─────────────────────────────────────────────────────────────


def tool_create_payment_link(state: dict, db: Any) -> dict:  # noqa: ANN401, PLR0911
    """Create a provider payment link for the lead's active offer.

    Idempotent: re-invoking in the same turn reuses an existing PENDING link.
    Currency comes from ``state["active_product"]["currency"]`` (offer SSoT).
    """
    if db is None:
        return {"status": "error", "message": "No database session available"}

    try:
        tenant_id = UUID(state["tenant_id"])
        lead_id = UUID(state["lead_id"])
    except (KeyError, ValueError) as exc:
        return {"status": "error", "message": f"Invalid state IDs: {exc}"}

    product = state.get("active_product") or {}
    amount = product.get("pricing_amount")
    currency = product.get("currency", "USD")
    offer_id_str = product.get("id")

    if not amount:
        return {"status": "error", "message": "No pricing_amount on active_product"}

    offer_id = UUID(offer_id_str) if offer_id_str else None

    # Idempotency check — reuse if pending link exists
    state_svc = PaymentStateService(db)
    if offer_id:
        existing = state_svc.find_pending_link(tenant_id, lead_id, offer_id)
        if existing is None:
            # Also check by provider in case offer_id not indexed
            existing = state_svc.find_pending_link(tenant_id, lead_id)
        if existing:
            return {
                "status": "success",
                "url": existing.url,
                "external_id": existing.external_id,
                "provider_id": existing.provider_id,
                "reused": True,
            }

    # Resolve provider
    provider = payment_provider_for_tenant(db, tenant_id)

    metadata: dict = {
        "tenant_id": str(tenant_id),
        "lead_id": str(lead_id),
        "offer_id": str(offer_id) if offer_id else "",
        "offer_title": product.get("title", "Oferta"),
    }

    try:
        link_output = provider.create_payment_link(
            tenant_id=tenant_id,
            lead_id=lead_id,
            offer_id=offer_id or UUID(int=0),
            amount=float(amount),
            currency=str(currency),
            metadata=metadata,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("payment_link_create_failed", error=str(exc), exc_info=True)
        return {"status": "error", "message": f"Provider error: {exc}"}

    # Persist to DB
    payment_row = PaymentLinkModel(
        tenant_id=tenant_id,
        lead_id=lead_id,
        offer_id=offer_id or UUID(int=0),
        provider=provider.provider_id,
        external_id=link_output.external_id,
        url=link_output.url,
        amount=amount,
        currency=str(currency),
        status="pending",
        metadata_=metadata,
    )
    db.add(payment_row)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        return {"status": "error", "message": "Duplicate payment link (IntegrityError)"}

    # Append to JSONB payment_state
    with contextlib.suppress(LookupError):
        state_svc.append_link(tenant_id, lead_id, link_output, payment_id=payment_row.id)

    # Publish event
    with contextlib.suppress(Exception):
        EventBus.publish(
            PaymentLinkCreatedEvent.create(
                tenant_id=tenant_id,
                lead_id=lead_id,
                external_id=link_output.external_id,
                provider_id=provider.provider_id,
                url=link_output.url,
                amount=float(amount),
                currency=str(currency),
            ),
            session=None,
        )

    db.commit()

    return {
        "status": "success",
        "url": link_output.url,
        "external_id": link_output.external_id,
        "provider_id": provider.provider_id,
        "reused": False,
    }


# ─────────────────────────────────────────────────────────────
# tool_verify_payment_status
# ─────────────────────────────────────────────────────────────


def tool_verify_payment_status(state: dict, db: Any) -> dict:  # noqa: ANN401
    """Poll provider for current payment status and update local DB.

    On PAID: updates PaymentLinkModel.status → "paid".
    """
    if db is None:
        return {"status": "error", "message": "No database session available"}

    try:
        tenant_id = UUID(state["tenant_id"])
        lead_id = UUID(state["lead_id"])
        payment_id_str = (state.get("_tool_args") or {}).get("payment_id")
        if not payment_id_str:
            return {"status": "error", "message": "payment_id required in _tool_args"}
        payment_id = UUID(payment_id_str)
    except (KeyError, ValueError) as exc:
        return {"status": "error", "message": f"Invalid state: {exc}"}

    link = db.execute(
        select(PaymentLinkModel).where(
            PaymentLinkModel.id == payment_id,
            PaymentLinkModel.tenant_id == tenant_id,
        )
    ).scalar_one_or_none()

    if link is None:
        return {"status": "error", "message": f"PaymentLink {payment_id} not found"}

    # Poll provider
    try:
        provider = payment_provider_for_tenant(db, tenant_id)
        remote_status = provider.verify_payment(link.external_id)
    except Exception as exc:  # noqa: BLE001
        logger.warning("payment_verify_provider_error", error=str(exc))
        return {"status": "success", "payment_status": link.status, "source": "local"}

    # Update local if changed
    if remote_status.value != link.status:
        link.status = remote_status.value
        db.commit()
        # Update JSONB state
        state_svc = PaymentStateService(db)
        with contextlib.suppress(Exception):
            state_svc.update_status_by_external_id(
                tenant_id,
                lead_id,
                link.external_id,
                status=PaymentEntryStatus(remote_status.value),
            )

    return {
        "status": "success",
        "payment_status": remote_status.value,
        "payment_id": str(payment_id),
        "source": "provider",
    }


# ─────────────────────────────────────────────────────────────
# tool_grant_access — saga
# ─────────────────────────────────────────────────────────────


def tool_grant_access(state: dict, db: Any) -> dict:  # noqa: ANN401, PLR0911
    """Grant digital access to lead after confirmed payment.

    Saga pattern:
    1. Gate: payment must be PAID.
    2. Idempotency: check payment_grant_audit UNIQUE constraint.
    3. Deliver via AccessProvider.
    4. Persist audit row (IntegrityError = duplicate → return existing).
    5. Publish AccessGrantedEvent.
    """
    if db is None:
        return {"status": "error", "message": "No database session available"}

    try:
        tenant_id = UUID(state["tenant_id"])
        lead_id = UUID(state["lead_id"])
        payment_id_str = (state.get("_tool_args") or {}).get("payment_id")
        if not payment_id_str:
            return {"status": "error", "message": "payment_id required in _tool_args"}
        payment_id = UUID(payment_id_str)
        offer_id = UUID((state.get("active_product") or {}).get("id", str(UUID(int=0))))
    except (KeyError, ValueError) as exc:
        return {"status": "error", "message": f"Invalid state: {exc}"}

    # 1. Gate: payment must be PAID
    link = db.execute(
        select(PaymentLinkModel).where(
            PaymentLinkModel.id == payment_id,
            PaymentLinkModel.tenant_id == tenant_id,
        )
    ).scalar_one_or_none()

    if link is None:
        return {"status": "error", "message": f"PaymentLink {payment_id} not found"}

    if link.status != "paid":
        return {
            "status": "success",
            "granted": False,
            "reason": f"payment_status={link.status} (not paid)",
        }

    # 2. Idempotency: existing audit row?
    existing_audit = db.execute(
        select(PaymentGrantAuditModel).where(
            PaymentGrantAuditModel.tenant_id == tenant_id,
            PaymentGrantAuditModel.lead_id == lead_id,
            PaymentGrantAuditModel.offer_id == offer_id,
            PaymentGrantAuditModel.payment_id == payment_id,
        )
    ).scalar_one_or_none()

    if existing_audit is not None:
        return {
            "status": "success",
            "granted": True,
            "duplicate": True,
            "audit_id": str(existing_audit.id),
            "channels": existing_audit.channels,
        }

    # 3. Deliver via AccessProvider
    access_provider = access_provider_for_offer(offer_id)
    channels_delivered: list[str] = []
    failure_detail: dict = {}

    try:
        delivery = access_provider.deliver(
            tenant_id=tenant_id,
            lead_id=lead_id,
            offer_id=offer_id,
        )
        if delivery.get("delivered"):
            channels_delivered.append(delivery.get("channel", "unknown"))
    except Exception as exc:  # noqa: BLE001
        failure_detail["delivery_error"] = str(exc)
        logger.warning("grant_access_delivery_failed", error=str(exc))

    # 4. Persist audit row
    audit = PaymentGrantAuditModel(
        tenant_id=tenant_id,
        lead_id=lead_id,
        offer_id=offer_id,
        payment_id=payment_id,
        channels=channels_delivered,
        status="granted" if channels_delivered else "partial",
        failure_detail=failure_detail,
    )
    db.add(audit)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        # Race: another request created the audit row concurrently
        existing_audit = db.execute(
            select(PaymentGrantAuditModel).where(
                PaymentGrantAuditModel.tenant_id == tenant_id,
                PaymentGrantAuditModel.lead_id == lead_id,
                PaymentGrantAuditModel.offer_id == offer_id,
                PaymentGrantAuditModel.payment_id == payment_id,
            )
        ).scalar_one_or_none()
        return {
            "status": "success",
            "granted": True,
            "duplicate": True,
            "audit_id": str(existing_audit.id) if existing_audit else None,
            "channels": existing_audit.channels if existing_audit else [],
        }

    # 5. Publish event
    with contextlib.suppress(Exception):
        EventBus.publish(
            AccessGrantedEvent.create(
                tenant_id=tenant_id,
                lead_id=lead_id,
                offer_id=offer_id,
                payment_id=payment_id,
                channels=channels_delivered,
                audit_id=audit.id,
            ),
            session=None,
        )

    db.commit()

    return {
        "status": "success",
        "granted": True,
        "duplicate": False,
        "audit_id": str(audit.id),
        "channels": channels_delivered,
        "failure_detail": failure_detail,
    }


# ─────────────────────────────────────────────────────────────
# Registry
# ─────────────────────────────────────────────────────────────

PAYMENT_TOOL_REGISTRY: dict[str, Any] = {
    "create_payment_link": tool_create_payment_link,
    "verify_payment_status": tool_verify_payment_status,
    "grant_access": tool_grant_access,
}
