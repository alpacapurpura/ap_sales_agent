"""Tests for TenantSubscription value object — domain layer."""

from __future__ import annotations

import datetime as dt
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.shared.billing.domain.subscription import TenantSubscription


def _now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _basic_sub(**overrides) -> TenantSubscription:
    now = _now()
    defaults = {
        "tenant_id": uuid4(),
        "plan_id": "free",
        "activated_at": now,
        "updated_at": now,
    }
    defaults.update(overrides)
    return TenantSubscription(**defaults)


class TestTenantSubscriptionInvariants:
    def test_basic_sub_creates_ok(self) -> None:
        sub = _basic_sub()
        assert sub.plan_id == "free"
        assert sub.cycle_anchor_day == 1
        assert sub.custom_overrides == {}
        assert sub.trial_ends_at is None
        assert sub.deleted_at is None

    def test_cycle_anchor_day_lower_bound(self) -> None:
        sub = _basic_sub(cycle_anchor_day=1)
        assert sub.cycle_anchor_day == 1

    def test_cycle_anchor_day_upper_bound(self) -> None:
        sub = _basic_sub(cycle_anchor_day=28)
        assert sub.cycle_anchor_day == 28

    def test_cycle_anchor_day_below_1_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _basic_sub(cycle_anchor_day=0)

    def test_cycle_anchor_day_above_28_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _basic_sub(cycle_anchor_day=29)

    def test_custom_overrides_roundtrip(self) -> None:
        overrides = {"llm_budget_total_usd": 50, "max_outbound_msg_per_day": 5000}
        sub = _basic_sub(custom_overrides=overrides)
        assert sub.custom_overrides == overrides

    def test_trial_ends_at_nullable(self) -> None:
        future = _now() + dt.timedelta(days=14)
        sub = _basic_sub(trial_ends_at=future)
        assert sub.trial_ends_at == future

    def test_frozen_model(self) -> None:
        sub = _basic_sub()
        with pytest.raises((TypeError, AttributeError, ValidationError)):
            sub.plan_id = "ultra"  # type: ignore[misc]
