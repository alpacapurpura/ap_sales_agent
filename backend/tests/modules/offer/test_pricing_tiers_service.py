"""Service + persistence tests for Phase 4 pricing tiers."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

import pytest

from luana_core_offer_studio.application.launch_edition_service import LaunchEditionService

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.orm import Session
from luana_core_offer_studio.domain.launch_edition import PricingTier
from luana_core_offer_studio.domain.offer import PricingStructure
from tests.modules.offer.conftest import create_product_model


def _make_offer(db: Session, tenant_id: uuid.UUID) -> uuid.UUID:
    model = create_product_model(
        tenant_id,
        archetype="experiencia",
        pricing=[{"label": "Base", "total_amount": 500.0, "plan_type": "one_time"}],
        currency="USD",
    )
    db.add(model)
    db.flush()
    return model.id


def _tier(
    label: str,
    *,
    amount: float,
    valid_from: datetime | None = None,
    valid_until: datetime | None = None,
    sort_order: int = 0,
) -> PricingTier:
    return PricingTier(
        label=label,
        pricing=[PricingStructure(label=label, total_amount=amount)],
        valid_from=valid_from,
        valid_until=valid_until,
        sort_order=sort_order,
    )


class TestResolveEffectivePricingFull:
    def test_active_tier_wins_over_override_and_offer(
        self,
        db: Session,
        tenant_a: uuid.UUID,
    ) -> None:
        offer_id = _make_offer(db, tenant_a)
        svc = LaunchEditionService(db)

        early = _tier(
            "early",
            amount=300.0,
            valid_until=datetime(2026, 5, 1, tzinfo=timezone.utc),
            sort_order=0,
        )
        regular = _tier(
            "regular",
            amount=400.0,
            valid_from=datetime(2026, 5, 1, tzinfo=timezone.utc),
            valid_until=datetime(2026, 5, 14, tzinfo=timezone.utc),
            sort_order=1,
        )

        edition = svc.create_edition(
            offer_id=offer_id,
            tenant_id=tenant_a,
            start_date=datetime(2026, 5, 1, tzinfo=timezone.utc),
            pricing_tiers=[early, regular],
        )

        frozen_now = datetime(2026, 5, 7, tzinfo=timezone.utc)
        pricing, currency, active = svc.resolve_effective_pricing_full(
            edition,
            tenant_a,
            now=frozen_now,
        )

        assert active is not None
        assert active.label == "regular"
        assert pricing[0]["total_amount"] == 400.0
        assert currency == "USD"

    def test_falls_back_to_override_when_no_active_tier(
        self,
        db: Session,
        tenant_a: uuid.UUID,
    ) -> None:
        offer_id = _make_offer(db, tenant_a)
        svc = LaunchEditionService(db)

        edition = svc.create_edition(
            offer_id=offer_id,
            tenant_id=tenant_a,
            start_date=datetime(2026, 5, 1, tzinfo=timezone.utc),
            pricing_override=[PricingStructure(label="override", total_amount=350.0)],
        )

        pricing, _, active = svc.resolve_effective_pricing_full(edition, tenant_a)

        assert active is None
        assert pricing[0]["total_amount"] == 350.0

    def test_falls_back_to_offer_pricing_when_no_override_and_no_tiers(
        self,
        db: Session,
        tenant_a: uuid.UUID,
    ) -> None:
        offer_id = _make_offer(db, tenant_a)
        svc = LaunchEditionService(db)

        edition = svc.create_edition(
            offer_id=offer_id,
            tenant_id=tenant_a,
            start_date=datetime(2026, 5, 1, tzinfo=timezone.utc),
        )

        pricing, _, active = svc.resolve_effective_pricing_full(edition, tenant_a)

        assert active is None
        assert pricing[0]["total_amount"] == 500.0


class TestPersistence:
    def test_pricing_tiers_roundtrip(self, db: Session, tenant_a: uuid.UUID) -> None:
        offer_id = _make_offer(db, tenant_a)
        svc = LaunchEditionService(db)

        tiers = [
            _tier(
                "early",
                amount=300.0,
                valid_until=datetime(2026, 5, 1, tzinfo=timezone.utc),
                sort_order=0,
            ),
            _tier(
                "regular",
                amount=400.0,
                valid_from=datetime(2026, 5, 1, tzinfo=timezone.utc),
                sort_order=1,
            ),
        ]

        created = svc.create_edition(
            offer_id=offer_id,
            tenant_id=tenant_a,
            start_date=datetime(2026, 5, 1, tzinfo=timezone.utc),
            pricing_tiers=tiers,
        )

        fetched = svc.get_edition(created.id, tenant_a)

        assert fetched is not None
        assert len(fetched.pricing_tiers) == 2
        labels = [t.label for t in fetched.pricing_tiers]
        assert labels == ["early", "regular"]
        assert fetched.pricing_tiers[0].pricing[0].total_amount == 300.0

    def test_update_rejects_overlapping_tiers(self, db: Session, tenant_a: uuid.UUID) -> None:
        offer_id = _make_offer(db, tenant_a)
        svc = LaunchEditionService(db)

        edition = svc.create_edition(
            offer_id=offer_id,
            tenant_id=tenant_a,
            start_date=datetime(2026, 5, 1, tzinfo=timezone.utc),
        )

        overlap_a = _tier(
            "a",
            amount=100.0,
            valid_from=datetime(2026, 5, 1, tzinfo=timezone.utc),
            valid_until=datetime(2026, 5, 10, tzinfo=timezone.utc),
        )
        overlap_b = _tier(
            "b",
            amount=200.0,
            valid_from=datetime(2026, 5, 5, tzinfo=timezone.utc),
            valid_until=datetime(2026, 5, 15, tzinfo=timezone.utc),
        )

        with pytest.raises(ValueError, match="overlap"):
            svc.update_edition(
                edition.id,
                tenant_a,
                {"pricing_tiers": [overlap_a, overlap_b]},
            )
