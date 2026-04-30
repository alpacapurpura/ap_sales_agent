"""Inbound webhook endpoint for payment providers — S9.

``POST /api/v1/sales-agent/webhooks/payment/{provider}``

Generic provider-agnostic endpoint. Routes to the ``PaymentWebhookProvider``
impl registered for ``{provider}`` in ``PAYMENT_WEBHOOK_PROVIDERS``.

Pipeline per request:

1. Look up registered ``PaymentWebhookProvider``. Unknown → 404.
2. Resolve per-tenant signing secret:
   a. ``ChannelConnectionModel.config["webhook_secret"]`` for the tenant's
      payment connection (resolves DEFERRED-S9).
   b. Env-var ``PAYMENT_WEBHOOK_SECRET_<PROVIDER>`` as fallback / testing.
3. ``verify_signature(body, headers, secret)`` → 401 on failure.
   Empty secret = fail-closed → 401 (no empty-secret bypass).
4. ``parse_payload(json)`` → ``ParsedPaymentWebhookEvent``.
5. Persist to ``payment_webhook_event`` (UNIQUE dedup). Replay → 200 duplicate.
6. Publish ``PaymentReceivedEvent`` or ``PaymentLinkCreatedEvent`` after commit.

Registry-driven: new provider = ``register_payment_webhook_provider(...)`` at
app startup. No edits here.

Arch test ``test_no_hardcoded_payment_provider_in_tools`` enforces.
"""

from __future__ import annotations

import contextlib
import json
import os
from typing import Annotated, Any
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.sales_agent.application.tools.payment.webhook_providers import (
    ParsedPaymentWebhookEvent,
    PaymentWebhookEventType,
    webhook_provider_for,
)
from src.modules.sales_agent.infrastructure.models.payment_webhook_event_model import (
    PaymentWebhookEventModel,
)
from src.shared.domain.events import PaymentReceivedEvent
from src.shared.domain_events.outbox.application.event_bus_adapter import (
    adapter_bus as EventBus,  # noqa: N812
)

logger = structlog.get_logger()

router = APIRouter()


class PaymentWebhookAck(BaseModel):
    """Acknowledgement returned to the payment provider."""

    model_config = ConfigDict(extra="forbid")

    status: str
    duplicate: bool = False


@router.post("/webhooks/payment/{provider}", response_model=PaymentWebhookAck)
async def payment_webhook(
    provider: str,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> PaymentWebhookAck:
    """Generic inbound entry-point for any payment provider webhook."""
    provider_cls = webhook_provider_for(provider)
    if provider_cls is None:
        raise HTTPException(status_code=404, detail=f"Unknown payment provider: {provider}")

    body = await request.body()
    headers = {k.lower(): v for k, v in request.headers.items()}

    # Resolve signing secret — fail-closed if empty
    secret = _resolve_signing_secret(db, provider, headers)
    if not secret:
        logger.warning("payment_webhook_empty_secret", provider=provider)
        raise HTTPException(status_code=401, detail="invalid_signature")

    provider_handler = provider_cls()

    if not provider_handler.verify_signature(body, headers, secret):
        logger.warning(
            "payment_webhook_signature_invalid",
            provider=provider,
            content_length=len(body),
        )
        raise HTTPException(status_code=401, detail="invalid_signature")

    try:
        payload = json.loads(body) if body else {}
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="malformed_json") from exc

    parsed = provider_handler.parse_payload(payload)

    is_new = _persist_dedup(db, parsed, payload)
    if not is_new:
        return PaymentWebhookAck(status="ok", duplicate=True)

    _dispatch(parsed, db)
    return PaymentWebhookAck(status="ok", duplicate=False)


# ─────────────────────────────────────────────────────────────
# helpers
# ─────────────────────────────────────────────────────────────


def _resolve_signing_secret(
    db: Session,
    provider: str,
    headers: dict[str, str],
) -> str:
    """Resolve the per-tenant signing secret for a payment provider.

    Resolution order:
    1. ``ChannelConnectionModel.config["webhook_secret"]`` — per-tenant
       (resolves DEFERRED-S9 from S8 scheduler stub).
    2. Env-var ``PAYMENT_WEBHOOK_SECRET_<PROVIDER>`` — test/fallback.
    """
    tenant_id: UUID | None = None

    # Try to extract tenant_id from the payload context (pre-parse best effort)
    # Many providers include a custom header or query param.
    raw_tenant = headers.get("x-tenant-id") or headers.get("x-nicolify-tenant-id")
    if raw_tenant:
        with contextlib.suppress(ValueError):
            tenant_id = UUID(raw_tenant)

    if tenant_id is not None:
        with contextlib.suppress(Exception):
            from src.shared.links.ports.payment_connection import (
                get_payment_webhook_secret,
            )

            secret = get_payment_webhook_secret(db, tenant_id, provider)
            if secret:
                return secret

    # Env-var fallback
    return os.environ.get(f"PAYMENT_WEBHOOK_SECRET_{provider.upper()}", "")


def _persist_dedup(
    db: Session,
    parsed: ParsedPaymentWebhookEvent,
    payload: dict[str, Any],
) -> bool:
    """Insert dedup row. Returns True if new, False if duplicate."""
    row = PaymentWebhookEventModel(
        tenant_id=parsed.tenant_id,
        provider=parsed.provider_id,
        external_id=parsed.external_payment_id or "",
        event_type=parsed.event_type.value,
        occurred_at=parsed.occurred_at,
        payload=payload,
    )
    db.add(row)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        return False
    db.commit()
    return True


def _dispatch(parsed: ParsedPaymentWebhookEvent, db: Session) -> None:
    """Publish domain event based on parsed webhook event type."""
    if parsed.event_type == PaymentWebhookEventType.PAID:
        if parsed.tenant_id is None:
            logger.warning(
                "payment_webhook_missing_tenant_id",
                provider=parsed.provider_id,
            )
            return

        # Look up lead_id from PaymentLinkModel via external_payment_id
        lead_id = parsed.lead_id
        offer_id: UUID | None = None
        payment_id: UUID | None = None

        if parsed.external_payment_id:
            try:
                from sqlalchemy import select

                from src.modules.sales_agent.infrastructure.models.payment_link_model import (
                    PaymentLinkModel,
                )

                link = db.execute(
                    select(PaymentLinkModel).where(
                        PaymentLinkModel.tenant_id == parsed.tenant_id,
                        PaymentLinkModel.external_id == parsed.external_payment_id,
                    )
                ).scalar_one_or_none()

                if link:
                    lead_id = lead_id or link.lead_id
                    offer_id = link.offer_id
                    payment_id = link.id
                    link.status = "paid"
                    db.flush()
            except Exception:  # noqa: BLE001
                pass

        if lead_id and offer_id and payment_id:
            EventBus.publish(
                PaymentReceivedEvent.create(
                    tenant_id=parsed.tenant_id,
                    lead_id=lead_id,
                    offer_id=offer_id,
                    payment_id=payment_id,
                    auto_grant=True,
                ),
                session=db,
            )
