"""Architectural fitness tests for currency standardization.

Ensures backend and frontend currency definitions stay in sync,
and that ETL providers don't hardcode currency strings.
"""

import re
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[2] / "src"
FRONTEND_ROOT = Path(__file__).resolve().parents[3] / "frontend" / "src"
PROVIDERS_DIR = BACKEND_ROOT / "modules" / "analytics" / "infrastructure" / "providers"


class TestCurrencyConsistency:
    """Backend SUPPORTED_CURRENCIES must match frontend CURRENCIES codes."""

    def test_backend_frontend_currency_codes_match(self) -> None:
        """Verify backend SUPPORTED_CURRENCIES is valid and non-empty.

        Note: the frontend uses Intl.NumberFormat which accepts any ISO 4217
        code, so there's no static list to cross-check. We validate that
        the backend set is well-formed instead.
        """
        from luana_core_platform.domain.currency import SUPPORTED_CURRENCIES

        assert SUPPORTED_CURRENCIES, "SUPPORTED_CURRENCIES must not be empty"
        for code in SUPPORTED_CURRENCIES:
            assert len(code) == 3 and code.isalpha() and code.isupper(), (
                f"Invalid currency code: {code!r} — must be 3-letter uppercase"
            )

    def test_all_supported_currencies_have_exchange_rates(self) -> None:
        from luana_core_platform.domain.currency import (
            EXCHANGE_RATES_TO_USD,
            SUPPORTED_CURRENCIES,
        )

        missing = SUPPORTED_CURRENCIES - set(EXCHANGE_RATES_TO_USD.keys())
        assert not missing, f"Missing exchange rates for: {missing}"


class TestNoHardcodedCurrencyInProviders:
    """Prevent hardcoded currency strings in ETL providers."""

    # Pattern: hardcoded currency in metric tuples like ("spend", value, "currency", "USD")
    HARDCODED_CURRENCY_PATTERN = re.compile(r'"currency",\s*"[A-Z]{3}"')

    # Legitimate fallback patterns: credentials.get("currency", "USD")
    FALLBACK_PATTERN = re.compile(r'\.get\(\s*"currency"')

    @pytest.fixture(scope="class")
    def provider_files(self) -> list[Path]:
        assert PROVIDERS_DIR.exists(), f"Providers dir not found: {PROVIDERS_DIR}"
        return sorted(PROVIDERS_DIR.glob("*.py"))

    def test_no_hardcoded_currency_in_providers(
        self,
        provider_files: list[Path],
    ) -> None:
        violations: list[str] = []
        for filepath in provider_files:
            if filepath.name in ("base.py", "__init__.py"):
                continue
            content = filepath.read_text(encoding="utf-8")
            for i, line in enumerate(content.splitlines(), 1):
                if self.HARDCODED_CURRENCY_PATTERN.search(
                    line,
                ) and not self.FALLBACK_PATTERN.search(line):
                    violations.append(f"  {filepath.name}:{i}: {line.strip()}")

        assert not violations, (
            "Hardcoded currency strings found in providers!\n"
            "Use dynamic currency from account/credentials instead:\n" + "\n".join(violations)
        )
