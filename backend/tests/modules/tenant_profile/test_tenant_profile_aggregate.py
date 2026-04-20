"""Domain invariant tests for :class:`TenantProfile`.

These tests exercise the aggregate root in pure Python — no database, no HTTP.
They cover every business rule documented in CONTRACT.md §8.
"""

from __future__ import annotations

import uuid
from datetime import timedelta

import pytest

from src.modules.tenant_profile.domain.events import (
    BusinessTypesChanged,
    TenantProfileInitialized,
)
from src.modules.tenant_profile.domain.exceptions import BusinessTypesChangeRateLimitedError
from src.modules.tenant_profile.domain.tenant_profile import (
    BUSINESS_TYPES_MAX,
    BUSINESS_TYPES_MIN,
    RATE_LIMIT_WINDOW,
    TenantProfile,
)
from src.shared.domain.datetime_utils import utc_now
from src.shared.domain.expert_business_type import ExpertBusinessType

# Convenient aliases
TYPE_A = ExpertBusinessType.ACADEMIA_INFOPRODUCTOR
TYPE_B = ExpertBusinessType.AGENCIA_FREELANCE
TYPE_C = ExpertBusinessType.CONSULTOR_PROFESIONAL

_TENANT = uuid.UUID("aaaa0000-0000-0000-0000-000000000001")


def _new_profile(tenant_id: uuid.UUID = _TENANT) -> TenantProfile:
    """Helper: fresh profile (onboarding not completed)."""
    return TenantProfile(
        tenant_id=tenant_id,
        business_types=(),
        declared_at=None,
        updated_at=utc_now(),
        last_business_types_change_at=None,
    )


class TestFirstTimeDeclaration:
    """Rules around the first ``update_business_types`` call on an empty profile."""

    def test_first_declaration_succeeds_with_min_entries(self) -> None:
        profile = _new_profile()
        events = profile.update_business_types((TYPE_A,))
        assert len(events) == 1
        assert isinstance(events[0], TenantProfileInitialized)
        assert events[0].business_types == (TYPE_A,)

    def test_first_declaration_emits_initialized_event(self) -> None:
        profile = _new_profile()
        events = profile.update_business_types((TYPE_A,))
        assert isinstance(events[0], TenantProfileInitialized)
        assert events[0].tenant_id == _TENANT

    def test_first_declaration_sets_declared_at(self) -> None:
        profile = _new_profile()
        now = utc_now()
        profile.update_business_types((TYPE_A,), now=now)
        assert profile.declared_at == now

    def test_first_declaration_marks_last_change(self) -> None:
        profile = _new_profile()
        now = utc_now()
        profile.update_business_types((TYPE_A,), now=now)
        assert profile.last_business_types_change_at == now

    def test_first_declaration_is_never_rate_limited(self) -> None:
        """Even with declared_at=None, the first write must not raise."""
        profile = _new_profile()
        # Pass an old now to simulate "would be rate-limited if previously declared"
        old_now = utc_now() - timedelta(days=1)
        events = profile.update_business_types((TYPE_A,), now=old_now)
        assert len(events) == 1

    def test_first_declaration_succeeds_with_max_entries(self) -> None:
        profile = _new_profile()
        events = profile.update_business_types((TYPE_A, TYPE_B))
        assert len(events) == 1


class TestInvariants:
    """Length and uniqueness constraints."""

    def test_zero_entries_raises_value_error(self) -> None:
        profile = _new_profile()
        with pytest.raises(ValueError, match="between"):
            profile.update_business_types(())

    def test_too_many_entries_raises_value_error(self) -> None:
        assert BUSINESS_TYPES_MAX == 2, "Adjust test if constant changes"
        profile = _new_profile()
        with pytest.raises(ValueError, match="between"):
            profile.update_business_types((TYPE_A, TYPE_B, TYPE_C))

    def test_duplicate_entries_raise_value_error(self) -> None:
        profile = _new_profile()
        with pytest.raises(ValueError, match="duplicates"):
            profile.update_business_types((TYPE_A, TYPE_A))

    def test_min_and_max_constants_match_business_rules(self) -> None:
        assert BUSINESS_TYPES_MIN == 1
        assert BUSINESS_TYPES_MAX == 2


class TestRateLimit:
    """Rate-limit window enforcement."""

    def test_change_inside_window_raises_rate_limited(self) -> None:
        """A change attempted 5 days after the last change should be blocked."""
        anchor = utc_now() - timedelta(days=5)
        profile = TenantProfile(
            tenant_id=_TENANT,
            business_types=(TYPE_A,),
            declared_at=anchor,
            updated_at=anchor,
            last_business_types_change_at=anchor,
        )
        with pytest.raises(BusinessTypesChangeRateLimitedError) as exc_info:
            profile.update_business_types((TYPE_B,))

        assert exc_info.value.next_allowed_at is not None

    def test_change_after_window_succeeds(self) -> None:
        """A change 31 days after last change must succeed."""
        anchor = utc_now() - RATE_LIMIT_WINDOW - timedelta(days=1)
        profile = TenantProfile(
            tenant_id=_TENANT,
            business_types=(TYPE_A,),
            declared_at=anchor,
            updated_at=anchor,
            last_business_types_change_at=anchor,
        )
        events = profile.update_business_types((TYPE_B,), now=utc_now())
        assert len(events) == 1
        assert isinstance(events[0], BusinessTypesChanged)

    def test_change_exactly_at_window_boundary_succeeds(self) -> None:
        """A change exactly 30 days after last change must succeed (>= boundary)."""
        anchor = utc_now() - RATE_LIMIT_WINDOW
        profile = TenantProfile(
            tenant_id=_TENANT,
            business_types=(TYPE_A,),
            declared_at=anchor,
            updated_at=anchor,
            last_business_types_change_at=anchor,
        )
        # Pass now = anchor + RATE_LIMIT_WINDOW → difference is exactly 0 days
        boundary_now = anchor + RATE_LIMIT_WINDOW
        events = profile.update_business_types((TYPE_B,), now=boundary_now)
        assert len(events) == 1

    def test_rate_limited_error_carries_next_allowed_at(self) -> None:
        anchor = utc_now() - timedelta(days=10)
        profile = TenantProfile(
            tenant_id=_TENANT,
            business_types=(TYPE_A,),
            declared_at=anchor,
            updated_at=anchor,
            last_business_types_change_at=anchor,
        )
        with pytest.raises(BusinessTypesChangeRateLimitedError) as exc_info:
            profile.update_business_types((TYPE_B,))

        expected = anchor + RATE_LIMIT_WINDOW
        assert exc_info.value.next_allowed_at == expected

    def test_next_allowed_change_at_uses_last_change_anchor(self) -> None:
        """The anchor should be ``last_business_types_change_at``, not ``declared_at``."""
        declared = utc_now() - timedelta(days=40)
        last_change = utc_now() - timedelta(days=10)
        profile = TenantProfile(
            tenant_id=_TENANT,
            business_types=(TYPE_A,),
            declared_at=declared,
            updated_at=declared,
            last_business_types_change_at=last_change,
        )
        # last_change + 30d is in the future → change must be blocked
        with pytest.raises(BusinessTypesChangeRateLimitedError):
            profile.update_business_types((TYPE_B,))


class TestNoOp:
    """No-op write contract (same set → empty events, clock not reset)."""

    def test_same_set_returns_empty_event_list(self) -> None:
        anchor = utc_now() - RATE_LIMIT_WINDOW - timedelta(days=1)
        profile = TenantProfile(
            tenant_id=_TENANT,
            business_types=(TYPE_A,),
            declared_at=anchor,
            updated_at=anchor,
            last_business_types_change_at=anchor,
        )
        events = profile.update_business_types((TYPE_A,))
        assert events == []

    def test_same_set_does_not_reset_last_change_at(self) -> None:
        anchor = utc_now() - RATE_LIMIT_WINDOW - timedelta(days=1)
        profile = TenantProfile(
            tenant_id=_TENANT,
            business_types=(TYPE_A,),
            declared_at=anchor,
            updated_at=anchor,
            last_business_types_change_at=anchor,
        )
        original_last_change = profile.last_business_types_change_at
        profile.update_business_types((TYPE_A,))
        assert profile.last_business_types_change_at == original_last_change

    def test_same_set_regardless_of_order_is_noop(self) -> None:
        """Sets are compared by value, not by order."""
        anchor = utc_now() - RATE_LIMIT_WINDOW - timedelta(days=1)
        profile = TenantProfile(
            tenant_id=_TENANT,
            business_types=(TYPE_A, TYPE_B),
            declared_at=anchor,
            updated_at=anchor,
            last_business_types_change_at=anchor,
        )
        # Same types but reversed order
        events = profile.update_business_types((TYPE_B, TYPE_A))
        assert events == []


class TestBusinessTypesChanged:
    """Events emitted on a real change."""

    def test_change_emits_business_types_changed_event(self) -> None:
        anchor = utc_now() - RATE_LIMIT_WINDOW - timedelta(days=1)
        profile = TenantProfile(
            tenant_id=_TENANT,
            business_types=(TYPE_A,),
            declared_at=anchor,
            updated_at=anchor,
            last_business_types_change_at=anchor,
        )
        events = profile.update_business_types((TYPE_B,))
        assert len(events) == 1
        assert isinstance(events[0], BusinessTypesChanged)
        assert events[0].old == (TYPE_A,)
        assert events[0].new == (TYPE_B,)

    def test_change_updates_last_change_at(self) -> None:
        anchor = utc_now() - RATE_LIMIT_WINDOW - timedelta(days=1)
        profile = TenantProfile(
            tenant_id=_TENANT,
            business_types=(TYPE_A,),
            declared_at=anchor,
            updated_at=anchor,
            last_business_types_change_at=anchor,
        )
        now = utc_now()
        profile.update_business_types((TYPE_B,), now=now)
        assert profile.last_business_types_change_at == now


class TestIsComplete:
    """``is_complete`` property."""

    def test_not_complete_without_declared_at(self) -> None:
        profile = _new_profile()
        assert not profile.is_complete

    def test_complete_after_first_declaration(self) -> None:
        profile = _new_profile()
        profile.update_business_types((TYPE_A,))
        assert profile.is_complete

    def test_can_change_when_not_declared(self) -> None:
        profile = _new_profile()
        assert profile.can_change_business_types()
