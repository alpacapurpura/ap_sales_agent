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
from sqlalchemy.orm import Session

from src.shared.links.ports.calendar import get_channel_credentials
from src.shared.links.ports.channel_adapter import create_manychat_connector
from src.shared.links.ports.crm_enrichment import (
    enrich_customer_with_manychat_data,
    get_recent_manychat_subscriber_ids,
)

logger = structlog.get_logger()


async def sync_manychat_subscribers(tenant_id: UUID, db: Session) -> dict:
    """Sync recent ManyChat subscribers for a tenant.

    Returns summary dict with counts.
    """
    # 1. Get ManyChat API key via shared port
    creds = get_channel_credentials(db, tenant_id, "manychat")
    if not creds:
        return {"status": "skipped", "reason": "no_connection"}

    api_key = creds.get("api_key")
    if not api_key:
        return {"status": "skipped", "reason": "no_api_key"}

    # 2. Get unique subscriber_ids from recent journey_events
    cutoff = datetime.now(UTC) - timedelta(hours=6)
    subscriber_ids = get_recent_manychat_subscriber_ids(db, tenant_id, cutoff)

    if not subscriber_ids:
        return {"status": "ok", "enriched": 0, "total": 0}

    # 3. Fetch and enrich each subscriber (rate limited)
    manychat_cls = create_manychat_connector()
    enriched = 0
    errors = 0
    for sub_id in subscriber_ids:
        ok, data = await manychat_cls.get_subscriber(api_key, sub_id)
        if ok:
            enrich_customer_with_manychat_data(db, tenant_id, data)
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
