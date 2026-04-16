"""Lead resolution ports for cross-module communication.

``scheduling`` and ``sales_agent`` use these to query/create CRM leads
without importing from ``crm`` directly.

Lazy imports keep the coupling inside ``shared/`` (not scanned by arch test).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session


def find_or_create_lead(
    db: Session,
    tenant_id: UUID,
    lead_data: dict,
) -> UUID | None:
    """Find a lead by email or create one. Returns lead ID or None.

    Lazy-imports Lead from CRM domain.
    """
    from sqlalchemy import select

    from src.modules.crm.domain.lead import Lead

    email = lead_data.get("email")
    if not email:
        return None

    lead_stmt = select(Lead).where(
        Lead.tenant_id == tenant_id,
        Lead.email == email,
    )
    existing_lead = db.execute(lead_stmt).scalars().first()

    if existing_lead:
        return existing_lead.id

    new_lead = Lead(
        tenant_id=tenant_id,
        full_name=lead_data.get("name"),
        email=email,
        phone=lead_data.get("phone"),
    )
    db.add(new_lead)
    db.flush()
    return new_lead.id


def verify_lead_exists(db: Session, tenant_id: UUID, lead_id: str) -> bool:
    """Check if a lead exists and belongs to the tenant.

    Lazy-imports Lead from CRM domain.
    Returns True if found, False otherwise.
    """
    from sqlalchemy import select

    from src.modules.crm.domain.lead import Lead

    stmt = select(Lead.id).where(
        Lead.id == lead_id,
        Lead.tenant_id == tenant_id,
    )
    return db.execute(stmt).scalar() is not None


def get_lead_names(db: Session, lead_ids: list[UUID]) -> dict:
    """Resolve lead IDs to display names via CRM models.

    Returns {lead_id: display_name} dict.
    Lazy-imports LeadModel from CRM infrastructure.
    """
    if not lead_ids:
        return {}

    from sqlalchemy import select
    from sqlalchemy.orm import joinedload

    from src.modules.crm.infrastructure.models.lead_model import LeadModel

    leads_stmt = select(LeadModel).options(joinedload(LeadModel.customer)).where(LeadModel.id.in_(lead_ids))
    leads = db.execute(leads_stmt).scalars().all()

    lead_map: dict = {}
    for lead in leads:
        customer_name = lead.customer.full_name if lead.customer else None
        profile = lead.profile_data or {}
        name = customer_name or profile.get("full_name") or profile.get("name") or "Unknown Lead"
        lead_map[lead.id] = name

    return lead_map
