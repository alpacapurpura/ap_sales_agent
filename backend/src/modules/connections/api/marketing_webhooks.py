"""Marketing platform webhook endpoints.

Handles incoming webhooks from Shopify, Mailerlite, and other marketing
platforms. Mailerlite webhooks create journey_events and trigger lead
score recalculation for MQL transitions.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session
import structlog

from src.core.database import get_db
from src.modules.connections.api.dependencies.webhook_security import verify_shopify_signature

logger = structlog.get_logger()

router = APIRouter()


@router.post("/shopify", status_code=status.HTTP_200_OK)
async def shopify_webhook(
    request: Request,
    verified: bool = Depends(verify_shopify_signature),
    db: Session = Depends(get_db),
):
    """
    Recibe un webhook de Shopify.
    """
    try:
        payload = await request.json()
        logger.info("shopify_webhook_received", payload_keys=list(payload.keys()))

        # TODO: Use Communication Service or Event Bus to handle this
        # e.g. event_bus.publish(ShopifyOrderReceived(payload))

        return {"status": "received", "source": "shopify"}

    except Exception as e:
        logger.error("shopify_webhook_error", error=str(e))
        raise HTTPException(status_code=400, detail="Invalid payload")


@router.post("/mailerlite/{tenant_id}", status_code=status.HTTP_200_OK)
async def handle_mailerlite_webhook(
    tenant_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
):
    """Handle Mailerlite webhook events (campaign.open, campaign.click).

    Creates journey_events and triggers lead score recalculation.
    If the score crosses the MQL threshold, a lifecycle transition is recorded.
    """
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event_type = payload.get("type", "")
    subscriber = payload.get("subscriber", {})
    email = subscriber.get("email")

    if not email:
        return {"status": "ignored", "reason": "no_email"}

    # 1. Find customer profile by email
    from src.modules.crm.infrastructure.models.customer_model import (
        CustomerProfileModel,
    )

    stmt = select(CustomerProfileModel).where(
        CustomerProfileModel.tenant_id == tenant_id,
        CustomerProfileModel.primary_email == email,
        CustomerProfileModel.is_inactive == False,  # noqa: E712
    )
    result = db.execute(stmt)
    profile = result.scalar_one_or_none()

    if not profile:
        return {"status": "ignored", "reason": "unknown_subscriber"}

    # 2. Map event type to event_name
    if "open" in event_type:
        event_name = "email_opened"
    elif "click" in event_type:
        event_name = "email_clicked"
    else:
        return {"status": "ignored", "reason": f"unsupported_event: {event_type}"}

    # 3. Create journey_event
    from src.modules.crm.infrastructure.models.customer_model import (
        JourneyEventModel,
    )

    journey_event = JourneyEventModel(
        profile_id=profile.id,
        tenant_id=tenant_id,
        event_name=event_name,
        event_type="track",
        properties={
            "campaign_id": str(payload.get("campaign", {}).get("id", "")),
            "campaign_name": payload.get("campaign", {}).get("name", ""),
            "source": "mailerlite_webhook",
        },
    )
    db.add(journey_event)

    # 4. Recalculate score (triggers MQL transition if threshold crossed)
    from src.modules.crm.application.services.lifecycle_service import LifecycleService

    lifecycle_svc = LifecycleService(db)
    lifecycle_svc.recalculate_score(profile.id, tenant_id)
    db.commit()

    logger.info(
        "mailerlite_webhook_processed",
        tenant_id=str(tenant_id),
        event=event_name,
        profile_id=str(profile.id),
    )
    return {"status": "processed", "event": event_name, "profile_id": str(profile.id)}


@router.post("/mailerlite", status_code=status.HTTP_200_OK)
async def mailerlite_webhook_legacy(request: Request, db: Session = Depends(get_db)):
    """Legacy Mailerlite webhook (no tenant_id). Kept for backward compatibility."""
    try:
        payload = await request.json()
        logger.info("mailerlite_webhook_received_legacy", payload_keys=list(payload.keys()))
        return {"status": "received", "source": "mailerlite"}
    except Exception as e:
        logger.error("mailerlite_webhook_error", error=str(e))
        raise HTTPException(status_code=400, detail="Invalid payload")
