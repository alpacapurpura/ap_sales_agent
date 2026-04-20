"""Domain events for the tenant_profile bounded context.

These events are raised by :class:`TenantProfile` commands and dispatched by the
application service to in-process subscribers (e.g. WebSocket broadcast for
cache invalidation) and future async subscribers (landing cache, agent rebuild).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.shared.domain.expert_business_type import ExpertBusinessType


@dataclass(frozen=True)
class TenantProfileInitialized:
    """Raised on the first-time declaration of business_types.

    Preconditions: ``declared_at`` was ``None`` before the update.
    Never rate-limited — first declaration is always allowed.
    """

    tenant_id: UUID
    business_types: tuple[ExpertBusinessType, ...]
    at: datetime


@dataclass(frozen=True)
class BusinessTypesChanged:
    """Raised when an already-declared profile changes its business_types.

    Consumers must invalidate:
    - ``['offer-type-presets', business_types]``
    - ``['offer-formats', business_types, archetype]``
    - ``['tenant-profile']``
    """

    tenant_id: UUID
    old: tuple[ExpertBusinessType, ...]
    new: tuple[ExpertBusinessType, ...]
    at: datetime
