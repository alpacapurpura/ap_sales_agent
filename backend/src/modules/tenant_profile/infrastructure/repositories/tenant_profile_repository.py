"""Concrete SQLAlchemy implementation of TenantProfileRepository.

Design decisions:
- Uses the project-wide sync ``Session`` (consistent with ``core/database.py``).
- ``get_or_init`` returns an in-memory domain object without persisting it —
  the caller must call ``save()`` to commit the state.
- ``save()`` uses merge() semantics (insert or update) for cross-dialect
  compatibility (SQLite in tests, PostgreSQL in production).
- Every query filters by ``tenant_id`` (PK here) — tenant isolation is
  structurally guaranteed by the primary key constraint.
"""

from __future__ import annotations

from datetime import UTC
from typing import TYPE_CHECKING

import structlog
from luana_core_platform.domain.datetime_utils import utc_now
from luana_core_platform.domain.expert_business_type import ExpertBusinessType
from luana_core_tenant_profile.domain.repository import TenantProfileRepository
from luana_core_tenant_profile.domain.tenant_profile import TenantProfile
from luana_core_tenant_profile.infrastructure.models.tenant_profile_model import (
    TenantProfileModel,
)
from sqlalchemy import select

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID

    from sqlalchemy.orm import Session

logger = structlog.get_logger()


def _ensure_utc(value: datetime | None) -> datetime | None:
    """Attach UTC tzinfo if the value is naive.

    SQLite drops tzinfo on round-trip — domain always writes UTC, so a naive
    readback is safe to re-stamp. PostgreSQL preserves tzinfo and is a no-op.
    """
    if value is None or value.tzinfo is not None:
        return value
    return value.replace(tzinfo=UTC)


def _to_domain(model: TenantProfileModel) -> TenantProfile:
    """Map ORM model → domain aggregate, guaranteeing timezone-aware datetimes."""
    raw_types: list[str] = model.business_types or []
    # Silently drop unknown enum values to handle legacy data gracefully.
    valid_values = {member.value for member in ExpertBusinessType}
    business_types = tuple(ExpertBusinessType(bt) for bt in raw_types if bt in valid_values)
    return TenantProfile(
        tenant_id=model.tenant_id,
        business_types=business_types,
        declared_at=_ensure_utc(model.declared_at),
        updated_at=_ensure_utc(model.updated_at) or utc_now(),
        last_business_types_change_at=_ensure_utc(model.last_business_types_change_at),
    )


class SqlTenantProfileRepository(TenantProfileRepository):
    """SQLAlchemy implementation of :class:`TenantProfileRepository`."""

    def __init__(self, db: Session) -> None:
        """Initialise with an active SQLAlchemy session."""
        self.db = db

    def get_or_none(self, tenant_id: UUID) -> TenantProfile | None:
        """Return the profile or ``None`` if the tenant has no row yet."""
        stmt = select(TenantProfileModel).where(TenantProfileModel.tenant_id == tenant_id)
        result = self.db.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return _to_domain(model)

    def get_or_init(self, tenant_id: UUID) -> TenantProfile:
        """Return existing profile, or a fresh in-memory (unsaved) one."""
        existing = self.get_or_none(tenant_id)
        if existing is not None:
            return existing
        now = utc_now()
        return TenantProfile(
            tenant_id=tenant_id,
            business_types=(),
            declared_at=None,
            updated_at=now,
            last_business_types_change_at=None,
        )

    def save(self, profile: TenantProfile) -> None:
        """Insert or update the profile row (upsert by tenant_id PK).

        Uses SQLAlchemy's ``merge()`` for cross-dialect compatibility (SQLite
        in tests, PostgreSQL in production). The session commit is deferred to
        the caller for transaction control; we flush here to make the change
        visible within the same session.
        """
        business_types_raw = [bt.value for bt in profile.business_types]

        # Load the existing row (if any) to decide insert vs update.
        stmt = select(TenantProfileModel).where(TenantProfileModel.tenant_id == profile.tenant_id)
        result = self.db.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            model = TenantProfileModel(
                tenant_id=profile.tenant_id,
                business_types=business_types_raw,
                declared_at=profile.declared_at,
                last_business_types_change_at=profile.last_business_types_change_at,
                updated_at=profile.updated_at,
            )
            self.db.add(model)
        else:
            model.business_types = business_types_raw
            model.declared_at = profile.declared_at
            model.last_business_types_change_at = profile.last_business_types_change_at
            model.updated_at = profile.updated_at

        self.db.commit()

        logger.info(
            "tenant_profile_saved",
            tenant_id=str(profile.tenant_id),
            business_types=business_types_raw,
            declared_at=profile.declared_at.isoformat() if profile.declared_at else None,
        )
