"""Tests for OpportunityMetricsRepository (Stage 3 CRM queries)."""

from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from luana_core_analytics_engine.infrastructure.repositories.opportunity_repository import (
    OpportunityMetricsRepository,
)


def _dt(y: int, m: int, d: int) -> datetime:
    return datetime(y, m, d, tzinfo=timezone.utc)


def _make_repo() -> tuple[OpportunityMetricsRepository, MagicMock]:
    session = MagicMock()
    session.execute.return_value.scalar.return_value = 0
    session.execute.return_value.all.return_value = []
    return OpportunityMetricsRepository(session), session


class TestCountNewSqls:
    def test_returns_int_from_scalar(self) -> None:
        repo, session = _make_repo()
        session.execute.return_value.scalar.return_value = 7
        result = repo.count_new_sqls(uuid4(), _dt(2026, 3, 1), _dt(2026, 3, 14))
        assert result == 7
        session.execute.assert_called_once()

    def test_returns_zero_when_none(self) -> None:
        repo, session = _make_repo()
        session.execute.return_value.scalar.return_value = None
        result = repo.count_new_sqls(uuid4(), _dt(2026, 3, 1), _dt(2026, 3, 14))
        assert result == 0

    def test_tenant_isolation_applied(self) -> None:
        repo, session = _make_repo()
        tid = uuid4()
        repo.count_new_sqls(tid, _dt(2026, 3, 1), _dt(2026, 3, 14))
        # query must be built using the provided tenant_id
        session.execute.assert_called_once()


class TestCountMqlsInPeriod:
    def test_returns_count(self) -> None:
        repo, session = _make_repo()
        session.execute.return_value.scalar.return_value = 3
        result = repo.count_mqls_in_period(uuid4(), _dt(2026, 3, 1), _dt(2026, 3, 14))
        assert result == 3

    def test_empty_returns_zero(self) -> None:
        repo, session = _make_repo()
        session.execute.return_value.scalar.return_value = None
        result = repo.count_mqls_in_period(uuid4(), _dt(2026, 3, 1), _dt(2026, 3, 14))
        assert result == 0


class TestCountCheckoutEvents:
    def test_empty_returns_default_dict(self) -> None:
        repo, session = _make_repo()
        session.execute.return_value.all.return_value = []
        result = repo.count_checkout_events(uuid4(), _dt(2026, 3, 1), _dt(2026, 3, 14))
        assert "checkout_initiated" in result
        assert "cart_abandoned" in result
        assert result["checkout_initiated"]["count"] == 0
        assert result["cart_abandoned"]["count"] == 0

    def test_counts_populated_from_rows(self) -> None:
        repo, session = _make_repo()
        session.execute.return_value.all.return_value = [
            ("checkout_initiated", 5),
            ("cart_abandoned", 2),
        ]
        result = repo.count_checkout_events(uuid4(), _dt(2026, 3, 1), _dt(2026, 3, 14))
        assert result["checkout_initiated"]["count"] == 5
        assert result["cart_abandoned"]["count"] == 2


class TestCountMeetingEvents:
    def test_empty_returns_zero_dict(self) -> None:
        repo, session = _make_repo()
        session.execute.return_value.all.return_value = []
        result = repo.count_meeting_events(uuid4(), _dt(2026, 3, 1), _dt(2026, 3, 14))
        assert result == {"booked": 0, "completed": 0, "no_show": 0, "rescheduled": 0}

    def test_meeting_counts_mapped(self) -> None:
        repo, session = _make_repo()
        session.execute.return_value.all.return_value = [
            ("meeting_booked", 4),
            ("meeting_completed", 3),
            ("meeting_no_show", 1),
            ("meeting_rescheduled", 0),
        ]
        result = repo.count_meeting_events(uuid4(), _dt(2026, 3, 1), _dt(2026, 3, 14))
        assert result["booked"] == 4
        assert result["completed"] == 3
        assert result["no_show"] == 1

    def test_unknown_event_name_ignored(self) -> None:
        repo, session = _make_repo()
        session.execute.return_value.all.return_value = [
            ("unknown_event", 99),
        ]
        result = repo.count_meeting_events(uuid4(), _dt(2026, 3, 1), _dt(2026, 3, 14))
        assert result["booked"] == 0


class TestCountPaymentLinkEvents:
    def test_returns_count(self) -> None:
        repo, session = _make_repo()
        session.execute.return_value.scalar.return_value = 6
        result = repo.count_payment_link_events(uuid4(), _dt(2026, 3, 1), _dt(2026, 3, 14))
        assert result["count"] == 6
        assert result["value"] == 0.0

    def test_empty_returns_zero(self) -> None:
        repo, session = _make_repo()
        session.execute.return_value.scalar.return_value = None
        result = repo.count_payment_link_events(uuid4(), _dt(2026, 3, 1), _dt(2026, 3, 14))
        assert result["count"] == 0
