"""Marketing platform webhook endpoints.

Handles incoming webhooks from Shopify, Mailerlite, and other marketing
platforms. Mailerlite webhooks create journey_events and trigger lead
score recalculation for MQL transitions. Shopify webhooks process checkout
events into journey_events with identity resolution and scoring.
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

# Module-level cache for shop_domain -> tenant_id resolution
_shop_tenant_cache: dict[str, UUID] = {}


async def _resolve_tenant(db: Session, shop_domain: str) -> UUID | None:
    """Resolve tenant_id from Shopify shop_domain via connections table.

    Caches the mapping in a module-level dict for subsequent calls.
    """
    if shop_domain in _shop_tenant_cache:
        return _shop_tenant_cache[shop_domain]

    from src.modules.connections.infrastructure.models.channel_connection_model import (
        ChannelConnectionModel,
    )

    stmt = select(ChannelConnectionModel.tenant_id).where(
        ChannelConnectionModel.channel_type == "shopify",
        ChannelConnectionModel.is_active == True,  # noqa: E712
    )
    results = db.execute(stmt).all()

    for (tenant_id,) in results:
        # Check config JSONB for shop_domain match
        conn_stmt = select(ChannelConnectionModel.config).where(
            ChannelConnectionModel.tenant_id == tenant_id,
            ChannelConnectionModel.channel_type == "shopify",
            ChannelConnectionModel.is_active == True,  # noqa: E712
        )
        config = db.execute(conn_stmt).scalar_one_or_none()
        if config and config.get("shop_domain") == shop_domain:
            _shop_tenant_cache[shop_domain] = tenant_id
            return tenant_id

    return None


async def _handle_checkout_created(db: Session, tenant_id: UUID, payload: dict) -> None:
    """Process checkouts/create webhook: identity resolution + journey_event + scoring."""
    from src.modules.crm.application.services.customer_service import CustomerService
    from src.modules.crm.application.services.lifecycle_service import LifecycleService
    from src.modules.crm.infrastructure.models.customer_model import JourneyEventModel

    email = payload.get("email")
    if not email:
        logger.warning("shopify_checkout_no_email", tenant_id=str(tenant_id))
        return

    checkout_token = payload.get("token", "")

    # Idempotency: check for existing event with same checkout_token
    if checkout_token:
        from sqlalchemy import func as sa_func

        existing_stmt = select(JourneyEventModel.id).where(
            JourneyEventModel.tenant_id == tenant_id,
            JourneyEventModel.event_name == "checkout_initiated",
            sa_func.jsonb_extract_path_text(
                JourneyEventModel.properties, "checkout_token"
            ) == checkout_token,
        )
        existing = db.execute(existing_stmt).scalar_one_or_none()
        if existing:
            logger.info("shopify_checkout_duplicate", checkout_token=checkout_token)
            return

    # Identity resolution
    customer_svc = CustomerService(db)
    profile = customer_svc.identify(
        tenant_id=tenant_id,
        traits={
            "email": email,
            "name": payload.get("billing_address", {}).get("name", ""),
        },
        identities={},
    )

    # Set lead_source for direct Shopify buyers
    if not profile.lead_source:
        profile.lead_source = "shopify"

    # Create journey_event
    journey_event = JourneyEventModel(
        profile_id=profile.id,
        tenant_id=tenant_id,
        event_name="checkout_initiated",
        event_type="track",
        properties={
            "source": "shopify",
            "checkout_token": checkout_token,
            "total_price": float(payload.get("total_price", 0)),
            "currency": payload.get("currency", "USD"),
            "line_items_count": len(payload.get("line_items", [])),
        },
    )
    db.add(journey_event)

    # Recalculate score (checkout_started = +8.0 pts)
    lifecycle_svc = LifecycleService(db)
    lifecycle_svc.recalculate_score(profile.id, tenant_id)
    db.commit()

    logger.info(
        "shopify_checkout_processed",
        tenant_id=str(tenant_id),
        profile_id=str(profile.id),
        checkout_token=checkout_token,
    )


async def _handle_order_created(db: Session, tenant_id: UUID, payload: dict) -> None:
    """Process orders/create webhook: journey_event + SaleCompletedEvent."""
    from src.modules.crm.application.services.customer_service import CustomerService
    from src.modules.crm.infrastructure.models.customer_model import JourneyEventModel

    email = payload.get("email")
    if not email:
        logger.warning("shopify_order_no_email", tenant_id=str(tenant_id))
        return

    order_id = str(payload.get("id", ""))
    checkout_token = payload.get("checkout_token", "")

    # Idempotency: check for existing event with same order_id
    if order_id:
        from sqlalchemy import func as sa_func

        existing_stmt = select(JourneyEventModel.id).where(
            JourneyEventModel.tenant_id == tenant_id,
            JourneyEventModel.event_name == "checkout_completed",
            sa_func.jsonb_extract_path_text(
                JourneyEventModel.properties, "order_id"
            ) == order_id,
        )
        existing = db.execute(existing_stmt).scalar_one_or_none()
        if existing:
            logger.info("shopify_order_duplicate", order_id=order_id)
            return

    # Identity resolution
    customer_svc = CustomerService(db)
    profile = customer_svc.identify(
        tenant_id=tenant_id,
        traits={
            "email": email,
            "name": payload.get("billing_address", {}).get("name", ""),
        },
        identities={},
    )

    total_price = float(payload.get("total_price", 0))

    # Create journey_event
    journey_event = JourneyEventModel(
        profile_id=profile.id,
        tenant_id=tenant_id,
        event_name="checkout_completed",
        event_type="track",
        properties={
            "source": "shopify",
            "order_id": order_id,
            "checkout_token": checkout_token,
            "total_price": total_price,
            "currency": payload.get("currency", "USD"),
            "line_items_count": len(payload.get("line_items", [])),
        },
    )
    db.add(journey_event)

    # Publish SaleCompletedEvent for Stage 4 (Ventas)
    from src.shared.domain.events import EventBus
    from src.modules.crm.domain.events import SaleCompletedEvent
    import uuid

    sale_event = SaleCompletedEvent.create(
        tenant_id=tenant_id,
        sale_id=uuid.uuid4(),
        customer_id=profile.id,
        stage="CONVERSION",
        amount=total_price,
        offer_id=uuid.UUID(int=0),  # No offer context from Shopify
    )
    EventBus.publish(sale_event, session=db)
    db.commit()

    logger.info(
        "shopify_order_processed",
        tenant_id=str(tenant_id),
        profile_id=str(profile.id),
        order_id=order_id,
    )


# TODO: Background task to detect abandoned carts (checkouts older than 1h
# without matching order). For now, cart_abandoned events will come from a
# future background job. Do NOT handle in webhook.

# ENABLE_MOCKS strategy: Unit tests in test_shopify_webhook.py call _handle_checkout_created
# directly with mock payloads, validating the full handler pipeline without a live Shopify
# dev store. The frontend ENABLE_MOCKS toggle returns mock data from metrics-mock-data.ts.
# Backend has no runtime mock toggle -- tests exercise handlers directly.


@router.post("/shopify", status_code=status.HTTP_200_OK)
async def shopify_webhook(
    request: Request,
    verified: bool = Depends(verify_shopify_signature),
    db: Session = Depends(get_db),
):
    """Receive and process Shopify webhooks.

    Reads X-Shopify-Topic and X-Shopify-Shop-Domain headers to dispatch
    to the appropriate handler. Always returns 200 OK to prevent Shopify retries.
    """
    try:
        payload = await request.json()
        topic = request.headers.get("X-Shopify-Topic", "")
        shop_domain = request.headers.get("X-Shopify-Shop-Domain", "")

        logger.info(
            "shopify_webhook_received",
            topic=topic,
            shop_domain=shop_domain,
        )

        # Resolve tenant from shop_domain
        tenant_id = await _resolve_tenant(db, shop_domain)
        if not tenant_id:
            logger.warning("shopify_webhook_unknown_tenant", shop_domain=shop_domain)
            return {"status": "ignored", "reason": "unknown_shop_domain"}

        # Dispatch to handler
        if topic == "checkouts/create":
            await _handle_checkout_created(db, tenant_id, payload)
        elif topic == "orders/create":
            await _handle_order_created(db, tenant_id, payload)
        else:
            logger.info("shopify_webhook_unhandled_topic", topic=topic)

        return {"status": "processed", "topic": topic}

    except Exception as e:
        logger.error("shopify_webhook_error", error=str(e))
        # Always return 200 OK to prevent Shopify retries
        return {"status": "error", "detail": "processing_failed"}


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
