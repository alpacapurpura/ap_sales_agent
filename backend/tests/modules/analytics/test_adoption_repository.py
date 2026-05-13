"""Tests for AdoptionMetricsRepository (Stage 5 CRM queries)."""

from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

from luana_core_analytics_engine.infrastructure.repositories.adoption_repository import (
    AdoptionMetricsRepository,
)


def _dt(y: int, m: int, d: int) -> datetime:
    return datetime(y, m, d, tzinfo=timezone.utc)


def _make_repo() -> tuple[AdoptionMetricsRepository, MagicMock]:
    session = MagicMock()
    session.execute.return_value.scalar.return_value = 0
    session.execute.return_value.all.return_value = []
    return AdoptionMetricsRepository(session), session


class TestGetCustomerHealthByOffer:
    def test_empty_returns_empty_list(self) -> None:
        repo, _session = _make_repo()
        result = repo.get_customer_health_by_offer(uuid4(), _dt(2026, 3, 1), _dt(2026, 3, 31))
        assert result == []

    def test_query_executed_once(self) -> None:
        repo, session = _make_repo()
        repo.get_customer_health_by_offer(uuid4(), _dt(2026, 3, 1), _dt(2026, 3, 31))
        session.execute.assert_called_once()


class TestGetAvgTtvByOffer:
    def test_empty_returns_empty_dict(self) -> None:
        repo, session = _make_repo()
        session.execute.return_value.all.return_value = []
        result = repo.get_avg_ttv_by_offer(uuid4(), _dt(2026, 3, 1), _dt(2026, 3, 31))
        assert result == {}

    def test_rows_with_none_ttv_excluded(self) -> None:
        repo, session = _make_repo()
        offer_id = uuid4()
        session.execute.return_value.all.return_value = [
            (offer_id, 5.3),
            (uuid4(), None),  # should be excluded
        ]
        result = repo.get_avg_ttv_by_offer(uuid4(), _dt(2026, 3, 1), _dt(2026, 3, 31))
        assert len(result) == 1
        assert result[str(offer_id)] == 5.3

    def test_ttv_rounded_to_one_decimal(self) -> None:
        repo, session = _make_repo()
        oid = uuid4()
        session.execute.return_value.all.return_value = [(oid, 3.567)]
        result = repo.get_avg_ttv_by_offer(uuid4(), _dt(2026, 3, 1), _dt(2026, 3, 31))
        assert result[str(oid)] == 3.6


class TestGetTotalCustomersAndSales:
    def test_returns_tuple_of_two_ints(self) -> None:
        repo, session = _make_repo()
        session.execute.return_value.scalar.side_effect = [25, 30]
        customers, sales = repo.get_total_customers_and_sales(uuid4(), _dt(2026, 3, 1), _dt(2026, 3, 31))
        assert customers == 25
        assert sales == 30

    def test_none_values_return_zero(self) -> None:
        repo, session = _make_repo()
        session.execute.return_value.scalar.side_effect = [None, None]
        customers, sales = repo.get_total_customers_and_sales(uuid4(), _dt(2026, 3, 1), _dt(2026, 3, 31))
        assert customers == 0
        assert sales == 0

    def test_executes_two_queries(self) -> None:
        repo, session = _make_repo()
        session.execute.return_value.scalar.side_effect = [10, 20]
        repo.get_total_customers_and_sales(uuid4(), _dt(2026, 3, 1), _dt(2026, 3, 31))
        assert session.execute.call_count == 2


class TestGetRefunds:
    def test_empty_returns_defaults(self) -> None:
        repo, session = _make_repo()
        session.execute.return_value.all.return_value = []
        count, amount, currency = repo.get_refunds(uuid4(), _dt(2026, 3, 1), _dt(2026, 3, 31))
        assert count == 0
        assert amount == 0.0
        assert currency == "USD"

    def test_single_currency_summed(self) -> None:
        repo, session = _make_repo()
        session.execute.return_value.all.return_value = [(3, 900.0, "MXN")]
        count, amount, currency = repo.get_refunds(uuid4(), _dt(2026, 3, 1), _dt(2026, 3, 31))
        assert count == 3
        assert amount == 900.0
        assert currency == "MXN"

    def test_multi_currency_picks_highest_count(self) -> None:
        repo, session = _make_repo()
        session.execute.return_value.all.return_value = [
            (5, 1500.0, "MXN"),
            (2, 200.0, "USD"),
        ]
        count, amount, currency = repo.get_refunds(uuid4(), _dt(2026, 3, 1), _dt(2026, 3, 31))
        assert count == 7
        assert amount == 1700.0
        assert currency == "MXN"  # max by count
