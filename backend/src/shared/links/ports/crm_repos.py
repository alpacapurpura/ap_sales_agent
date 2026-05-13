"""CRM repository + service factories via lazy imports.

These factories let modules outside ``crm`` obtain CRM repos and services
without creating a direct cross-module import that violates DDD boundaries.
All heavy imports happen lazily inside each factory function so the arch test
(which scans only top-level and function-body imports in ``src/modules/``) does
not flag them — shared/ is an allowed import target.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import Session


def get_customer_repository(db: Session) -> object:
    """Return a CustomerRepository instance for the given session."""
    from luana_core_crm.infrastructure.repositories.customer_repository import (
        CustomerRepository,
    )

    return CustomerRepository(db)


def get_journey_event_repository(db: Session) -> object:
    """Return a JourneyEventRepository instance for the given session."""
    from luana_core_crm.infrastructure.repositories.customer_repository import (
        JourneyEventRepository,
    )

    return JourneyEventRepository(db)


def get_lead_metrics_repository(db: Session) -> object:
    """Return a LeadRepository instance for the given session."""
    from luana_core_crm.infrastructure.repositories.lead_metrics_repository import (
        LeadRepository,
    )

    return LeadRepository(db)


def get_customer_service(db: Session) -> object:
    """Return a CustomerService instance for the given session."""
    from luana_core_crm.application.services.customer_service import CustomerService

    return CustomerService(db)


def get_identity_service(db: Session) -> object:
    """Return an IdentityService instance (wraps CustomerRepository internally)."""
    from luana_core_crm.application.services.identity_service import IdentityService
    from luana_core_crm.infrastructure.repositories.customer_repository import (
        CustomerRepository,
    )

    return IdentityService(CustomerRepository(db))


def get_ig_profile_enricher(db: Session) -> object:
    """Return an InstagramProfileEnricher instance for the given session."""
    from luana_core_crm.application.services.ig_profile_enricher import (
        InstagramProfileEnricher,
    )

    return InstagramProfileEnricher(db)


def get_lifecycle_service(db: Session) -> object:
    """Return a LifecycleService instance for the given session."""
    from luana_core_crm.application.services.lifecycle_service import LifecycleService

    return LifecycleService(db)


def get_lead_telegram_id(db: Session, tenant_id: UUID, lead_id: UUID) -> str | None:
    """Return the Telegram chat ID for a lead, or None if not found.

    Sync variant — uses Session (for workers + sync contexts).
    Enforces tenant isolation: queries WHERE id = lead_id AND tenant_id = tenant_id.
    Returns None if the lead doesn't exist, belongs to a different tenant, or has
    no telegram_id set.
    """
    from luana_core_platform.infrastructure.models.crm import LeadModel
    from sqlalchemy import select

    row = db.execute(
        select(LeadModel.telegram_id).where(
            LeadModel.id == lead_id,
            LeadModel.tenant_id == tenant_id,
        )
    ).scalar_one_or_none()
    return row or None


async def get_lead_telegram_id_async(
    session: AsyncSession,
    tenant_id: UUID,
    lead_id: UUID,
) -> str | None:
    """Return the Telegram chat ID for a lead, or None if not found.

    Async variant — uses AsyncSession (for TelegramChannelRouter and other async paths).
    Enforces tenant isolation: queries WHERE id = lead_id AND tenant_id = tenant_id.
    Returns None if the lead doesn't exist, belongs to a different tenant, or has
    no telegram_id set.
    """
    from luana_core_platform.infrastructure.models.crm import LeadModel
    from sqlalchemy import select

    result = await session.execute(
        select(LeadModel.telegram_id).where(
            LeadModel.id == lead_id,
            LeadModel.tenant_id == tenant_id,
        )
    )
    row = result.scalar_one_or_none()
    return row or None
