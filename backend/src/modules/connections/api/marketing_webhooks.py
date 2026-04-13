"""Marketing platform webhook endpoints.

Handles incoming webhooks from Shopify, Mailerlite, and other marketing
platforms. Mailerlite webhooks create journey_events and trigger lead
score recalculation for MQL transitions. Shopify webhooks process checkout
events into journey_events with identity resolution and scoring.
"""

from collections.abc import Callable
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.connections.api.dependencies.webhook_security import (
    verify_shopify_signature,
)

logger = structlog.get_logger()

# -- ManyChat event mapping --
_MANYCHAT_EVENT_MAP = {
    "subscriber.new": "manychat_subscriber_created",
    "tag.applied": "manychat_tag_applied",
    "flow.triggered": "manychat_flow_triggered",
    "field.updated": "manychat_field_updated",
    "comment.trigger": "manychat_comment_trigger",
}

_MANYCHAT_CHANNEL_SLUG = {
    "instagram": "manychat-ig",
    "whatsapp": "manychat-wa",
}

router = APIRouter()

# -- ManyChat helper functions --


_TAG_METRIC_MAP: dict[str, str] = {
    "Solicito_reunion": "meetings_requested",
    "link_clicked": "link_clicks",
    "quiz_started": "qualified_leads",
    "Estrategia": "qualified_leads",
    "Orden": "qualified_leads",
    "Bienestar": "qualified_leads",
    "Liderazgo": "qualified_leads",
    "Claridad": "qualified_leads",
}


def _tag_to_metric(payload: dict) -> str:
    return _TAG_METRIC_MAP.get(payload.get("tag_name", ""), "tag_applied")


def _flow_to_metric(payload: dict) -> str:
    flow_name = payload.get("flow_name", "")
    if "BOFU" in flow_name.upper():
        return "bofu_flows_triggered"
    if "FollowUp" in flow_name or "Sequence" in flow_name:
        return "sequences_sent"
    return "flows_triggered"


def _field_to_metric(payload: dict) -> str | None:
    return (
        "consultations" if payload.get("custom_field_name", "") == "Consultas" else None
    )


_EVENT_METRIC_HANDLERS: dict[str, Callable[[dict], str | None]] = {
    "subscriber.new": lambda _: "new_subscribers",
    "comment.trigger": lambda _: "comment_triggers",
    "tag.applied": _tag_to_metric,
    "flow.triggered": _flow_to_metric,
    "field.updated": _field_to_metric,
}


def _event_to_metric_name(event_type: str, payload: dict) -> str | None:
    """Map ManyChat event type to a metric_name for staging_metrics."""
    handler = _EVENT_METRIC_HANDLERS.get(event_type)
    return handler(payload) if handler else None


_EVENT_STAGE_HANDLERS: dict[str, Callable[[dict], str]] = {
    "comment.trigger": lambda _: "attraction",
    "subscriber.new": lambda _: "capture",
    "tag.applied": lambda p: (
        "opportunity" if p.get("tag_name", "") == "Solicito_reunion" else "nurture"
    ),
    "flow.triggered": lambda p: (
        "opportunity" if "BOFU" in p.get("flow_name", "").upper() else "nurture"
    ),
    "field.updated": lambda _: "nurture",
}


def _event_to_stage(event_type: str, payload: dict) -> str | None:
    """Map ManyChat event to funnel stage."""
    handler = _EVENT_STAGE_HANDLERS.get(event_type)
    return handler(payload) if handler else None


def _event_to_channel_suffix(event_type: str, payload: dict) -> str:
    """Map event type to channel slug suffix."""
    if event_type == "comment.trigger":
        return "comments"
    if event_type in ("tag.applied", "field.updated"):
        tag = payload.get("tag_name", "")
        if tag == "Solicito_reunion":
            return "bofu"
        return "sequences"
    if event_type == "flow.triggered":
        flow_name = payload.get("flow_name", "")
        if "BOFU" in flow_name.upper():
            return "bofu"
        return "sequences"
    return "ig"


def _resolve_manychat_profile(
    db: Session,
    tenant_id: UUID,
    payload: dict,
    channel_slug: str,
):
    """Resolve or create a customer profile from ManyChat subscriber data."""
    from src.modules.crm.application.services.customer_service import CustomerService

    ig_username = payload.get("ig_username")
    email = payload.get("email")
    phone = payload.get("phone")
    first_name = payload.get("first_name", "")
    last_name = payload.get("last_name", "")

    # First, try to match by instagram_username trait (bridge Meta <-> ManyChat).
    # When a user sends a DM, Meta webhook arrives first (~100ms) and the
    # InstagramProfileEnricher sets traits.instagram_username on the profile.
    # ManyChat processes the same message ~1-3s later with ig_username.
    # This lookup prevents creating a duplicate profile.
    profile = None
    if ig_username:
        from src.modules.crm.infrastructure.models.customer_model import (
            CustomerProfileModel as _CustomerProfile,
        )
        from src.modules.crm.infrastructure.repositories.customer_repository import (
            CustomerRepository,
        )

        customer_repo = CustomerRepository(db)
        existing = customer_repo.find_by_trait(
            tenant_id=tenant_id,
            trait_key="instagram_username",
            trait_value=ig_username.lstrip("@"),
        )
        if existing:
            stmt = select(_CustomerProfile).where(_CustomerProfile.id == existing.id)
            profile = db.execute(stmt).scalar_one_or_none()

    if not profile and (email or phone):
        customer_svc = CustomerService(db)
        traits = {"name": f"{first_name} {last_name}".strip()}
        if email:
            traits["email"] = email
        identities: dict[str, str] = {}
        if ig_username:
            identities["instagram"] = ig_username
        if phone:
            identities["phone"] = phone

        profile = customer_svc.identify(
            tenant_id=tenant_id,
            traits=traits,
            identities=identities,
        )
        if not profile.lead_source:
            profile.lead_source = channel_slug

    return profile


def _build_manychat_event_properties(
    payload: dict,
    subscriber_id: str,
    channel: str,
    event_type: str,
) -> dict[str, str | dict[str, str]]:
    """Build journey_event properties dict from ManyChat payload."""
    properties: dict[str, str | dict[str, str]] = {
        "source": "manychat_webhook",
        "manychat_subscriber_id": subscriber_id,
        "channel": channel,
        "event_type": event_type,
    }
    if payload.get("tag_name"):
        properties["tag_name"] = payload["tag_name"]
    if payload.get("flow_ns"):
        properties["flow_ns"] = payload["flow_ns"]
        properties["flow_name"] = payload.get("flow_name", "")
    if payload.get("custom_field_name"):
        properties["custom_field_name"] = payload["custom_field_name"]
        properties["custom_field_value"] = payload.get("custom_field_value", "")
    if payload.get("custom_fields"):
        properties["custom_fields_snapshot"] = payload["custom_fields"]
    return properties


def _create_journey_events(
    db: Session,
    tenant_id: UUID,
    profile,
    event_name: str,
    event_type: str,
    properties: dict,
    channel_slug: str,
    channel: str,
    subscriber_id: str,
) -> None:
    """Create journey_event(s) and recalculate lead score."""
    from src.modules.crm.application.services.lifecycle_service import LifecycleService
    from src.modules.crm.infrastructure.models.customer_model import JourneyEventModel

    journey_event = JourneyEventModel(
        profile_id=profile.id,
        tenant_id=tenant_id,
        event_name=event_name,
        event_type="track",
        properties=properties,
    )
    db.add(journey_event)

    # Bridge: subscriber.new -> message_received for conversation counting.
    if event_type == "subscriber.new":
        msg_event = JourneyEventModel(
            profile_id=profile.id,
            tenant_id=tenant_id,
            event_name="message_received",
            event_type="track",
            properties={
                "channel_slug": channel_slug,
                "channel_type": channel,
                "message_direction": "inbound",
                "source": "manychat_webhook",
                "manychat_subscriber_id": subscriber_id,
            },
        )
        db.add(msg_event)

    lifecycle_svc = LifecycleService(db)
    lifecycle_svc.recalculate_score(profile.id, tenant_id)


def _promote_manychat_metric(
    db: Session,
    tenant_id: UUID,
    event_type: str,
    payload: dict,
    channel_slug: str,
    subscriber_id: str,
) -> None:
    """Promote ManyChat event to official_metrics for Growth Studio."""
    from src.modules.analytics.application.services.manychat_metrics_promoter import (
        ManyChatMetricsPromoter,
    )
    from src.shared.domain.datetime_utils import utc_today as date_cls_today

    metric_name = _event_to_metric_name(event_type, payload)
    stage_slug = _event_to_stage(event_type, payload)
    if not metric_name or not stage_slug:
        return

    resolved_channel = (
        channel_slug
        if stage_slug in ("capture", "attraction")
        else f"manychat-{_event_to_channel_suffix(event_type, payload)}"
    )
    # For attraction stage, use the dedicated slug
    if stage_slug == "attraction":
        resolved_channel = "manychat-comments"

    promoter = ManyChatMetricsPromoter(db)
    promoter.promote_event(
        tenant_id=tenant_id,
        channel_slug=resolved_channel,
        metric_name=metric_name,
        metric_date=date_cls_today(),
        stage_slug=stage_slug,
        value=1.0,
        extra={"subscriber_id": subscriber_id, "event_type": event_type},
    )


async def _handle_manychat_event(
    db: Session,
    tenant_id: UUID,
    payload: dict,
    channel: str,
) -> None:
    """Process a ManyChat webhook event into journey_events + official_metrics."""
    event_type = payload.get("event_type", "")
    event_name = _MANYCHAT_EVENT_MAP.get(event_type, f"manychat_{event_type}")
    channel_slug = _MANYCHAT_CHANNEL_SLUG.get(channel, "manychat-ig")
    subscriber_id = payload.get("subscriber_id", "")

    # 1. Identity resolution
    profile = _resolve_manychat_profile(db, tenant_id, payload, channel_slug)

    # 2. Create journey_event(s) + recalculate score
    if profile:
        properties = _build_manychat_event_properties(
            payload,
            subscriber_id,
            channel,
            event_type,
        )
        _create_journey_events(
            db,
            tenant_id,
            profile,
            event_name,
            event_type,
            properties,
            channel_slug,
            channel,
            subscriber_id,
        )

    # 3. Promote metric to official_metrics for Growth Studio
    _promote_manychat_metric(
        db,
        tenant_id,
        event_type,
        payload,
        channel_slug,
        subscriber_id,
    )

    db.commit()

    logger.info(
        "manychat_webhook_processed",
        tenant_id=str(tenant_id),
        event=event_name,
        channel=channel,
        profile_id=str(profile.id) if profile else "none",
    )


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
                JourneyEventModel.properties,
                "checkout_token",
            )
            == checkout_token,
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

    # Extract line_items for unmatched product detection
    line_items_raw = payload.get("line_items", [])
    line_items_data = [
        {
            "product_id": str(item.get("product_id", "")),
            "variant_id": str(item.get("variant_id", "")),
            "title": item.get("title", ""),
            "price": float(item.get("price", 0)),
            "quantity": int(item.get("quantity", 1)),
        }
        for item in line_items_raw
    ]

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
            "line_items_count": len(line_items_raw),
            "line_items": line_items_data,
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
    """Process orders/create webhook: journey_event + per-line-item SaleCompletedEvents."""
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
            sa_func.jsonb_extract_path_text(JourneyEventModel.properties, "order_id")
            == order_id,
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

    # Extract and resolve line_items
    line_items_raw = payload.get("line_items", [])
    line_items_data = [
        {
            "product_id": str(item.get("product_id", "")),
            "variant_id": str(item.get("variant_id", "")),
            "title": item.get("title", ""),
            "price": float(item.get("price", 0)),
            "quantity": int(item.get("quantity", 1)),
        }
        for item in line_items_raw
    ]

    # Bulk resolve product_id → offer_id mappings
    from src.modules.offer.infrastructure.repositories.external_product_mapping_repository import (
        ExternalProductMappingRepository,
    )

    mapping_repo = ExternalProductMappingRepository(db)
    product_ids = [li["product_id"] for li in line_items_data if li["product_id"]]
    resolved_mappings = mapping_repo.bulk_resolve(tenant_id, "shopify", product_ids)

    # Create journey_event with full line_items
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
            "line_items_count": len(line_items_raw),
            "line_items": line_items_data,
        },
    )
    db.add(journey_event)

    # Publish one SaleCompletedEvent per line_item
    import uuid as uuid_mod

    from src.shared.domain.events import EventBus, SaleCompletedEvent

    for item in line_items_data:
        product_id = item["product_id"]
        offer_id = resolved_mappings.get(product_id, uuid_mod.UUID(int=0))
        line_amount = item["price"] * item["quantity"]

        sale_event = SaleCompletedEvent.create(
            tenant_id=tenant_id,
            sale_id=uuid_mod.uuid4(),
            customer_id=profile.id,
            stage="CONVERSION",
            amount=line_amount,
            offer_id=offer_id,
        )
        EventBus.publish(sale_event, session=db)

    # Fallback: if no line_items, publish single event with total
    if not line_items_data:
        sale_event = SaleCompletedEvent.create(
            tenant_id=tenant_id,
            sale_id=uuid_mod.uuid4(),
            customer_id=profile.id,
            stage="CONVERSION",
            amount=total_price,
            offer_id=uuid_mod.UUID(int=0),
        )
        EventBus.publish(sale_event, session=db)

    db.commit()

    logger.info(
        "shopify_order_processed",
        tenant_id=str(tenant_id),
        profile_id=str(profile.id),
        order_id=order_id,
        line_items=len(line_items_data),
        resolved_offers=len(resolved_mappings),
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
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from None

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
        logger.info(
            "mailerlite_webhook_received_legacy",
            payload_keys=list(payload.keys()),
        )
        return {"status": "received", "source": "mailerlite"}
    except Exception as e:
        logger.error("mailerlite_webhook_error", error=str(e))
        raise HTTPException(status_code=400, detail="Invalid payload") from e


@router.post("/manychat/{tenant_id}", status_code=status.HTTP_200_OK)
async def handle_manychat_webhook(
    tenant_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
):
    """Receive ManyChat events via External Request blocks.

    Event types:
    - subscriber.new: New subscriber captured
    - tag.applied: Tag assigned to subscriber
    - flow.triggered: Automation flow triggered
    - field.updated: Custom field value changed
    - comment.trigger: Comment trigger activated
    """
    from pydantic import ValidationError

    from src.modules.connections.api.dto.manychat_webhook_dto import (
        ManyChatWebhookPayload,
    )

    try:
        raw = await request.json()
        dto = ManyChatWebhookPayload(**raw)
    except ValidationError as ve:
        raise HTTPException(status_code=422, detail=ve.errors()) from ve
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from None

    payload = dto.model_dump()
    event_type = dto.event_type
    channel = dto.channel

    # Verify tenant has ManyChat connected
    from src.modules.connections.infrastructure.models.channel_connection_model import (
        ChannelConnectionModel,
    )

    conn_stmt = select(ChannelConnectionModel).where(
        ChannelConnectionModel.tenant_id == tenant_id,
        ChannelConnectionModel.channel_type == "manychat",
        ChannelConnectionModel.is_active == True,  # noqa: E712
    )
    connection = db.execute(conn_stmt).scalar_one_or_none()
    if not connection:
        logger.warning("manychat_webhook_no_connection", tenant_id=str(tenant_id))
        return {"status": "ignored", "reason": "no_manychat_connection"}

    await _handle_manychat_event(db, tenant_id, payload, channel)

    return {"status": "processed", "event": event_type}
