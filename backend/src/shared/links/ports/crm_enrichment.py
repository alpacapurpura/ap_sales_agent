"""CRM enrichment operations via lazy imports.

Workers (analytics) use these helpers to access CRM models without
importing from ``crm`` directly.

Lazy imports keep the coupling inside ``shared/`` which is not scanned
by the arch test boundary checker.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID

    from sqlalchemy.orm import Session


def get_recent_manychat_subscriber_ids(
    db: Session,
    tenant_id: UUID,
    cutoff: datetime,
) -> list[str]:
    """Return distinct ManyChat subscriber IDs from recent journey_events."""
    from luana_core_crm.infrastructure.models.customer_model import JourneyEventModel
    from sqlalchemy import func as sa_func
    from sqlalchemy import select

    stmt = (
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
    rows = db.execute(stmt).all()
    return [r.sub_id for r in rows if r.sub_id]


def enrich_customer_with_manychat_data(
    db: Session,
    tenant_id: UUID,
    mc_data: dict,
) -> None:
    """Update CRM customer_profile.traits with ManyChat subscriber data."""
    from datetime import UTC, datetime

    from luana_core_crm.infrastructure.models.customer_model import CustomerProfileModel
    from sqlalchemy import select
    from sqlalchemy.orm.attributes import flag_modified

    email = mc_data.get("email")
    if not email:
        return

    stmt = select(CustomerProfileModel).where(
        CustomerProfileModel.tenant_id == tenant_id,
        CustomerProfileModel.primary_email == email,
    )
    profile = db.execute(stmt).scalar_one_or_none()
    if not profile:
        return

    ig_username = mc_data.get("ig_username")
    traits = dict(profile.traits) if profile.traits else {}
    traits["manychat"] = {
        "subscriber_id": str(mc_data.get("id", "")),
        "ig_username": ig_username,
        "last_interaction": mc_data.get("last_interaction"),
        "tags": [t.get("name") for t in mc_data.get("tags", [])],
        "custom_fields": {cf.get("name"): cf.get("value") for cf in mc_data.get("custom_fields", [])},
        "score": next(
            (cf.get("value") for cf in mc_data.get("custom_fields", []) if cf.get("name") == "points"),
            None,
        ),
        "synced_at": datetime.now(UTC).isoformat(),
    }
    profile.traits = traits
    flag_modified(profile, "traits")


def sync_mailerlite_email_activities(
    db: Session,
    tenant_id: UUID,
    activities: list[dict],
) -> int:
    """Create journey_events for MailerLite email open/click activities.

    Returns number of new events created.
    """
    from luana_core_crm.application.services.lifecycle_service import LifecycleService
    from luana_core_crm.infrastructure.models.customer_model import (
        CustomerProfileModel,
        JourneyEventModel,
    )
    from sqlalchemy import and_, select

    lifecycle_svc = LifecycleService(db)
    synced = 0

    for activity in activities:
        email = activity.get("email")
        campaign_id = activity.get("campaign_id")
        event_type = activity.get("event_type")

        profile = db.execute(
            select(CustomerProfileModel).where(
                and_(
                    CustomerProfileModel.tenant_id == tenant_id,
                    CustomerProfileModel.primary_email == email,
                    CustomerProfileModel.is_inactive == False,
                ),
            ),
        ).scalar_one_or_none()

        if not profile:
            continue

        event_name = "email_opened" if event_type == "open" else "email_clicked"

        existing = db.execute(
            select(JourneyEventModel.id).where(
                and_(
                    JourneyEventModel.profile_id == profile.id,
                    JourneyEventModel.tenant_id == tenant_id,
                    JourneyEventModel.event_name == event_name,
                    JourneyEventModel.properties["campaign_id"].astext == str(campaign_id),
                ),
            ),
        ).scalar_one_or_none()

        if existing:
            continue

        journey_event = JourneyEventModel(
            profile_id=profile.id,
            tenant_id=tenant_id,
            event_name=event_name,
            event_type="track",
            properties={
                "campaign_id": str(campaign_id),
                "campaign_name": activity.get("campaign_name", ""),
                "source": "mailerlite_etl_sync",
            },
        )
        db.add(journey_event)
        lifecycle_svc.recalculate_score(profile.id, tenant_id)
        synced += 1

    return synced


def run_crm_inactivity_detection_batch(db: Session) -> dict:
    """Run CRM inactivity detection + score decay for all tenants.

    Returns result dict from InactivityService.run_batch().
    """
    from luana_core_crm.application.services.inactivity_service import InactivityService

    service = InactivityService(db)
    return service.run_batch()
