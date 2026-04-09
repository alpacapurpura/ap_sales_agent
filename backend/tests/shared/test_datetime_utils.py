"""Tests for shared datetime utilities."""

from datetime import UTC, datetime

import pytest

from src.shared.domain.datetime_utils import (
    ensure_utc,
    is_valid_timezone,
    to_tenant_tz,
    utc_now,
)


class TestUtcNow:
    def test_returns_aware_datetime(self) -> None:
        result = utc_now()
        assert result.tzinfo is not None

    def test_is_utc(self) -> None:
        result = utc_now()
        assert result.tzinfo == UTC


class TestToTenantTz:
    def test_utc_to_lima(self) -> None:
        dt = datetime(2026, 4, 9, 0, 0, 0, tzinfo=UTC)
        result = to_tenant_tz(dt, "America/Lima")
        assert result.hour == 19
        assert result.day == 8

    def test_utc_to_bogota(self) -> None:
        dt = datetime(2026, 4, 9, 12, 0, 0, tzinfo=UTC)
        result = to_tenant_tz(dt, "America/Bogota")
        assert result.hour == 7

    def test_naive_input_assumed_utc(self) -> None:
        dt = datetime(2026, 4, 9, 5, 0, 0)  # noqa: DTZ001 — intentionally naive to test assumption
        result = to_tenant_tz(dt, "America/Lima")
        assert result.hour == 0

    def test_utc_stays_utc(self) -> None:
        dt = datetime(2026, 4, 9, 12, 0, 0, tzinfo=UTC)
        result = to_tenant_tz(dt, "UTC")
        assert result.hour == 12


class TestEnsureUtc:
    def test_naive_gets_utc(self) -> None:
        dt = datetime(2026, 4, 9, 12, 0, 0)  # noqa: DTZ001 — intentionally naive to test assumption
        result = ensure_utc(dt)
        assert result.tzinfo == UTC
        assert result.hour == 12

    def test_aware_non_utc_converts(self) -> None:
        from zoneinfo import ZoneInfo

        lima = ZoneInfo("America/Lima")
        dt = datetime(2026, 4, 9, 7, 0, 0, tzinfo=lima)
        result = ensure_utc(dt)
        assert result.hour == 12

    def test_already_utc_unchanged(self) -> None:
        dt = datetime(2026, 4, 9, 12, 0, 0, tzinfo=UTC)
        result = ensure_utc(dt)
        assert result.hour == 12
        assert result.tzinfo == UTC


class TestIsValidTimezone:
    @pytest.mark.parametrize(
        "tz",
        ["America/Lima", "America/Bogota", "America/Mexico_City", "UTC", "US/Eastern"],
    )
    def test_valid_timezones(self, tz: str) -> None:
        assert is_valid_timezone(tz) is True

    @pytest.mark.parametrize("tz", ["Narnia/Castle", "Invalid", "", "UTC+5"])
    def test_invalid_timezones(self, tz: str) -> None:
        assert is_valid_timezone(tz) is False
