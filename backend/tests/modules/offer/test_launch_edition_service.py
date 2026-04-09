"""Tests for LaunchEditionService business logic."""

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy.orm import Session

from src.modules.offer.application.launch_edition_service import (
    LaunchEditionService,
)
from src.modules.offer.domain.launch_edition import EditionStatus
from src.modules.offer.domain.offer import PricingStructure
from tests.modules.offer.conftest import create_product_model


def _make_offer(db: Session, tenant_id: uuid.UUID, **kwargs) -> uuid.UUID:
    model = create_product_model(
        tenant_id,
        archetype="programa",
        pricing=[{"label": "Base", "total_amount": 497, "plan_type": "one_time"}],
        currency="USD",
        **kwargs,
    )
    db.add(model)
    db.flush()
    return model.id


class TestCreateEdition:
    def test_create_with_defaults(self, db: Session, tenant_a):
        offer_id = _make_offer(db, tenant_a)
        svc = LaunchEditionService(db)
        edition = svc.create_edition(
            offer_id=offer_id,
            tenant_id=tenant_a,
            start_date=datetime(2026, 7, 15, tzinfo=timezone.utc),
        )
        assert edition.edition_number == 1
        assert edition.edition_name == "Edición #1"
        assert edition.status == EditionStatus.DRAFT

    def test_create_with_custom_name(self, db: Session, tenant_a):
        offer_id = _make_offer(db, tenant_a)
        svc = LaunchEditionService(db)
        edition = svc.create_edition(
            offer_id=offer_id,
            tenant_id=tenant_a,
            edition_name="Cohorte Especial",
            start_date=datetime(2026, 7, 15, tzinfo=timezone.utc),
        )
        assert edition.edition_name == "Cohorte Especial"

    def test_create_for_nonexistent_offer_raises(self, db: Session, tenant_a):
        svc = LaunchEditionService(db)
        with pytest.raises(ValueError, match="not found"):
            svc.create_edition(
                offer_id=uuid.uuid4(),
                tenant_id=tenant_a,
                start_date=datetime(2026, 7, 15, tzinfo=timezone.utc),
            )


class TestResolveEffectivePricing:
    def test_no_override_returns_offer_pricing(self, db: Session, tenant_a):
        offer_id = _make_offer(db, tenant_a)
        svc = LaunchEditionService(db)
        edition = svc.create_edition(
            offer_id=offer_id,
            tenant_id=tenant_a,
            start_date=datetime(2026, 7, 15, tzinfo=timezone.utc),
        )
        pricing, currency = svc.resolve_effective_pricing(edition, tenant_a)
        assert len(pricing) == 1
        assert pricing[0]["total_amount"] == 497
        assert currency == "USD"

    def test_override_returns_edition_pricing(self, db: Session, tenant_a):
        offer_id = _make_offer(db, tenant_a)
        svc = LaunchEditionService(db)
        edition = svc.create_edition(
            offer_id=offer_id,
            tenant_id=tenant_a,
            start_date=datetime(2026, 7, 15, tzinfo=timezone.utc),
            pricing_override=[
                PricingStructure(label="Early Bird", total_amount=397),
            ],
        )
        pricing, currency = svc.resolve_effective_pricing(edition, tenant_a)
        assert len(pricing) == 1
        assert pricing[0]["total_amount"] == 397
        assert currency == "USD"


class TestDuplicateEdition:
    def test_duplicate_increments_number(self, db: Session, tenant_a):
        offer_id = _make_offer(db, tenant_a)
        svc = LaunchEditionService(db)
        original = svc.create_edition(
            offer_id=offer_id,
            tenant_id=tenant_a,
            edition_name="Original",
            start_date=datetime(2026, 7, 15, tzinfo=timezone.utc),
            capacity=30,
        )
        dup = svc.duplicate_edition(original.id, tenant_a)
        assert dup.edition_number == 2
        assert dup.capacity == 30
        assert dup.status == EditionStatus.DRAFT
        assert dup.enrollment_count == 0


class TestListEditions:
    def test_list_returns_non_cancelled(self, db: Session, tenant_a):
        offer_id = _make_offer(db, tenant_a)
        svc = LaunchEditionService(db)
        svc.create_edition(
            offer_id=offer_id,
            tenant_id=tenant_a,
            start_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
        e2 = svc.create_edition(
            offer_id=offer_id,
            tenant_id=tenant_a,
            start_date=datetime(2026, 7, 1, tzinfo=timezone.utc),
        )
        svc.delete_edition(e2.id, tenant_a)
        editions = svc.list_editions(offer_id, tenant_a)
        assert len(editions) == 1
