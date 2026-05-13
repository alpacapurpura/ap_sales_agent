"""Tests for ExpansionMetricsRepository (Stage 6 CRM queries)."""

from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

from luana_core_analytics_engine.infrastructure.repositories.expansion_repository import (
    ExpansionMetricsRepository,
)


def _dt(y: int, m: int, d: int) -> datetime:
    return datetime(y, m, d, tzinfo=timezone.utc)


def _make_repo() -> tuple[ExpansionMetricsRepository, MagicMock]:
    session = MagicMock()
    session.execute.return_value.scalar.return_value = 0
    session.execute.return_value.all.return_value = []
    return ExpansionMetricsRepository(session), session


class TestGetExpansionSalesGrouped:
    def test_empty_db_returns_empty_dicts(self) -> None:
        repo, session = _make_repo()
        session.execute.return_value.all.return_value = []
        result = repo.get_expansion_sales_grouped(uuid4(), _dt(2026, 3, 1), _dt(2026, 3, 31))
        assert result == {"renewals": [], "upsells": []}

    def test_rows_mapped_to_tuples(self) -> None:
        repo, session = _make_repo()
        offer_id = uuid4()
        session.execute.return_value.all.side_effect = [
            [(offer_id, 3, 9000.0, "MXN")],  # renewals
            [(offer_id, 2, 4000.0, "MXN")],  # upsells
        ]
        result = repo.get_expansion_sales_grouped(uuid4(), _dt(2026, 3, 1), _dt(2026, 3, 31))
        assert len(result["renewals"]) == 1
        assert result["renewals"][0] == (offer_id, 3, 9000.0, "MXN")
        assert len(result["upsells"]) == 1

    def test_execute_called_twice(self) -> None:
        repo, session = _make_repo()
        session.execute.return_value.all.return_value = []
        repo.get_expansion_sales_grouped(uuid4(), _dt(2026, 3, 1), _dt(2026, 3, 31))
        assert session.execute.call_count == 2  # renewals + upsells


class TestGetChurnData:
    def test_empty_returns_empty_list(self) -> None:
        repo, session = _make_repo()
        session.execute.return_value.all.return_value = []
        result = repo.get_churn_data_by_offer(uuid4(), _dt(2026, 3, 1), _dt(2026, 3, 31))
        assert result == []

    def test_rows_mapped(self) -> None:
        repo, session = _make_repo()
        offer_id = uuid4()
        session.execute.return_value.all.return_value = [(offer_id, 5, 15000.0, "MXN")]
        result = repo.get_churn_data_by_offer(uuid4(), _dt(2026, 3, 1), _dt(2026, 3, 31))
        assert result[0] == (offer_id, 5, 15000.0, "MXN")


class TestGetTotalChurnCount:
    def test_returns_scalar(self) -> None:
        repo, session = _make_repo()
        session.execute.return_value.scalar.return_value = 12
        result = repo.get_total_churn_count(uuid4(), _dt(2026, 3, 1), _dt(2026, 3, 31))
        assert result == 12

    def test_none_returns_zero(self) -> None:
        repo, session = _make_repo()
        session.execute.return_value.scalar.return_value = None
        result = repo.get_total_churn_count(uuid4(), _dt(2026, 3, 1), _dt(2026, 3, 31))
        assert result == 0


class TestGetActiveCustomerCount:
    def test_returns_count(self) -> None:
        repo, session = _make_repo()
        session.execute.return_value.scalar.return_value = 42
        result = repo.get_active_customer_count(uuid4())
        assert result == 42

    def test_none_returns_zero(self) -> None:
        repo, session = _make_repo()
        session.execute.return_value.scalar.return_value = None
        result = repo.get_active_customer_count(uuid4())
        assert result == 0


class TestGetAvgLtv:
    def test_returns_avg_and_currency(self) -> None:
        repo, session = _make_repo()
        session.execute.return_value.scalar.side_effect = [1500.5, "MXN"]
        avg, currency = repo.get_avg_ltv(uuid4())
        assert avg == 1500.5
        assert currency == "MXN"

    def test_none_avg_returns_zero(self) -> None:
        repo, session = _make_repo()
        session.execute.return_value.scalar.side_effect = [None, None]
        avg, currency = repo.get_avg_ltv(uuid4())
        assert avg == 0.0
        assert currency == "MXN"  # default


class TestGetExpansionCustomerCount:
    def test_returns_count(self) -> None:
        repo, session = _make_repo()
        session.execute.return_value.scalar.return_value = 8
        result = repo.get_expansion_customer_count(uuid4(), _dt(2026, 3, 1), _dt(2026, 3, 31))
        assert result == 8

    def test_none_returns_zero(self) -> None:
        repo, session = _make_repo()
        session.execute.return_value.scalar.return_value = None
        result = repo.get_expansion_customer_count(uuid4(), _dt(2026, 3, 1), _dt(2026, 3, 31))
        assert result == 0
