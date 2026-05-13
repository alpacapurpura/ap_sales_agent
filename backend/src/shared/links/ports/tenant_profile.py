"""Cross-module port for read-only tenant_profile access.

Other bounded contexts (sales_agent, landing, analytics) MUST use these
functions instead of importing from ``tenant_profile/`` directly. This preserves
the DDD boundary: only the port is visible across modules.

Lazy imports inside each function prevent circular imports and keep
``shared/`` dependency-free from any ``modules/`` package at import time.

Consumers:
  - ``sales_agent`` — grounding the agent identity document with business context.
  - ``landing`` — template selection fallback when no preset is declared.
  - ``analytics`` — future segmentation (not yet implemented).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uuid import UUID

    from luana_core_platform.domain.expert_business_type import ExpertBusinessType
    from sqlalchemy.orm import Session


def get_tenant_business_types(
    db: Session,
    tenant_id: UUID,
) -> tuple[ExpertBusinessType, ...]:
    """Return the tenant's declared business_types, or an empty tuple.

    Args:
        db: Active SQLAlchemy session.
        tenant_id: The tenant to look up.

    Returns:
        Tuple of :class:`ExpertBusinessType` values, or ``()`` when the tenant
        has no declared profile yet (onboarding not completed).
    """
    from luana_core_tenant_profile.infrastructure.repositories.tenant_profile_repository import (
        SqlTenantProfileRepository,
    )

    profile = SqlTenantProfileRepository(db).get_or_none(tenant_id)
    return profile.business_types if profile is not None else ()


def is_tenant_profile_complete(
    db: Session,
    tenant_id: UUID,
) -> bool:
    """Return True when the tenant has completed the business_types onboarding.

    Args:
        db: Active SQLAlchemy session.
        tenant_id: The tenant to look up.

    Returns:
        ``True`` if ``declared_at`` is set and at least one business_type is
        declared. ``False`` otherwise (new tenant, or incomplete onboarding).
    """
    from luana_core_tenant_profile.infrastructure.repositories.tenant_profile_repository import (
        SqlTenantProfileRepository,
    )

    profile = SqlTenantProfileRepository(db).get_or_none(tenant_id)
    return profile.is_complete if profile is not None else False
