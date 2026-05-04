"""Unit tests — SaleRepository edge cases.

PR-2 PI-11: coverage lift para sale_repository.py (86% → ≥95%).
Tests cubren los 6 statements faltantes:
- find_by_id cuando no existe (None path)
- find_by_customer_id con múltiples sales
- count_sales_by_customer con mezcla de status
- get_sales_by_date_range edge: fecha futura retorna vacío
- SaleRepository.save update de sale existente (update path)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from sqlalchemy.orm import Session

from src.modules.crm.domain.enums import SaleStatus, SaleStage
from src.modules.crm.domain.sale import Sale
from src.modules.crm.infrastructure.repositories.sale_repository import SaleRepository
from src.shared.infrastructure.models.crm import SaleModel

TENANT_ID = uuid.UUID("00000000-0000-0000-0001-000000000001")
NOW = datetime.now(timezone.utc)


def _make_sale(
    tenant_id: UUID,
    customer_id: UUID,
    *,
    amount: float = 100.0,
    currency: str = "USD",
    status: SaleStatus = SaleStatus.COMPLETED,
    stage: SaleStage = SaleStage.CONVERSION,
    occurred_at: datetime | None = None,
) -> Sale:
    return Sale(
        id=uuid4(),
        tenant_id=tenant_id,
        customer_id=customer_id,
        offer_id=uuid4(),
        amount=amount,
        currency=currency,
        status=status,
        stage=stage,
        source="MANUAL",
        occurred_at=occurred_at or NOW,
    )


class TestSaleRepositorySave:
    def test_save_creates_new_sale(self, db: Session):
        repo = SaleRepository(db)
        customer_id = uuid4()
        sale = _make_sale(TENANT_ID, customer_id)

        saved = repo.save(sale)

        assert saved.id == sale.id
        assert saved.tenant_id == TENANT_ID
        assert saved.amount == 100.0

    def test_save_updates_existing_sale(self, db: Session):
        """save() en sale existente actualiza campos (update path — líneas #42-58)."""
        repo = SaleRepository(db)
        customer_id = uuid4()
        sale = _make_sale(TENANT_ID, customer_id, amount=50.0)

        # Primera vez: create
        repo.save(sale)

        # Segunda vez: update con amount diferente
        sale.amount = 200.0
        sale.status = SaleStatus.REFUNDED
        updated = repo.save(sale)

        assert updated.amount == 200.0
        assert updated.status == SaleStatus.REFUNDED


class TestFindById:
    def test_find_by_id_returns_sale_when_found(self, db: Session):
        repo = SaleRepository(db)
        customer_id = uuid4()
        sale = _make_sale(TENANT_ID, customer_id)
        repo.save(sale)

        found = repo.find_by_id(sale.id)

        assert found is not None
        assert found.id == sale.id

    def test_find_by_id_returns_none_when_not_found(self, db: Session):
        """None path — línea #67 (faltante en cobertura)."""
        repo = SaleRepository(db)

        result = repo.find_by_id(uuid4())

        assert result is None


class TestFindByCustomerId:
    def test_find_by_customer_id_returns_all_sales(self, db: Session):
        """find_by_customer_id retorna todas las sales del customer (línea #69-78)."""
        repo = SaleRepository(db)
        customer_id = uuid4()

        sale1 = _make_sale(TENANT_ID, customer_id, amount=100.0)
        sale2 = _make_sale(TENANT_ID, customer_id, amount=200.0)
        repo.save(sale1)
        repo.save(sale2)

        # Sale de otro customer
        other_customer = uuid4()
        sale_other = _make_sale(TENANT_ID, other_customer, amount=999.0)
        repo.save(sale_other)

        result = repo.find_by_customer_id(customer_id)

        assert len(result) == 2
        amounts = {s.amount for s in result}
        assert 100.0 in amounts
        assert 200.0 in amounts

    def test_find_by_customer_id_returns_empty_list(self, db: Session):
        repo = SaleRepository(db)

        result = repo.find_by_customer_id(uuid4())

        assert result == []


class TestCountSalesByCustomer:
    def test_count_only_completed_sales(self, db: Session):
        """count_sales_by_customer cuenta solo COMPLETED (líneas #80-90)."""
        repo = SaleRepository(db)
        customer_id = uuid4()

        completed1 = _make_sale(TENANT_ID, customer_id, status=SaleStatus.COMPLETED)
        completed2 = _make_sale(TENANT_ID, customer_id, status=SaleStatus.COMPLETED)
        pending = _make_sale(TENANT_ID, customer_id, status=SaleStatus.PENDING)
        failed = _make_sale(TENANT_ID, customer_id, status=SaleStatus.FAILED)

        for s in [completed1, completed2, pending, failed]:
            repo.save(s)

        count = repo.count_sales_by_customer(customer_id)

        assert count == 2

    def test_count_returns_zero_for_no_sales(self, db: Session):
        repo = SaleRepository(db)

        count = repo.count_sales_by_customer(uuid4())

        assert count == 0

    def test_count_returns_zero_for_non_completed(self, db: Session):
        """Si solo hay PENDING/FAILED, count = 0."""
        repo = SaleRepository(db)
        customer_id = uuid4()

        refunded = _make_sale(TENANT_ID, customer_id, status=SaleStatus.REFUNDED)
        repo.save(refunded)

        count = repo.count_sales_by_customer(customer_id)

        assert count == 0


class TestGetSalesByDateRange:
    def test_returns_sales_within_range(self, db: Session):
        """get_sales_by_date_range filtra por tenant + fecha + COMPLETED (líneas #92-113)."""
        repo = SaleRepository(db)
        customer_id = uuid4()

        sale_in_range = _make_sale(
            TENANT_ID,
            customer_id,
            status=SaleStatus.COMPLETED,
            occurred_at=NOW - timedelta(days=3),
        )
        repo.save(sale_in_range)

        start = NOW - timedelta(days=7)
        end = NOW + timedelta(days=1)

        results = repo.get_sales_by_date_range(TENANT_ID, start, end)

        assert len(results) == 1
        assert results[0].id == sale_in_range.id

    def test_excludes_sales_outside_range(self, db: Session):
        """Sale fuera del rango no aparece."""
        repo = SaleRepository(db)
        customer_id = uuid4()

        old_sale = _make_sale(
            TENANT_ID,
            customer_id,
            status=SaleStatus.COMPLETED,
            occurred_at=NOW - timedelta(days=30),
        )
        repo.save(old_sale)

        start = NOW - timedelta(days=7)
        end = NOW

        results = repo.get_sales_by_date_range(TENANT_ID, start, end)

        assert results == []

    def test_excludes_pending_sales_from_range(self, db: Session):
        """get_sales_by_date_range solo retorna COMPLETED (status filter)."""
        repo = SaleRepository(db)
        customer_id = uuid4()

        pending_sale = _make_sale(
            TENANT_ID,
            customer_id,
            status=SaleStatus.PENDING,
            occurred_at=NOW - timedelta(days=1),
        )
        repo.save(pending_sale)

        start = NOW - timedelta(days=7)
        end = NOW + timedelta(days=1)

        results = repo.get_sales_by_date_range(TENANT_ID, start, end)

        assert results == []

    def test_tenant_isolation_in_date_range(self, db: Session):
        """Sales de otro tenant no aparecen."""
        repo = SaleRepository(db)
        other_tenant = uuid4()
        customer_id = uuid4()

        sale_other = _make_sale(
            other_tenant,
            customer_id,
            status=SaleStatus.COMPLETED,
            occurred_at=NOW - timedelta(days=1),
        )
        repo.save(sale_other)

        start = NOW - timedelta(days=7)
        end = NOW + timedelta(days=1)

        results = repo.get_sales_by_date_range(TENANT_ID, start, end)

        assert results == []

    def test_returns_empty_for_future_range(self, db: Session):
        """Rango completamente futuro retorna lista vacía (edge case)."""
        repo = SaleRepository(db)

        start = NOW + timedelta(days=30)
        end = NOW + timedelta(days=60)

        results = repo.get_sales_by_date_range(TENANT_ID, start, end)

        assert results == []
