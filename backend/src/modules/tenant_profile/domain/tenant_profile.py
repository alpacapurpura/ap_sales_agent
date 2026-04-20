"""Aggregate root for the tenant_profile bounded context.

Ownership: this dataclass is the single source of truth for ``business_types``
in the entire platform. No other module may declare a field with this name in
a domain dataclass or Pydantic model (enforced by
``tests/architecture/test_business_types_ssot.py``).

Business rules (§8 of CONTRACT.md):
- Min entries: 1 — a tenant must declare at least one type.
- Max entries: 2 — product decision (tunable via ``BUSINESS_TYPES_MAX``).
- No duplicates — enforced by the command method.
- Rate limit: 30 days between changes (``RATE_LIMIT_WINDOW``).
- First-time declaration (``declared_at is None``) is never rate-limited.
- No-op write (same set) does not reset the clock and emits no event.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID

from src.modules.tenant_profile.domain.events import (
    BusinessTypesChanged,
    TenantProfileInitialized,
)
from src.modules.tenant_profile.domain.exceptions import (
    BusinessTypesChangeRateLimitedError,
)
from src.shared.domain.datetime_utils import utc_now
from src.shared.domain.expert_business_type import ExpertBusinessType

# Business-rule constants — product-tunable, change here only.
BUSINESS_TYPES_MIN: int = 1
BUSINESS_TYPES_MAX: int = 2
RATE_LIMIT_WINDOW: timedelta = timedelta(days=30)

# Type alias used in DTOs and the port.
DomainEvent = TenantProfileInitialized | BusinessTypesChanged


@dataclass
class TenantProfile:
    """Aggregate root that captures the tenant's operational classification.

    ``business_types`` is the only field today; the aggregate is designed to
    accommodate future fields (sector, company_size, stage, goals) without
    requiring a schema migration beyond column adds.

    Invariants are enforced by :meth:`update_business_types` — the single
    command method on the aggregate.
    """

    tenant_id: UUID
    business_types: tuple[ExpertBusinessType, ...]
    declared_at: datetime | None  # None → onboarding not yet completed
    updated_at: datetime
    last_business_types_change_at: datetime | None

    # ── Queries ───────────────────────────────────────────────────────────

    @property
    def is_complete(self) -> bool:
        """True when the tenant has completed onboarding (declared at least one type)."""
        return self.declared_at is not None and len(self.business_types) >= BUSINESS_TYPES_MIN

    def can_change_business_types(self, now: datetime | None = None) -> bool:
        """False while inside the 30-day rate-limit window after the last change.

        First-time declaration (``declared_at is None``) is always allowed.
        The anchor is ``last_business_types_change_at`` when set, otherwise
        ``declared_at`` (handles the edge case where a profile was initialized
        without tracking the change timestamp separately).
        """
        if self.declared_at is None:
            return True
        anchor = self.last_business_types_change_at or self.declared_at
        return (now or utc_now()) - anchor >= RATE_LIMIT_WINDOW

    def next_allowed_change_at(self) -> datetime | None:
        """Absolute UTC timestamp after which a new change is permitted.

        Returns ``None`` when there is no restriction (never declared).
        """
        anchor = self.last_business_types_change_at or self.declared_at
        return anchor + RATE_LIMIT_WINDOW if anchor else None

    # ── Command ───────────────────────────────────────────────────────────

    def update_business_types(
        self,
        new: tuple[ExpertBusinessType, ...],
        *,
        now: datetime | None = None,
    ) -> list[DomainEvent]:
        """Declare or change the tenant's business_types.

        Args:
            new: The desired tuple of ``ExpertBusinessType`` values.
            now: Override for "current time" (testing). Defaults to ``utc_now()``.

        Returns:
            A list of domain events to be published. Empty when the write is
            a no-op (same set as current value).

        Raises:
            ValueError: If ``new`` violates length or uniqueness invariants.
            BusinessTypesChangeRateLimitedError: If a change is attempted within
                the 30-day window after the last change.
        """
        if not (BUSINESS_TYPES_MIN <= len(new) <= BUSINESS_TYPES_MAX):
            msg = (
                f"business_types must have between {BUSINESS_TYPES_MIN} "
                f"and {BUSINESS_TYPES_MAX} entries; got {len(new)}"
            )
            raise ValueError(msg)

        if len(set(new)) != len(new):
            msg = "business_types must not contain duplicates"
            raise ValueError(msg)

        now = now or utc_now()

        if self.declared_at is None:
            # First-time declaration — never rate-limited.
            self.business_types = new
            self.declared_at = now
            self.updated_at = now
            self.last_business_types_change_at = now
            return [
                TenantProfileInitialized(
                    tenant_id=self.tenant_id,
                    business_types=new,
                    at=now,
                )
            ]

        if set(self.business_types) == set(new):
            # No-op write — same set, no event, clock not reset.
            return []

        if not self.can_change_business_types(now):
            # next_allowed_change_at() is always non-None at this point because
            # declared_at is set (the ``declared_at is None`` branch returned above).
            next_allowed = self.next_allowed_change_at()
            if next_allowed is None:
                # Defensive: should not happen; declare_at is set at this point.
                msg = "Internal error: rate limit anchor missing despite declared_at being set"
                raise ValueError(msg)
            raise BusinessTypesChangeRateLimitedError(next_allowed_at=next_allowed)

        old = self.business_types
        self.business_types = new
        self.updated_at = now
        self.last_business_types_change_at = now
        return [
            BusinessTypesChanged(
                tenant_id=self.tenant_id,
                old=old,
                new=new,
                at=now,
            )
        ]
