"""Periodic ManyChat subscriber sync task.

Reads subscriber_ids from recent manychat journey_events,
fetches their full profile from ManyChat API, and updates
CRM customer_profiles with enrichment data (tags, custom fields, score).

Schedule: Every 6 hours via ARQ.
Rate limit aware: 10 req/s max to ManyChat API.
"""

import asyncio
from datetime import UTC, datetime, timedelta
from uuid import UUID

import structlog
from sqlalchemy import func as sa_func
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.modules.connections.infrastructure.marketing_connectors.manychat import (
    ManyChatConnector,
)
from src.modules.connections.infrastructure.models.channel_connection_model import (
    ChannelConnectionModel,
)
from src.modules.crm.infrastructure.models.customer_model import JourneyEventModel

logger = structlog.get_logger()


async def sync_manychat_subscribers(tenant_id: UUID, db: Session) -> dict:
    """Sync recent ManyChat subscribers for a tenant.

    Returns summary dict with counts.
    """
    # 1. Get ManyChat API key
    conn_stmt = select(ChannelConnectionModel).where(
        ChannelConnectionModel.tenant_id == tenant_id,
        ChannelConnectionModel.channel_type == "manychat",
        ChannelConnectionModel.is_active == True,
    )
    connection = db.execute(conn_stmt).scalar_one_or_none()
    if not connection:
        return {"status": "skipped", "reason": "no_connection"}

    api_key = connection.credentials.get("api_key")
    if not api_key:
        return {"status": "skipped", "reason": "no_api_key"}

    # 2. Get unique subscriber_ids from recent journey_events
    cutoff = datetime.now(UTC) - timedelta(hours=6)
    sub_stmt = (
        select(
            sa_func.jsonb_extract_path_text(
                JourneyEventModel.properties,
                "manychat_subscriber_id",
            ).label("sub_id"),
        )
        .where(
            JourneyEventModel.tenant_id == tenant_id,
            JourneyEventModel.event_name.like("manychat_%"),
            JourneyEventModel.occurred_at >= cutoff,
        )
        .distinct()
    )
    rows = db.execute(sub_stmt).all()
    subscriber_ids = [r.sub_id for r in rows if r.sub_id]

    if not subscriber_ids:
        return {"status": "ok", "enriched": 0, "total": 0}

    # 3. Fetch and enrich each subscriber (rate limited)
    enriched = 0
    errors = 0
    for sub_id in subscriber_ids:
        ok, data = await ManyChatConnector.get_subscriber(api_key, sub_id)
        if ok:
            _enrich_profile(db, tenant_id, data)
            enriched += 1
        else:
            errors += 1
        await asyncio.sleep(0.15)  # ~7 req/s to stay under 10/s limit

    db.commit()

    logger.info(
        "manychat_sync_completed",
        tenant_id=str(tenant_id),
        enriched=enriched,
        errors=errors,
        total=len(subscriber_ids),
    )
    return {"enriched": enriched, "errors": errors, "total": len(subscriber_ids)}


def _enrich_profile(db: Session, tenant_id: UUID, mc_data: dict) -> None:
    """Update CRM customer_profile with ManyChat subscriber data."""
    from src.modules.crm.infrastructure.models.customer_model import (
        CustomerProfileModel,
    )

    email = mc_data.get("email")
    ig_username = mc_data.get("ig_username")

    if not email and not ig_username:
        return

    # Find profile by email
    if email:
        stmt = select(CustomerProfileModel).where(
            CustomerProfileModel.tenant_id == tenant_id,
            CustomerProfileModel.primary_email == email,
        )
    else:
        # Fallback: can't reliably query by ig_username via identities
        return

    profile = db.execute(stmt).scalar_one_or_none()
    if not profile:
        return

    # Merge ManyChat data into profile.traits (JSONB)
    traits = dict(profile.traits) if profile.traits else {}
    traits["manychat"] = {
        "subscriber_id": str(mc_data.get("id", "")),
        "ig_username": ig_username,
        "last_interaction": mc_data.get("last_interaction"),
        "tags": [t.get("name") for t in mc_data.get("tags", [])],
        "custom_fields": {
            cf.get("name"): cf.get("value") for cf in mc_data.get("custom_fields", [])
        },
        "score": next(
            (
                cf.get("value")
                for cf in mc_data.get("custom_fields", [])
                if cf.get("name") == "points"
            ),
            None,
        ),
        "synced_at": datetime.now(UTC).isoformat(),
    }
    profile.traits = traits

    from sqlalchemy.orm.attributes import flag_modified

    flag_modified(profile, "traits")
