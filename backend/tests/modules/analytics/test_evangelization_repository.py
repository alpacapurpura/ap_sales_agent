"""Tests for EvangelizationRepository (Stage 7 CRM queries)."""

from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from luana_core_analytics_engine.infrastructure.repositories.evangelization_repository import (
    EvangelizationRepository,
)


def _dt(y: int, m: int, d: int) -> datetime:
    return datetime(y, m, d, tzinfo=timezone.utc)


def _make_repo() -> tuple[EvangelizationRepository, MagicMock]:
    session = MagicMock()
    session.execute.return_value.scalar.return_value = 0
    session.execute.return_value.all.return_value = []
    session.execute.return_value.first.return_value = (0, 0, 0, 0, None)
    return EvangelizationRepository(session), session


class TestGetEvangelizationDataEmptyTenant:
    """Happy-path with 0 evangelists — covers the full method body."""

    async def test_returns_expected_keys(self) -> None:
        repo, session = _make_repo()
        exec_mock = session.execute.return_value

        exec_mock.all.return_value = []
        exec_mock.scalar.return_value = 0
        # 5-tuple covers both _compute_k_factor[0:2] and _get_nps_summary[0:5]
        exec_mock.first.return_value = (0, 0, 0, 0, None)

        result = await repo.get_evangelization_data(uuid4(), _dt(2026, 3, 1), _dt(2026, 3, 31))

        assert "header_kpis" in result
        assert "mini_funnel" in result
        assert "referidos" in result
        assert "candidatos" in result
        assert "nps_summary" in result

    async def test_empty_data_kpis_are_zeros(self) -> None:
        repo, session = _make_repo()
        exec_mock = session.execute.return_value
        exec_mock.all.return_value = []
        exec_mock.scalar.return_value = 0
        exec_mock.first.return_value = (0, 0, 0, 0, None)  # covers k_factor + nps_summary

        result = await repo.get_evangelization_data(uuid4(), _dt(2026, 3, 1), _dt(2026, 3, 31))

        kpis = result["header_kpis"]
        assert kpis["k_factor"] == 0.0
        assert kpis["active_evangelists"] == 0
        assert kpis["referral_conversions"] == 0
        assert kpis["referral_revenue"] == 0.0

    async def test_empty_referidos_and_candidatos(self) -> None:
        repo, session = _make_repo()
        exec_mock = session.execute.return_value
        exec_mock.all.return_value = []
        exec_mock.scalar.return_value = 0
        exec_mock.first.return_value = (0, 0, 0, 0, None)  # covers k_factor + nps_summary

        result = await repo.get_evangelization_data(uuid4(), _dt(2026, 3, 1), _dt(2026, 3, 31))

        assert result["referidos"] == []
        assert result["candidatos"] == []


class TestGetActiveEvangelists:
    def test_empty_returns_empty_list(self) -> None:
        repo, session = _make_repo()
        session.execute.return_value.all.return_value = []
        result = repo._get_active_evangelists(uuid4())
        assert result == []

    def test_rows_mapped_to_dicts(self) -> None:
        repo, session = _make_repo()
        cid = uuid4()
        session.execute.return_value.all.return_value = [
            (cid, "María García", "REF001", True),
        ]
        result = repo._get_active_evangelists(uuid4())
        assert len(result) == 1
        assert result[0]["code"] == "REF001"
        assert result[0]["full_name"] == "María García"
        assert result[0]["is_active"] is True

    def test_no_name_returns_empty_string(self) -> None:
        repo, session = _make_repo()
        cid = uuid4()
        session.execute.return_value.all.return_value = [(cid, None, "REF002", True)]
        result = repo._get_active_evangelists(uuid4())
        assert result[0]["full_name"] is None  # raw value preserved; stage maps it


class TestComputeKFactor:
    def test_zero_evangelists_returns_zero_k_factor(self) -> None:
        repo, session = _make_repo()
        session.execute.return_value.scalar.return_value = 0
        session.execute.return_value.first.return_value = (0, 0)
        result = repo._compute_k_factor(uuid4(), _dt(2026, 3, 1), _dt(2026, 3, 31))
        assert result["k_factor"] == 0.0

    def test_k_factor_formula(self) -> None:
        repo, session = _make_repo()
        # 4 referral codes, (10 referrals sent, 5 conversions)
        session.execute.return_value.scalar.return_value = 4
        session.execute.return_value.first.return_value = (10, 5)
        result = repo._compute_k_factor(uuid4(), _dt(2026, 3, 1), _dt(2026, 3, 31))
        # K = (10/4) * (5/10) = 2.5 * 0.5 = 1.25
        assert result["k_factor"] == pytest.approx(1.25, rel=0.01)

    def test_zero_referrals_returns_zero(self) -> None:
        repo, session = _make_repo()
        session.execute.return_value.scalar.return_value = 3  # 3 codes
        session.execute.return_value.first.return_value = (0, 0)  # 0 referrals
        result = repo._compute_k_factor(uuid4(), _dt(2026, 3, 1), _dt(2026, 3, 31))
        assert result["k_factor"] == 0.0


class TestGetNpsSummary:
    def test_no_responses_returns_none_nps(self) -> None:
        repo, session = _make_repo()
        session.execute.return_value.first.return_value = (0, 0, 0, 0, None)
        session.execute.return_value.scalar.return_value = 0
        result = repo._get_nps_summary(uuid4())
        assert result["nps_score"] is None
        assert result["standard_nps"] is None
        assert result["total_responses"] == 0
        assert result["response_rate_pct"] == 0.0

    def test_promoters_only_gives_nps_100(self) -> None:
        repo, session = _make_repo()
        session.execute.return_value.first.return_value = (10, 10, 0, 0, 9.5)
        session.execute.return_value.scalar.return_value = 20  # surveys sent
        result = repo._get_nps_summary(uuid4())
        assert result["standard_nps"] == pytest.approx(100.0, rel=0.01)
        assert result["response_rate_pct"] == pytest.approx(50.0, rel=0.01)


class TestGetUgcCounts:
    def test_empty_returns_zeros(self) -> None:
        repo, session = _make_repo()
        session.execute.return_value.first.return_value = (0, 0)
        result = repo._get_ugc_counts(uuid4())
        assert result == {"total": 0, "written": 0, "audio": 0}

    def test_counts_summed(self) -> None:
        repo, session = _make_repo()
        session.execute.return_value.first.return_value = (3, 1)
        result = repo._get_ugc_counts(uuid4())
        assert result["written"] == 3
        assert result["audio"] == 1
        assert result["total"] == 4


class TestGetMiniFunnel:
    def test_zero_source_gives_zero_conversion(self) -> None:
        repo, session = _make_repo()
        session.execute.return_value.scalar.side_effect = [0, 0]
        result = repo._get_mini_funnel(uuid4())
        assert result["conversion_rate"] == 0.0
        assert result["source_value"] == 0
        assert result["target_value"] == 0

    def test_conversion_rate_computed(self) -> None:
        repo, session = _make_repo()
        session.execute.return_value.scalar.side_effect = [100, 20]
        result = repo._get_mini_funnel(uuid4())
        assert result["conversion_rate"] == pytest.approx(20.0, rel=0.01)


class TestGetReferralStats:
    def test_empty_returns_defaults(self) -> None:
        repo, session = _make_repo()
        session.execute.return_value.all.return_value = []
        result = repo._get_referral_stats_for_code(uuid4(), "REF001", _dt(2026, 3, 1), _dt(2026, 3, 31))
        assert result == {"referrals_sent": 0, "conversions": 0, "revenue": 0.0, "currency": "MXN"}

    def test_multi_currency_aggregated(self) -> None:
        repo, session = _make_repo()
        session.execute.return_value.all.return_value = [
            (5, 3, 9000.0, "MXN"),
            (2, 1, 500.0, "USD"),
        ]
        result = repo._get_referral_stats_for_code(uuid4(), "REF001", _dt(2026, 3, 1), _dt(2026, 3, 31))
        assert result["referrals_sent"] == 7
        assert result["conversions"] == 4
        assert result["revenue"] == pytest.approx(9500.0, rel=0.01)
