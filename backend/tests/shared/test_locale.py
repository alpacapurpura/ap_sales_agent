"""Tests for TenantLocale value object."""

from src.shared.domain.locale import TenantLocale


class TestTenantLocale:
    def test_creation(self) -> None:
        locale = TenantLocale(currency="PEN", timezone="America/Lima")
        assert locale.currency == "PEN"
        assert locale.timezone == "America/Lima"

    def test_frozen_immutable(self) -> None:
        locale = TenantLocale(currency="PEN", timezone="America/Lima")
        try:
            locale.currency = "USD"  # type: ignore[misc]
            raise AssertionError("Should have raised")
        except AttributeError:
            pass

    def test_equality(self) -> None:
        a = TenantLocale(currency="PEN", timezone="America/Lima")
        b = TenantLocale(currency="PEN", timezone="America/Lima")
        assert a == b

    def test_inequality(self) -> None:
        a = TenantLocale(currency="PEN", timezone="America/Lima")
        b = TenantLocale(currency="USD", timezone="UTC")
        assert a != b

    def test_default(self) -> None:
        locale = TenantLocale.default()
        assert locale.currency == "USD"
        assert locale.timezone == "UTC"
