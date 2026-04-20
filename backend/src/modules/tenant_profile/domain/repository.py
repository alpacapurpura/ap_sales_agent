"""Repository interface (abstract) for the tenant_profile bounded context.

The concrete implementation lives in ``infrastructure/repositories/``.
The domain layer only knows the interface — infrastructure details are
invisible here.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uuid import UUID

    from src.modules.tenant_profile.domain.tenant_profile import TenantProfile


class TenantProfileRepository(ABC):
    """Abstract repository for :class:`TenantProfile` persistence.

    All implementations must be tenant-scoped: every method that performs a
    database lookup MUST filter by ``tenant_id``.
    """

    @abstractmethod
    def get_or_none(self, tenant_id: UUID) -> TenantProfile | None:
        """Return the profile for ``tenant_id``, or ``None`` if not found."""
        ...

    @abstractmethod
    def get_or_init(self, tenant_id: UUID) -> TenantProfile:
        """Return the profile for ``tenant_id`` or a fresh (empty) profile.

        A fresh profile has ``declared_at=None`` and ``business_types=()``,
        signalling that onboarding has not been completed. The returned profile
        is NOT persisted until :meth:`save` is called.
        """
        ...

    @abstractmethod
    def save(self, profile: TenantProfile) -> None:
        """Persist (insert or update) the aggregate state."""
        ...
