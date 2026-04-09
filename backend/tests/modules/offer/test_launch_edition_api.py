"""Tests for launch_editions API DTOs and response model."""

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from src.modules.offer.api.launch_editions import (
    LaunchEditionCreateDTO,
    LaunchEditionResponse,
)
from src.modules.offer.application.launch_edition_service import (
    LaunchEditionService,
)
from tests.modules.offer.conftest import create_product_model


def _make_offer(db: Session, tenant_id: uuid.UUID) -> uuid.UUID:
    model = create_product_model(
        tenant_id,
        archetype="programa",
        pricing=[{"label": "Base", "total_amount": 497, "plan_type": "one_time"}],
        currency="USD",
    )
    db.add(model)
    db.flush()
    return model.id


class TestLaunchEditionCreateDTO:
    def test_minimal(self):
        dto = LaunchEditionCreateDTO(
            start_date=datetime(2026, 7, 15, tzinfo=timezone.utc),
        )
        assert dto.edition_name is None

    def test_full(self):
        dto = LaunchEditionCreateDTO(
            edition_name="Cohorte #1",
            start_date=datetime(2026, 7, 15, tzinfo=timezone.utc),
            end_date=datetime(2026, 8, 26, tzinfo=timezone.utc),
            timezone="America/Lima",
            capacity=30,
        )
        assert dto.capacity == 30


class TestLaunchEditionResponse:
    def test_from_domain(self, db: Session, tenant_a):
        offer_id = _make_offer(db, tenant_a)
        svc = LaunchEditionService(db)
        edition = svc.create_edition(
            offer_id=offer_id,
            tenant_id=tenant_a,
            start_date=datetime(2026, 7, 15, tzinfo=timezone.utc),
        )
        effective_pricing, currency = svc.resolve_effective_pricing(edition, tenant_a)
        response = LaunchEditionResponse.from_domain(
            edition, effective_pricing, currency
        )
        assert response.edition_name == "Edición #1"
        assert response.effective_pricing[0]["total_amount"] == 497
        assert response.currency == "USD"
        assert response.pricing_override is None
