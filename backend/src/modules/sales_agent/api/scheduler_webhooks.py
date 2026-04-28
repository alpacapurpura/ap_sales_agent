"""Inbound webhook endpoint for external scheduler providers (S8).

`POST /api/v1/sales-agent/webhooks/scheduler/{provider}`

Generic provider-agnostic endpoint. Routes to the
``WebhookProvider`` impl registered for ``{provider}`` in
``SCHEDULER_WEBHOOK_PROVIDERS``. Internal scheduler does NOT use this
endpoint — its bookings come via Nicolify's own
``POST /event-types/.../book`` flow.

Pipeline per request:

1. Look up the registered ``WebhookProvider`` class. Unknown → 404.
2. Resolve the per-tenant signing secret (lazy stub today; pluggable
   when external provider config lands).
3. ``verify_signature(body, headers, secret)`` → 401 on failure.
4. ``parse_payload(json)`` → ``ParsedWebhookEvent``.
5. Persist to ``scheduler_webhook_event`` (UNIQUE natural key dedup).
   Replay → 200 ``duplicate``.
6. Translate to ``AppointmentEvent`` / ``BookingMissedEvent`` and
   ``EventBus.publish(... session=db)`` so subscribers fire after
   commit.

This endpoint is intentionally **registry-driven**. Adding Cal.com or
Calendly tomorrow:

* ``register_webhook_provider(CalcomWebhookProvider)`` at app startup.
* No edits here.

Arch test ``test_no_hardcoded_webhook_provider.py`` enforces.
"""

# [SALES-AGENT-S8-WEBHOOK]  # noqa: ERA001

from __future__ import annotations

import datetime as dt
import json
from typing import Annotated, Any
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.sales_agent.application.tools.scheduling.webhook_providers import (
    ParsedWebhookEvent,
    UnknownWebhookProviderError,
    WebhookEventType,
    webhook_provider_for,
)
from src.modules.sales_agent.infrastructure.models.scheduler_webhook_event_model import (
    SchedulerWebhookEventModel,
)
from src.shared.domain.events import AppointmentEvent, EventBus

logger = structlog.get_logger()

router = APIRouter()


class WebhookAck(BaseModel):
    """Acknowledgement returned to the scheduler provider."""

    model_config = ConfigDict(extra="forbid")

    status: str
    event_type: str
    duplicate: bool = False


@router.post("/webhooks/scheduler/{provider}", response_model=WebhookAck)
async def scheduler_webhook(
    provider: str,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> WebhookAck:
    """Generic inbound entry-point for any external scheduler provider."""
    try:
        provider_cls = webhook_provider_for(provider)
    except UnknownWebhookProviderError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    body = await request.body()
    headers = {k.lower(): v for k, v in request.headers.items()}
    secret = _resolve_signing_secret(db, provider)

    handler = provider_cls()
    if not handler.verify_signature(body, headers, secret):
        logger.warning(
            "scheduler_webhook_signature_invalid",
            provider=provider,
            content_length=len(body),
        )
        raise HTTPException(status_code=401, detail="invalid_signature")

    try:
        payload = json.loads(body) if body else {}
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="malformed_json") from exc

    parsed = handler.parse_payload(payload)

    if parsed.event_type == WebhookEventType.IGNORED:
        # Still log to dedup table for audit, but don't fan out.
        _persist_dedup(db, parsed, payload)
        return WebhookAck(status="ignored", event_type=parsed.event_type.value)

    is_duplicate = not _persist_dedup(db, parsed, payload)
    if is_duplicate:
        return WebhookAck(
            status="duplicate",
            event_type=parsed.event_type.value,
            duplicate=True,
        )

    _dispatch(parsed, db)
    return WebhookAck(status="ok", event_type=parsed.event_type.value)


# ──────────────────────────────────────────────────────────────
# helpers
# ──────────────────────────────────────────────────────────────


def _persist_dedup(
    db: Session,
    parsed: ParsedWebhookEvent,
    payload: dict[str, Any],
) -> bool:
    """Insert a dedup row. Returns ``True`` if new, ``False`` if duplicate."""
    row = SchedulerWebhookEventModel(
        provider=parsed.provider_id,
        tracking_id=parsed.tracking_id,
        event_type=parsed.event_type.value,
        occurred_at=parsed.occurred_at,
        tenant_id=parsed.tenant_id,
        lead_id=parsed.lead_id,
        payload_raw=payload,
    )
    db.add(row)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        return False
    db.commit()
    return True


def _dispatch(parsed: ParsedWebhookEvent, db: Session) -> None:
    """Translate webhook event to a shared domain event + publish."""
    if parsed.tenant_id is None or parsed.lead_id is None:
        logger.warning(
            "scheduler_webhook_missing_identifiers",
            provider=parsed.provider_id,
            event_type=parsed.event_type.value,
        )
        return

    appointment_status = _to_appointment_status(parsed.event_type)
    if appointment_status is None:
        return

    appointment_uuid = _coerce_appointment_uuid(parsed.external_appointment_id)

    EventBus.publish(
        AppointmentEvent.create(
            tenant_id=parsed.tenant_id,
            lead_id=parsed.lead_id,
            appointment_id=appointment_uuid,
            appointment_status=appointment_status,
        ),
        session=db,
    )


def _to_appointment_status(event_type: WebhookEventType) -> str | None:
    """Map normalized webhook event type to AppointmentStatus value."""
    return {
        WebhookEventType.BOOKING_CONFIRMED: "SCHEDULED",
        WebhookEventType.BOOKING_RESCHEDULED: "SCHEDULED",
        WebhookEventType.BOOKING_COMPLETED: "COMPLETED",
        WebhookEventType.BOOKING_NO_SHOW: "NO_SHOW",
        WebhookEventType.BOOKING_CANCELLED: "CANCELLED",
    }.get(event_type)


def _coerce_appointment_uuid(raw: str | None) -> UUID:
    """Coerce a provider appointment id into a deterministic UUID.

    External appointment ids are provider-specific strings; pin to a
    deterministic UUID5 so the AppointmentEvent payload type holds.
    """
    import uuid as _uuid

    if raw is None:
        return _uuid.uuid4()
    try:
        return UUID(str(raw))
    except ValueError:
        return _uuid.uuid5(_uuid.NAMESPACE_URL, str(raw))


def _resolve_signing_secret(db: Session, provider: str) -> str:
    """Return the per-tenant signing secret for this provider.

    Stub today: reads ``SCHEDULER_WEBHOOK_SECRET_<PROVIDER>`` env var
    until per-tenant connection config lands. Concrete external provider
    impls (Cal.com / Calendly) will replace this with a connection
    lookup analogous to ``get_channel_credentials``.
    """
    import os

    _ = db  # reserved for future per-tenant lookup
    return os.environ.get(f"SCHEDULER_WEBHOOK_SECRET_{provider.upper()}", "")


# Backwards-friendly alias used by tests.
_now = dt.datetime.now  # type: ignore[assignment]
