# Master Data: TenantLocale Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish a universal master data system (currency + timezone) so every module respects the tenant's locale preferences, with enforcement rules and tests to prevent regressions.

**Architecture:** TenantLocale value object (shared/domain) injected via FastAPI Depends (backend) and React Context (frontend). Backend stores UTC + source currency; frontend converts to tenant timezone/currency for display. Dual-display rules: single-source shows source+tenant, aggregated shows tenant+USD.

**Tech Stack:** Python 3.12 (dataclasses, zoneinfo), FastAPI Depends, Pydantic v2, React Context + React Query, date-fns-tz, Vitest, pytest

**Spec:** `docs/superpowers/specs/2026-04-09-master-data-locale-design.md`

---

## Phase 1: Backend Shared Infrastructure (Tasks 1–5)

### Task 1: TenantLocale Value Object

**Files:**
- Create: `backend/src/shared/domain/locale.py`
- Create: `backend/tests/shared/test_locale.py`

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/shared/test_locale.py`:

```python
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
            assert False, "Should have raised"
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && .venv/bin/pytest tests/shared/test_locale.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.shared.domain.locale'`

- [ ] **Step 3: Write the implementation**

Create `backend/src/shared/domain/locale.py`:

```python
"""TenantLocale — immutable value object for tenant display preferences.

Single source of truth for 'how should this tenant see monetary amounts and dates'.
Backend stores UTC + source currency; TenantLocale drives conversion for display.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class TenantLocale:
    """Immutable tenant display preferences."""

    currency: str  # ISO 4217: "PEN", "USD", "MXN"
    timezone: str  # IANA: "America/Lima", "America/Bogota"

    @classmethod
    def default(cls) -> "TenantLocale":
        """Fallback when tenant settings are unavailable."""
        return cls(currency="USD", timezone="UTC")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && .venv/bin/pytest tests/shared/test_locale.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add backend/src/shared/domain/locale.py backend/tests/shared/test_locale.py
git commit -m "feat(shared): add TenantLocale value object"
```

---

### Task 2: Datetime Utilities

**Files:**
- Create: `backend/src/shared/domain/datetime_utils.py`
- Create: `backend/tests/shared/test_datetime_utils.py`

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/shared/test_datetime_utils.py`:

```python
"""Tests for shared datetime utilities."""

from datetime import UTC, datetime, timezone

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
        # UTC midnight -> Lima is UTC-5 = 7pm previous day
        dt = datetime(2026, 4, 9, 0, 0, 0, tzinfo=UTC)
        result = to_tenant_tz(dt, "America/Lima")
        assert result.hour == 19
        assert result.day == 8

    def test_utc_to_bogota(self) -> None:
        # Bogota is also UTC-5
        dt = datetime(2026, 4, 9, 12, 0, 0, tzinfo=UTC)
        result = to_tenant_tz(dt, "America/Bogota")
        assert result.hour == 7

    def test_naive_input_assumed_utc(self) -> None:
        dt = datetime(2026, 4, 9, 5, 0, 0)  # naive
        result = to_tenant_tz(dt, "America/Lima")
        assert result.hour == 0  # 5 UTC -> 0 Lima

    def test_utc_stays_utc(self) -> None:
        dt = datetime(2026, 4, 9, 12, 0, 0, tzinfo=UTC)
        result = to_tenant_tz(dt, "UTC")
        assert result.hour == 12


class TestEnsureUtc:
    def test_naive_gets_utc(self) -> None:
        dt = datetime(2026, 4, 9, 12, 0, 0)
        result = ensure_utc(dt)
        assert result.tzinfo == UTC
        assert result.hour == 12

    def test_aware_non_utc_converts(self) -> None:
        from zoneinfo import ZoneInfo

        lima = ZoneInfo("America/Lima")
        dt = datetime(2026, 4, 9, 7, 0, 0, tzinfo=lima)  # 7am Lima = 12pm UTC
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && .venv/bin/pytest tests/shared/test_datetime_utils.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write the implementation**

Create `backend/src/shared/domain/datetime_utils.py`:

```python
"""Centralized datetime utilities — replaces ad-hoc datetime.utcnow() usage.

Rules:
- Backend ALWAYS stores UTC.
- Frontend converts to tenant timezone for display.
- Use utc_now() instead of datetime.utcnow() (deprecated Python 3.12+).
"""

from datetime import UTC, datetime
from zoneinfo import ZoneInfo


def utc_now() -> datetime:
    """Timezone-aware UTC now. Drop-in replacement for deprecated datetime.utcnow()."""
    return datetime.now(UTC)


def to_tenant_tz(dt: datetime, tz_name: str) -> datetime:
    """Convert a datetime to the tenant's local timezone for display.

    If the input is naive, it is assumed to be UTC.
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(ZoneInfo(tz_name))


def ensure_utc(dt: datetime) -> datetime:
    """Normalize any datetime to UTC.

    - Naive datetimes are assumed UTC (tzinfo added).
    - Aware datetimes are converted to UTC.
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def is_valid_timezone(tz_name: str) -> bool:
    """Check if a string is a valid IANA timezone identifier."""
    try:
        ZoneInfo(tz_name)
        return True
    except (KeyError, ValueError):
        return False
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && .venv/bin/pytest tests/shared/test_datetime_utils.py -v`
Expected: all passed

- [ ] **Step 5: Commit**

```bash
git add backend/src/shared/domain/datetime_utils.py backend/tests/shared/test_datetime_utils.py
git commit -m "feat(shared): add centralized datetime utilities (utc_now, to_tenant_tz)"
```

---

### Task 3: Extend Currency Utilities (Bidirectional Conversion + Display Builders)

**Files:**
- Modify: `backend/src/shared/domain/currency.py`
- Modify: `backend/tests/shared/test_currency.py`

- [ ] **Step 1: Write the failing tests**

Append to `backend/tests/shared/test_currency.py`:

```python
from src.shared.domain.currency import (
    AggregatedMoneyDisplay,
    MoneyDisplay,
    build_aggregated_display,
    build_money_display,
    convert_currency,
)


class TestConvertCurrency:
    """Bidirectional conversion via USD pivot."""

    def test_same_currency_identity(self) -> None:
        assert convert_currency(500.0, "PEN", "PEN") == 500.0

    def test_pen_to_usd(self) -> None:
        result = convert_currency(100.0, "PEN", "USD")
        assert result is not None
        # 100 PEN * 0.27 (PEN->USD rate) = 27.0 USD
        assert result == 27.0

    def test_usd_to_pen(self) -> None:
        result = convert_currency(27.0, "USD", "PEN")
        assert result is not None
        # 27 USD / 0.27 = 100 PEN
        assert result == 100.0

    def test_pen_to_mxn(self) -> None:
        result = convert_currency(100.0, "PEN", "MXN")
        assert result is not None
        # 100 PEN * 0.27 (->USD) / 0.058 (USD->MXN) ≈ 465.52
        assert result == 465.52

    def test_unknown_source_returns_none(self) -> None:
        assert convert_currency(100.0, "XYZ", "USD") is None

    def test_unknown_target_returns_none(self) -> None:
        assert convert_currency(100.0, "USD", "XYZ") is None

    def test_zero_amount(self) -> None:
        assert convert_currency(0.0, "PEN", "USD") == 0.0


class TestBuildMoneyDisplay:
    """Single-source display builder."""

    def test_same_currency_no_conversion(self) -> None:
        result = build_money_display(500.0, "PEN", "PEN")
        assert isinstance(result, MoneyDisplay)
        assert result.source_amount == 500.0
        assert result.source_currency == "PEN"
        assert result.tenant_amount is None  # same, no need
        assert result.usd_amount is None  # no need

    def test_different_source_and_tenant(self) -> None:
        # Source USD, tenant PEN
        result = build_money_display(100.0, "USD", "PEN")
        assert result.source_amount == 100.0
        assert result.source_currency == "USD"
        assert result.tenant_amount is not None  # converted to PEN
        assert result.tenant_currency == "PEN"
        # USD is source, so usd_amount not duplicated
        assert result.usd_amount is None

    def test_tenant_is_usd_source_is_pen(self) -> None:
        result = build_money_display(500.0, "PEN", "USD")
        assert result.source_amount == 500.0
        assert result.tenant_amount is not None  # converted to USD
        assert result.tenant_currency == "USD"
        # tenant IS usd, so usd_amount not needed separately
        assert result.usd_amount is None

    def test_neither_is_usd(self) -> None:
        # Source MXN, tenant PEN — need USD too
        result = build_money_display(1000.0, "MXN", "PEN")
        assert result.source_currency == "MXN"
        assert result.tenant_currency == "PEN"
        assert result.tenant_amount is not None
        assert result.usd_amount is not None  # neither is USD


class TestBuildAggregatedDisplay:
    """Multi-source aggregated display builder."""

    def test_single_currency(self) -> None:
        result = build_aggregated_display([(500.0, "PEN"), (300.0, "PEN")], "PEN")
        assert isinstance(result, AggregatedMoneyDisplay)
        assert result.tenant_amount == 800.0
        assert result.tenant_currency == "PEN"
        assert result.usd_amount is not None  # always show USD for aggregated

    def test_mixed_currencies(self) -> None:
        result = build_aggregated_display(
            [(500.0, "PEN"), (100.0, "USD")],
            "PEN",
        )
        assert result.tenant_currency == "PEN"
        assert result.tenant_amount > 500.0  # 500 PEN + 100 USD converted to PEN
        assert result.usd_amount is not None

    def test_tenant_is_usd(self) -> None:
        result = build_aggregated_display([(500.0, "PEN"), (100.0, "USD")], "USD")
        assert result.tenant_currency == "USD"
        assert result.usd_amount is None  # tenant IS USD, no duplicate
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && .venv/bin/pytest tests/shared/test_currency.py::TestConvertCurrency -v`
Expected: FAIL — `ImportError: cannot import name 'convert_currency'`

- [ ] **Step 3: Write the implementation**

Add to `backend/src/shared/domain/currency.py` (after existing functions):

```python
from dataclasses import dataclass


def convert_currency(
    amount: float, from_currency: str, to_currency: str
) -> float | None:
    """Convert between any two supported currencies via USD as pivot.

    Returns None if either currency has no known exchange rate.
    """
    if from_currency == to_currency:
        return round(amount, 2)
    rate_from = EXCHANGE_RATES_TO_USD.get(from_currency)
    rate_to = EXCHANGE_RATES_TO_USD.get(to_currency)
    if rate_from is None or rate_to is None or rate_to == 0:
        return None
    usd_amount = amount * rate_from
    return round(usd_amount / rate_to, 2)


@dataclass(frozen=True)
class MoneyDisplay:
    """Pre-computed amounts for frontend single-source dual display."""

    source_amount: float
    source_currency: str
    tenant_amount: float | None
    tenant_currency: str
    usd_amount: float | None


def build_money_display(
    amount: float, source_currency: str, tenant_currency: str
) -> MoneyDisplay:
    """Build display amounts for a single-source monetary value.

    Rules:
    - source == tenant: show once (no conversion needed)
    - source != tenant: show source + tenant equivalent
    - If neither is USD: also include USD equivalent
    """
    if source_currency == tenant_currency:
        return MoneyDisplay(
            source_amount=amount,
            source_currency=source_currency,
            tenant_amount=None,
            tenant_currency=tenant_currency,
            usd_amount=None,
        )

    tenant_amount = convert_currency(amount, source_currency, tenant_currency)
    need_usd = source_currency != "USD" and tenant_currency != "USD"
    usd_amount = convert_to_usd(amount, source_currency) if need_usd else None

    return MoneyDisplay(
        source_amount=amount,
        source_currency=source_currency,
        tenant_amount=tenant_amount,
        tenant_currency=tenant_currency,
        usd_amount=usd_amount,
    )


@dataclass(frozen=True)
class AggregatedMoneyDisplay:
    """Pre-computed amounts for frontend multi-source aggregated display."""

    tenant_amount: float
    tenant_currency: str
    usd_amount: float | None


def build_aggregated_display(
    amounts: list[tuple[float, str]],
    tenant_currency: str,
) -> AggregatedMoneyDisplay:
    """Sum amounts from multiple currencies into tenant currency + USD.

    Rules:
    - All amounts converted to tenant currency and summed
    - USD shown unless tenant currency IS USD
    """
    tenant_total = 0.0
    usd_total = 0.0

    for amount, currency in amounts:
        converted = convert_currency(amount, currency, tenant_currency)
        tenant_total += converted if converted is not None else 0.0
        usd = convert_to_usd(amount, currency)
        usd_total += usd if usd is not None else 0.0

    tenant_total = round(tenant_total, 2)
    usd_total = round(usd_total, 2)

    return AggregatedMoneyDisplay(
        tenant_amount=tenant_total,
        tenant_currency=tenant_currency,
        usd_amount=usd_total if tenant_currency != "USD" else None,
    )
```

- [ ] **Step 4: Run all currency tests**

Run: `cd backend && .venv/bin/pytest tests/shared/test_currency.py -v`
Expected: all passed (old + new)

- [ ] **Step 5: Commit**

```bash
git add backend/src/shared/domain/currency.py backend/tests/shared/test_currency.py
git commit -m "feat(shared): add bidirectional currency conversion + display builders"
```

---

### Task 4: Backend Dependency — get_tenant_locale

**Files:**
- Modify: `backend/src/modules/iam/api/dependencies.py`
- Create: `backend/tests/modules/iam/test_tenant_locale_dependency.py`

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/modules/iam/test_tenant_locale_dependency.py`:

```python
"""Tests for get_tenant_locale FastAPI dependency."""

import uuid

import pytest
from sqlalchemy.orm import Session

from src.modules.iam.infrastructure.models.tenant_model import TenantModel
from src.shared.domain.locale import TenantLocale


class TestGetTenantLocale:
    """Unit tests for the tenant locale resolution logic."""

    def test_returns_tenant_values(self, db: Session) -> None:
        """When tenant has currency=PEN and timezone=America/Lima, return those."""
        tenant_id = uuid.uuid4()
        tenant = TenantModel(
            id=tenant_id,
            name="Test",
            slug=f"test-{tenant_id.hex[:8]}",
            default_currency="PEN",
            timezone="America/Lima",
        )
        db.add(tenant)
        db.commit()

        from src.modules.iam.api.dependencies import _resolve_tenant_locale

        result = _resolve_tenant_locale(db, tenant_id)
        assert isinstance(result, TenantLocale)
        assert result.currency == "PEN"
        assert result.timezone == "America/Lima"

    def test_fallback_when_fields_null(self, db: Session) -> None:
        """When tenant has null currency/timezone, fall back to defaults."""
        tenant_id = uuid.uuid4()
        tenant = TenantModel(
            id=tenant_id,
            name="Test Null",
            slug=f"test-null-{tenant_id.hex[:8]}",
        )
        # Don't set default_currency or timezone — rely on server_default
        db.add(tenant)
        db.commit()

        from src.modules.iam.api.dependencies import _resolve_tenant_locale

        result = _resolve_tenant_locale(db, tenant_id)
        assert result.currency == "USD"
        assert result.timezone == "UTC"

    def test_missing_tenant_returns_default(self, db: Session) -> None:
        """When tenant doesn't exist, return default locale."""
        from src.modules.iam.api.dependencies import _resolve_tenant_locale

        result = _resolve_tenant_locale(db, uuid.uuid4())
        assert result == TenantLocale.default()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && .venv/bin/pytest tests/modules/iam/test_tenant_locale_dependency.py -v`
Expected: FAIL — `ImportError: cannot import name '_resolve_tenant_locale'`

- [ ] **Step 3: Write the implementation**

Add to `backend/src/modules/iam/api/dependencies.py` at the end of the file:

```python
from src.shared.domain.locale import TenantLocale


def _resolve_tenant_locale(db: Session, tenant_id: UUID) -> TenantLocale:
    """Load TenantLocale from DB. Extracted for testability."""
    tenant = (
        db.execute(select(TenantModel).where(TenantModel.id == tenant_id))
        .scalars()
        .first()
    )
    if tenant:
        return TenantLocale(
            currency=tenant.default_currency or "USD",
            timezone=tenant.timezone or "UTC",
        )
    return TenantLocale.default()


def get_tenant_locale(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TenantLocale:
    """FastAPI dependency: resolves TenantLocale for the current request.

    The tenant row is typically already in the SA session identity map
    from get_current_user, so this is a cache hit, not a new query.
    """
    return _resolve_tenant_locale(db, user.tenant_id)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && .venv/bin/pytest tests/modules/iam/test_tenant_locale_dependency.py -v`
Expected: all passed

- [ ] **Step 5: Commit**

```bash
git add backend/src/modules/iam/api/dependencies.py backend/tests/modules/iam/test_tenant_locale_dependency.py
git commit -m "feat(iam): add get_tenant_locale FastAPI dependency"
```

---

### Task 5: Architecture Fitness Test — Master Data Enforcement

**Files:**
- Create: `backend/tests/architecture/test_master_data.py`

- [ ] **Step 1: Write the arch test**

Create `backend/tests/architecture/test_master_data.py`:

```python
"""Architecture fitness tests for master data (currency + timezone) enforcement.

These tests use the ratchet pattern: known legacy violations are in an allowlist
that can only shrink over time. New violations fail the build.
"""

import ast
import re
from pathlib import Path

import pytest

BACKEND_SRC = Path("src")
FRONTEND_SRC = Path(__file__).resolve().parents[3] / "frontend" / "src"

# ── Currency: no hardcoded "USD" as Pydantic field defaults ──────────

# Files allowed to have `= "USD"` as field defaults (source of truth + settings)
ALLOWED_USD_DEFAULT_FILES: set[str] = {
    "src/shared/domain/currency.py",
    "src/modules/iam/domain/tenant.py",       # GeneralSettings default
    "src/modules/iam/api/settings.py",         # Reads from tenant, fallback is OK
    "src/shared/domain/locale.py",             # TenantLocale.default()
}

# Legacy violations — shrink this list as you fix them
KNOWN_USD_DEFAULT_VIOLATIONS: set[str] = {
    "src/modules/offer/domain/offer.py",
    "src/shared/domain/ports.py",
    "src/modules/crm/domain/sale.py",
    "src/modules/analytics/application/dto/sales_dto.py",
    "src/modules/analytics/application/dto/adoption_dto.py",
}


def _find_usd_field_defaults(root: Path) -> set[str]:
    """Find .py files with `= "USD"` patterns in class field definitions."""
    violations: set[str] = set()
    pattern = re.compile(r'''[:=]\s*["']USD["']''')
    for py_file in root.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
        rel = str(py_file.relative_to(py_file.parents[len(py_file.parts) - len(root.parts) - 1]))
        if not rel.startswith("src/"):
            continue
        text = py_file.read_text()
        if pattern.search(text) and rel not in ALLOWED_USD_DEFAULT_FILES:
            violations.add(rel)
    return violations


class TestNoCurrencyHardcodes:
    def test_no_new_usd_defaults(self) -> None:
        violations = _find_usd_field_defaults(BACKEND_SRC)
        new_violations = violations - KNOWN_USD_DEFAULT_VIOLATIONS
        assert not new_violations, (
            f"New hardcoded 'USD' defaults found. Use TenantLocale or remove the default:\n"
            + "\n".join(sorted(new_violations))
        )


# ── Timezone: no datetime.utcnow() usage ────────────────────────────

KNOWN_UTCNOW_VIOLATIONS: set[str] = {
    "src/shared/links/service.py",
    "src/modules/copilot/application/tools/analytics_tools.py",
    "src/modules/assets/infrastructure/repositories/asset_repository.py",
    "src/modules/assets/infrastructure/repositories/gallery_repository.py",
    "src/modules/connections/infrastructure/channels/google_calendar.py",
    "src/modules/brand/infrastructure/repositories/avatar_repository.py",
    "src/modules/sales_agent/infrastructure/repositories/state_repository.py",
    "src/modules/sales_agent/domain/events.py",
}


def _find_utcnow_usage(root: Path) -> set[str]:
    """Find .py files using deprecated datetime.utcnow()."""
    violations: set[str] = set()
    pattern = re.compile(r"\.utcnow\(\)|datetime\.utcnow\b")
    for py_file in root.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
        rel = str(py_file.relative_to(py_file.parents[len(py_file.parts) - len(root.parts) - 1]))
        if not rel.startswith("src/"):
            continue
        text = py_file.read_text()
        if pattern.search(text):
            violations.add(rel)
    return violations


class TestNoUtcnow:
    def test_no_new_utcnow_usage(self) -> None:
        violations = _find_utcnow_usage(BACKEND_SRC)
        new_violations = violations - KNOWN_UTCNOW_VIOLATIONS
        assert not new_violations, (
            f"New datetime.utcnow() usage found. Use utc_now() from shared.domain.datetime_utils:\n"
            + "\n".join(sorted(new_violations))
        )


# ── Timezone: no DateTime() without timezone=True in models ─────────

KNOWN_NAIVE_DATETIME_MODELS: set[str] = {
    "src/modules/sales_agent/infrastructure/models/agent_state_checkpoint_model.py",
}


def _find_naive_datetime_columns(root: Path) -> set[str]:
    """Find model files with DateTime() columns missing timezone=True."""
    violations: set[str] = set()
    # Match: Column(DateTime, or Column(DateTime() but NOT Column(DateTime(timezone=True)
    pattern = re.compile(
        r"Column\(\s*DateTime\s*[,)]"  # DateTime without parens or with empty parens
        r"|Column\(\s*DateTime\(\s*\)"  # DateTime()
    )
    tz_pattern = re.compile(r"Column\(\s*DateTime\(\s*timezone\s*=\s*True\s*\)")
    for py_file in root.rglob("*model*.py"):
        if "__pycache__" in str(py_file):
            continue
        rel = str(py_file.relative_to(py_file.parents[len(py_file.parts) - len(root.parts) - 1]))
        if not rel.startswith("src/"):
            continue
        text = py_file.read_text()
        for line in text.splitlines():
            if pattern.search(line) and not tz_pattern.search(line):
                violations.add(rel)
                break
    return violations


class TestNoNaiveDatetimeColumns:
    def test_no_new_naive_datetime_columns(self) -> None:
        violations = _find_naive_datetime_columns(BACKEND_SRC)
        new_violations = violations - KNOWN_NAIVE_DATETIME_MODELS
        assert not new_violations, (
            f"New DateTime columns without timezone=True found:\n"
            + "\n".join(sorted(new_violations))
        )
```

- [ ] **Step 2: Run the arch test**

Run: `cd backend && .venv/bin/pytest tests/architecture/test_master_data.py -v`
Expected: all 3 pass (known violations in allowlists, no NEW violations)

- [ ] **Step 3: Commit**

```bash
git add backend/tests/architecture/test_master_data.py
git commit -m "test(arch): add master data fitness tests (currency, utcnow, datetime columns)"
```

---

## Phase 2: Backend Migration — Fix Violations (Tasks 6–9)

### Task 6: Replace all datetime.utcnow() with utc_now()

**Files to modify (8 files):**
- `backend/src/shared/links/service.py` (lines 31, 52, 92, 100)
- `backend/src/modules/copilot/application/tools/analytics_tools.py` (line 38)
- `backend/src/modules/assets/infrastructure/repositories/asset_repository.py` (line 100)
- `backend/src/modules/assets/infrastructure/repositories/gallery_repository.py` (line 88)
- `backend/src/modules/connections/infrastructure/channels/google_calendar.py` (line 49)
- `backend/src/modules/brand/infrastructure/repositories/avatar_repository.py` (line 84)
- `backend/src/modules/sales_agent/infrastructure/repositories/state_repository.py` (lines 48, 70)
- `backend/src/modules/sales_agent/domain/events.py` (line 11)

- [ ] **Step 1: Fix shared/links/service.py**

Replace `import datetime` section and all 4 usages:

```python
# Add import at top
from src.shared.domain.datetime_utils import utc_now

# Line 31: replace datetime.datetime.utcnow() with utc_now()
timestamp_hex = f"{int(utc_now().timestamp()):x}"

# Line 52: replace
expires_at = utc_now() + datetime.timedelta(days=expires_days)

# Line 92-93: replace
if link.expires_at and link.expires_at.replace(tzinfo=None) < utc_now().replace(tzinfo=None):

# Line 100: replace
link.last_visited_at = utc_now()
```

- [ ] **Step 2: Fix remaining 7 files**

For each file, add `from src.shared.domain.datetime_utils import utc_now` and replace `datetime.utcnow()` / `datetime.datetime.utcnow()` with `utc_now()`.

**sales_agent/domain/events.py** (special case — Pydantic Field default):
```python
from src.shared.domain.datetime_utils import utc_now

class DomainEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    occurred_on: datetime = Field(default_factory=utc_now)
    version: int = 1
```

**sales_agent/infrastructure/repositories/state_repository.py**:
```python
from src.shared.domain.datetime_utils import utc_now

# Line 48: existing.updated_at = utc_now()
# Line 70: .values(is_active=False, deleted_at=utc_now())
```

Same pattern for: `asset_repository.py`, `gallery_repository.py`, `avatar_repository.py`, `google_calendar.py`, `analytics_tools.py`.

- [ ] **Step 3: Remove utcnow from arch test allowlist**

In `backend/tests/architecture/test_master_data.py`, set:
```python
KNOWN_UTCNOW_VIOLATIONS: set[str] = set()  # All fixed!
```

- [ ] **Step 4: Run arch test + full backend tests**

Run: `cd backend && .venv/bin/pytest tests/architecture/test_master_data.py::TestNoUtcnow -v && .venv/bin/pytest -x -q --tb=short`
Expected: all pass

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "refactor: replace all datetime.utcnow() with utc_now() from shared utils"
```

---

### Task 7: Fix AgentStateCheckpointModel DateTime columns + Migration

**Files:**
- Modify: `backend/src/modules/sales_agent/infrastructure/models/agent_state_checkpoint_model.py`
- Create: `backend/alembic/versions/xxx_checkpoint_datetime_timezone.py`

- [ ] **Step 1: Fix the model**

In `agent_state_checkpoint_model.py`, change all 6 DateTime columns:

```python
from sqlalchemy.sql import func

# Line 49
paused_at = Column(DateTime(timezone=True), nullable=True)

# Line 55
frozen_at = Column(DateTime(timezone=True), nullable=True)

# Line 59
last_human_message_at = Column(DateTime(timezone=True), nullable=True)

# Line 64
deleted_at = Column(DateTime(timezone=True), nullable=True)

# Line 65
created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

# Lines 66-67
updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
```

Also remove the `from datetime import datetime` import (no longer needed after Task 6 removed utcnow).

- [ ] **Step 2: Create idempotent Alembic migration**

Create migration file (use `alembic revision` to get the correct revision ID, then write raw SQL):

```python
"""Add timezone to agent_state_checkpoint datetime columns.

Revision ID: <auto>
"""

from alembic import op


def upgrade() -> None:
    # PostgreSQL: ALTER COLUMN TYPE TIMESTAMPTZ is safe for existing data.
    # Existing TIMESTAMP values are treated as UTC by PostgreSQL when converting.
    for col in [
        "paused_at",
        "frozen_at",
        "last_human_message_at",
        "deleted_at",
        "created_at",
        "updated_at",
    ]:
        op.execute(
            f"ALTER TABLE agent_state_checkpoints "
            f"ALTER COLUMN {col} TYPE TIMESTAMPTZ USING {col} AT TIME ZONE 'UTC'"
        )

    # Set server defaults for created_at and updated_at
    op.execute(
        "ALTER TABLE agent_state_checkpoints "
        "ALTER COLUMN created_at SET DEFAULT now()"
    )
    op.execute(
        "ALTER TABLE agent_state_checkpoints "
        "ALTER COLUMN updated_at SET DEFAULT now()"
    )


def downgrade() -> None:
    for col in [
        "paused_at",
        "frozen_at",
        "last_human_message_at",
        "deleted_at",
        "created_at",
        "updated_at",
    ]:
        op.execute(
            f"ALTER TABLE agent_state_checkpoints "
            f"ALTER COLUMN {col} TYPE TIMESTAMP USING {col} AT TIME ZONE 'UTC'"
        )
```

- [ ] **Step 3: Remove from arch test allowlist**

In `test_master_data.py`:
```python
KNOWN_NAIVE_DATETIME_MODELS: set[str] = set()  # All fixed!
```

- [ ] **Step 4: Run tests**

Run: `cd backend && .venv/bin/pytest tests/architecture/test_master_data.py::TestNoNaiveDatetimeColumns -v`
Expected: PASS

- [ ] **Step 5: Apply migration (requires Docker)**

Run: `docker exec -t visionarias_brain_dev bash -c "cd /app && alembic upgrade head"`

- [ ] **Step 6: Commit**

```bash
git add backend/src/modules/sales_agent/infrastructure/models/agent_state_checkpoint_model.py backend/alembic/versions/*checkpoint_datetime* backend/tests/architecture/test_master_data.py
git commit -m "fix(sales_agent): add timezone=True to checkpoint DateTime columns + migration"
```

---

### Task 8: Remove hardcoded USD defaults from backend DTOs/domains

**Files to modify (5 files):**
- `backend/src/modules/offer/domain/offer.py` (line 106)
- `backend/src/modules/offer/api/dto/products.py` (line 40)
- `backend/src/shared/domain/ports.py` (line 57)
- `backend/src/modules/crm/domain/sale.py` (line 19)
- `backend/src/modules/analytics/application/dto/adoption_dto.py` (line 38)

- [ ] **Step 1: Fix each file**

**offer/domain/offer.py:106** — Keep required, remove default:
```python
currency: str  # Set from tenant.default_currency at creation time
```

**offer/api/dto/products.py:40** — Make nullable without hardcoded default:
```python
currency: str | None = None
```

**shared/domain/ports.py:57** — Remove default:
```python
currency: str  # Source of truth from offer
```

**crm/domain/sale.py:19** — Remove default:
```python
currency: str  # Source of truth from transaction
```

**analytics/dto/adoption_dto.py:38** — Remove default:
```python
refund_currency: str  # From tenant or shop currency
```

- [ ] **Step 2: Fix any test factories/fixtures that relied on the default**

Search test files for offer/sale creation and add explicit `currency="USD"` or `currency="PEN"` where previously the default was relied upon.

Run: `cd backend && .venv/bin/pytest -x -q --tb=short` to find any failures.

- [ ] **Step 3: Remove from arch test allowlist**

In `test_master_data.py`:
```python
KNOWN_USD_DEFAULT_VIOLATIONS: set[str] = set()  # All fixed!
```

- [ ] **Step 4: Run full backend tests**

Run: `cd backend && .venv/bin/pytest -x -q --tb=short`
Expected: all pass

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "refactor: remove hardcoded USD defaults from DTOs and domain models"
```

---

### Task 9: Fix hardcoded timezone in scheduling

**Files:**
- Modify: `backend/src/modules/scheduling/application/services/availability_service.py` (lines 94, 167)

- [ ] **Step 1: Fix availability_service.py**

Line 94 — migration logic fallback: read tenant timezone instead of hardcoding:
```python
# Before: data["timezone"] = "America/Bogota"
# After: 
tenant = self._get_tenant()
data["timezone"] = tenant.timezone if tenant and tenant.timezone else "UTC"
```

Line 167 — event type creation: same pattern:
```python
# Before: timezone="America/Bogota"
# After:
tenant = self._get_tenant()
tz = tenant.timezone if tenant and tenant.timezone else "UTC"
```

- [ ] **Step 2: Run scheduling tests**

Run: `cd backend && .venv/bin/pytest tests/modules/scheduling/ -v`
Expected: all pass

- [ ] **Step 3: Commit**

```bash
git add backend/src/modules/scheduling/application/services/availability_service.py
git commit -m "fix(scheduling): use tenant timezone instead of hardcoded America/Bogota"
```

---

## Phase 3: Frontend Infrastructure (Tasks 10–13)

### Task 10: Frontend Date Formatting Utility

**Files:**
- Create: `frontend/src/lib/format-date.ts`
- Create: `frontend/src/lib/__tests__/format-date.test.ts`

- [ ] **Step 1: Write the failing tests**

Create `frontend/src/lib/__tests__/format-date.test.ts`:

```typescript
import { describe, expect, it } from 'vitest';
import {
  formatTenantDate,
  formatTenantDateTime,
  formatTenantTime,
} from '../format-date';

describe('formatTenantDate', () => {
  it('formats in UTC', () => {
    const result = formatTenantDate('2026-04-09T12:00:00Z', 'UTC');
    expect(result).toContain('9');
    expect(result).toMatch(/abr/i); // Spanish month
  });

  it('formats in America/Lima', () => {
    // Midnight UTC = 7pm previous day in Lima (UTC-5)
    const result = formatTenantDate('2026-04-09T00:00:00Z', 'America/Lima');
    expect(result).toContain('8'); // Should be April 8th in Lima
  });

  it('accepts custom format', () => {
    const result = formatTenantDate('2026-04-09T12:00:00Z', 'UTC', 'yyyy-MM-dd');
    expect(result).toBe('2026-04-09');
  });
});

describe('formatTenantDateTime', () => {
  it('includes time component', () => {
    const result = formatTenantDateTime('2026-04-09T15:30:00Z', 'UTC');
    expect(result).toContain('15:30');
  });

  it('converts time to tenant timezone', () => {
    // 15:30 UTC = 10:30 Lima
    const result = formatTenantDateTime('2026-04-09T15:30:00Z', 'America/Lima');
    expect(result).toContain('10:30');
  });
});

describe('formatTenantTime', () => {
  it('shows only time', () => {
    const result = formatTenantTime('2026-04-09T15:30:00Z', 'UTC');
    expect(result).toBe('15:30');
  });

  it('converts to tenant timezone', () => {
    const result = formatTenantTime('2026-04-09T15:30:00Z', 'America/Lima');
    expect(result).toBe('10:30');
  });
});
```

- [ ] **Step 2: Run to verify failure**

Run: `cd frontend && npx vitest run src/lib/__tests__/format-date.test.ts`
Expected: FAIL — module not found

- [ ] **Step 3: Write the implementation**

Create `frontend/src/lib/format-date.ts`:

```typescript
/**
 * Centralized date formatting utilities.
 * All dates displayed in the UI pass through these functions,
 * which convert UTC to the tenant's timezone.
 *
 * Uses date-fns-tz (already installed) for timezone conversion.
 */

import { formatInTimeZone } from 'date-fns-tz';
import { es } from 'date-fns/locale';

/**
 * Format a date string in the tenant's timezone.
 * @param isoDate - ISO 8601 date string (UTC from backend)
 * @param timezone - IANA timezone (e.g., "America/Lima")
 * @param format - date-fns format string (default: "d MMM yyyy")
 */
export function formatTenantDate(
  isoDate: string,
  timezone: string,
  format?: string,
): string {
  return formatInTimeZone(
    new Date(isoDate),
    timezone,
    format ?? 'd MMM yyyy',
    { locale: es },
  );
}

/**
 * Format a date+time string in the tenant's timezone.
 */
export function formatTenantDateTime(
  isoDate: string,
  timezone: string,
): string {
  return formatInTimeZone(
    new Date(isoDate),
    timezone,
    'd MMM yyyy, HH:mm',
    { locale: es },
  );
}

/**
 * Format only the time portion in the tenant's timezone.
 */
export function formatTenantTime(
  isoDate: string,
  timezone: string,
): string {
  return formatInTimeZone(
    new Date(isoDate),
    timezone,
    'HH:mm',
    { locale: es },
  );
}
```

- [ ] **Step 4: Run tests**

Run: `cd frontend && npx vitest run src/lib/__tests__/format-date.test.ts`
Expected: all pass

- [ ] **Step 5: Commit**

```bash
git add frontend/src/lib/format-date.ts frontend/src/lib/__tests__/format-date.test.ts
git commit -m "feat(frontend): add tenant timezone date formatting utilities"
```

---

### Task 11: Extend formatMoney with Dual Display Functions

**Files:**
- Modify: `frontend/src/lib/format-money.ts`
- Modify: `frontend/src/lib/__tests__/format-money.test.ts`

- [ ] **Step 1: Write the failing tests**

Append to `frontend/src/lib/__tests__/format-money.test.ts`:

```typescript
import { formatMoneyDual, formatAggregatedMoney } from '../format-money';

describe('formatMoneyDual', () => {
  it('shows single when source equals tenant', () => {
    const result = formatMoneyDual(500, 'PEN', 'PEN');
    expect(result).toMatch(/S\/|PEN/);
    expect(result).toContain('500');
    expect(result).not.toContain('~');
  });

  it('shows dual when source differs from tenant', () => {
    const result = formatMoneyDual(100, 'USD', 'PEN', 370);
    expect(result).toContain('$');
    expect(result).toContain('100');
    expect(result).toContain('~');
    expect(result).toContain('370');
  });

  it('shows just source when tenantAmount not available', () => {
    const result = formatMoneyDual(100, 'USD', 'PEN');
    expect(result).toContain('100');
  });
});

describe('formatAggregatedMoney', () => {
  it('shows single when tenant is USD', () => {
    const result = formatAggregatedMoney(1350, 'USD');
    expect(result).toContain('$');
    expect(result).toContain('1,350');
    expect(result).not.toContain('~');
  });

  it('shows dual when tenant is not USD', () => {
    const result = formatAggregatedMoney(5000, 'PEN', 1350);
    expect(result).toMatch(/S\/|PEN/);
    expect(result).toContain('5,000');
    expect(result).toContain('~');
    expect(result).toContain('1,350');
    expect(result).toContain('USD');
  });

  it('shows single when usdAmount is null', () => {
    const result = formatAggregatedMoney(5000, 'PEN');
    expect(result).toMatch(/S\/|PEN/);
    expect(result).not.toContain('USD');
  });
});
```

- [ ] **Step 2: Run to verify failure**

Run: `cd frontend && npx vitest run src/lib/__tests__/format-money.test.ts`
Expected: FAIL — `formatMoneyDual` not found

- [ ] **Step 3: Write the implementation**

Append to `frontend/src/lib/format-money.ts`:

```typescript
/**
 * Single-source dual display.
 * Rules:
 * - source === tenant → show once
 * - source !== tenant → "source amount (~ tenant amount CURRENCY)"
 */
export function formatMoneyDual(
  amount: number,
  sourceCurrency: string,
  tenantCurrency: string,
  tenantAmount?: number | null,
): string {
  const main = formatMoney(amount, sourceCurrency, { fractionDigits: 0 });

  if (sourceCurrency === tenantCurrency) return main;

  if (tenantAmount != null) {
    const tenantFormatted = formatMoney(tenantAmount, tenantCurrency, {
      fractionDigits: 0,
    });
    return `${main} (~ ${tenantFormatted})`;
  }

  return main;
}

/**
 * Multi-source aggregated display.
 * Rules:
 * - tenant === USD → show once
 * - tenant !== USD → "tenant amount (~ usd amount USD)"
 */
export function formatAggregatedMoney(
  tenantAmount: number,
  tenantCurrency: string,
  usdAmount?: number | null,
): string {
  const main = formatMoney(tenantAmount, tenantCurrency, { fractionDigits: 0 });

  if (tenantCurrency === 'USD') return main;

  if (usdAmount != null) {
    const usdFormatted = formatMoney(usdAmount, 'USD', {
      fractionDigits: 0,
      locale: 'en-US',
    });
    return `${main} (~ ${usdFormatted} USD)`;
  }

  return main;
}
```

- [ ] **Step 4: Run tests**

Run: `cd frontend && npx vitest run src/lib/__tests__/format-money.test.ts`
Expected: all pass

- [ ] **Step 5: Commit**

```bash
git add frontend/src/lib/format-money.ts frontend/src/lib/__tests__/format-money.test.ts
git commit -m "feat(frontend): add formatMoneyDual and formatAggregatedMoney"
```

---

### Task 12: TenantLocale React Context + Provider

**Files:**
- Modify: `frontend/src/lib/api/settings.ts` (add timezone to GeneralSettings interface)
- Create: `frontend/src/features/tenant/context/tenant-locale-context.tsx`
- Create: `frontend/src/features/tenant/__tests__/tenant-locale-context.test.tsx`
- Modify: `frontend/src/app/providers.tsx`

- [ ] **Step 1: Update GeneralSettings interface**

In `frontend/src/lib/api/settings.ts`, line 6-8:

```typescript
export interface GeneralSettings {
  default_currency: string;
  timezone: string;
}
```

- [ ] **Step 2: Write the failing tests**

Create `frontend/src/features/tenant/__tests__/tenant-locale-context.test.tsx`:

```typescript
import { renderHook } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import React from 'react';
import { TenantLocaleProvider, useTenantLocale } from '../context/tenant-locale-context';

describe('useTenantLocale', () => {
  it('returns default values when no provider', () => {
    // Without provider, should return defaults
    const { result } = renderHook(() => useTenantLocale());
    expect(result.current.currency).toBe('USD');
    expect(result.current.timezone).toBe('UTC');
  });

  it('returns provided values from context', () => {
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <TenantLocaleProvider
        initialLocale={{ currency: 'PEN', timezone: 'America/Lima' }}
      >
        {children}
      </TenantLocaleProvider>
    );

    const { result } = renderHook(() => useTenantLocale(), { wrapper });
    expect(result.current.currency).toBe('PEN');
    expect(result.current.timezone).toBe('America/Lima');
  });
});
```

- [ ] **Step 3: Run to verify failure**

Run: `cd frontend && npx vitest run src/features/tenant/__tests__/tenant-locale-context.test.tsx`
Expected: FAIL — module not found

- [ ] **Step 4: Write the implementation**

Create directory and file `frontend/src/features/tenant/context/tenant-locale-context.tsx`:

```typescript
'use client';

import { createContext, useContext, useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import { useAuth } from '@clerk/nextjs';
import { settingsApi } from '@/lib/api/settings';

export interface TenantLocale {
  currency: string;
  timezone: string;
}

const DEFAULT_LOCALE: TenantLocale = {
  currency: 'USD',
  timezone: 'UTC',
};

const TenantLocaleContext = createContext<TenantLocale>(DEFAULT_LOCALE);

interface TenantLocaleProviderProps {
  children: ReactNode;
  /** For testing: skip the API fetch and use these values directly. */
  initialLocale?: TenantLocale;
}

export function TenantLocaleProvider({
  children,
  initialLocale,
}: TenantLocaleProviderProps) {
  const [locale, setLocale] = useState<TenantLocale>(
    initialLocale ?? DEFAULT_LOCALE,
  );
  const { getToken } = useAuth();

  useEffect(() => {
    // Skip fetch if initial values were provided (testing)
    if (initialLocale) return;

    let cancelled = false;

    async function load() {
      try {
        const token = await getToken();
        if (!token || cancelled) return;

        const settings = await settingsApi.getGeneralSettings(token);
        if (!cancelled) {
          setLocale({
            currency: settings.default_currency || 'USD',
            timezone: settings.timezone || 'UTC',
          });
        }
      } catch {
        // Keep defaults on error — non-blocking
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [getToken, initialLocale]);

  return (
    <TenantLocaleContext.Provider value={locale}>
      {children}
    </TenantLocaleContext.Provider>
  );
}

/**
 * Access the current tenant's locale preferences.
 * Returns { currency, timezone } — falls back to USD/UTC if settings not loaded.
 */
export function useTenantLocale(): TenantLocale {
  return useContext(TenantLocaleContext);
}
```

- [ ] **Step 5: Wire into providers.tsx**

In `frontend/src/app/providers.tsx`, add the import and wrap children:

```typescript
import { TenantLocaleProvider } from '@/features/tenant/context/tenant-locale-context';

// Inside the return, wrap after NavigationProvider:
<NavigationProvider>
  <NavigationOverlay />
  <TenantLocaleProvider>
    {children}
  </TenantLocaleProvider>
</NavigationProvider>
```

- [ ] **Step 6: Run tests**

Run: `cd frontend && npx vitest run src/features/tenant/__tests__/tenant-locale-context.test.tsx`
Expected: all pass

- [ ] **Step 7: Run all frontend tests + types**

Run: `cd frontend && npx tsc --noEmit && npx vitest run`
Expected: all pass

- [ ] **Step 8: Commit**

```bash
git add frontend/src/features/tenant/ frontend/src/app/providers.tsx frontend/src/lib/api/settings.ts
git commit -m "feat(frontend): add TenantLocaleProvider + useTenantLocale hook"
```

---

### Task 13: Fix Growth Studio format utility

**Files:**
- Modify: `frontend/src/features/growth-studio/components/metrics-dashboard/utils/format.ts`

- [ ] **Step 1: Update format.ts**

Replace the file content to use tenant-aware formatting:

```typescript
import { formatMoney } from '@/lib/format-money';
import { formatTenantDateTime } from '@/lib/format-date';

export { formatDualCurrency, formatMoneyDual, formatAggregatedMoney } from '@/lib/format-money';

export function formatLastUpdated(isoDate: string, timezone: string): string {
  return formatTenantDateTime(isoDate, timezone);
}

export function formatNum(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1000) return `${(n / 1000).toFixed(n >= 10000 ? 0 : 1)}k`;
  return n.toLocaleString('es-ES');
}

export function formatDuration(seconds: number): string {
  if (seconds < 60) return `${Math.round(seconds)}s`;
  const min = Math.floor(seconds / 60);
  const sec = Math.round(seconds % 60);
  return `${min}m ${sec}s`;
}

export function formatCurrency(n: number, currency: string): string {
  return formatMoney(n, currency);
}

export type MetricFormat = 'number' | 'currency' | 'percentage' | 'duration';

export function formatMetricValue(
  value: number,
  format?: MetricFormat,
  currency?: string,
): string {
  switch (format) {
    case 'currency':
      return formatCurrency(value, currency ?? 'USD');
    case 'percentage':
      return `${value.toFixed(1)}%`;
    case 'duration':
      return formatDuration(value);
    default:
      return formatNum(value);
  }
}
```

Note: `formatLastUpdated` now requires a `timezone` parameter. Callers will be updated in Task 14.

- [ ] **Step 2: Run types check**

Run: `cd frontend && npx tsc --noEmit 2>&1 | head -30`
Expected: May show errors in callers of `formatLastUpdated` — these will be fixed in Task 14.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/growth-studio/components/metrics-dashboard/utils/format.ts
git commit -m "refactor(growth-studio): make format utility tenant-locale-aware"
```

---

## Phase 4: Frontend Migration — Fix All Violations (Tasks 14–15)

### Task 14: Fix all frontend date formatting violations (~12 files)

**Pattern:** In each file, import `useTenantLocale` and replace `toLocaleDateString()` / `toLocaleTimeString()` with `formatTenantDate()` / `formatTenantTime()`.

**Files to modify:**
1. `frontend/src/features/settings/components/team-view.tsx`
2. `frontend/src/features/audit/components/context-panel.tsx`
3. `frontend/src/features/audit/components/node-details-panel.tsx`
4. `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/MetricSidebar.tsx`
5. `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/SidebarContent.tsx`
6. `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/MetaAdsDashboard.tsx`
7. `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/tabs/CampaignsTab.tsx`
8. `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/ChannelDetailSidebar.tsx`
9. `frontend/src/features/growth-studio/components/metrics-dashboard/channel-widgets/ChannelRowHeader.tsx`
10. `frontend/src/features/growth-studio/components/metrics-dashboard/detail-panels/NurtureOpportunityDetail.tsx`

- [ ] **Step 1: Fix each file with the same pattern**

For each file:

1. Add imports:
```typescript
import { useTenantLocale } from '@/features/tenant/context/tenant-locale-context';
import { formatTenantDate, formatTenantDateTime, formatTenantTime } from '@/lib/format-date';
```

2. Inside the component function, add:
```typescript
const { timezone } = useTenantLocale();
```

3. Replace patterns:
- `new Date(x).toLocaleDateString('es-ES', {...})` → `formatTenantDate(x, timezone)`
- `new Date(x).toLocaleDateString('es-MX')` → `formatTenantDate(x, timezone)`
- `new Date(x).toLocaleDateString('es', {...})` → `formatTenantDate(x, timezone)`
- `new Date(x).toLocaleDateString()` → `formatTenantDate(x, timezone)`
- `new Date(x).toLocaleTimeString('es-ES', {...})` → `formatTenantTime(x, timezone)`
- `formatLastUpdated(x)` → `formatLastUpdated(x, timezone)`

Note: If a component is a Server Component (no `'use client'`), add `'use client'` or extract the date display into a small client component.

- [ ] **Step 2: Run types + tests**

Run: `cd frontend && npx tsc --noEmit && npx vitest run`
Expected: all pass

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "refactor(frontend): replace browser timezone with tenant timezone in all date displays"
```

---

### Task 15: Fix all frontend currency fallbacks (5 files)

**Files to modify:**
1. `frontend/src/features/offer-studio/components/editor/sections/pricing/pricing-form.tsx`
2. `frontend/src/features/offer-studio/api/adapter.ts`
3. `frontend/src/features/offer-studio/components/dashboard/offer-card.tsx`
4. `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/tabs/CostosTab.tsx`

- [ ] **Step 1: Fix each file**

For each file:

1. Add import:
```typescript
import { useTenantLocale } from '@/features/tenant/context/tenant-locale-context';
```

2. Inside the component, add:
```typescript
const { currency: tenantCurrency } = useTenantLocale();
```

3. Replace patterns:
- `currency || 'USD'` → `currency || tenantCurrency`
- `currency: p.currency || data.currency || "USD"` → `currency: p.currency || data.currency || tenantCurrency`

Note: For `adapter.ts` which is not a component (it's a plain function), the `tenantCurrency` must be passed as a parameter from the calling component.

- [ ] **Step 2: Run types + tests**

Run: `cd frontend && npx tsc --noEmit && npx vitest run`
Expected: all pass

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "refactor(frontend): replace hardcoded USD fallbacks with tenant currency"
```

---

## Phase 5: Claude Code Rule + Final Verification (Tasks 16–17)

### Task 16: Create Claude Code enforcement rule

**Files:**
- Create: `.claude/rules/master-data.md`

- [ ] **Step 1: Write the rule**

Create `.claude/rules/master-data.md`:

```markdown
# Master Data: Currency & Timezone

**Every module MUST use the tenant's locale preferences. No hardcoded currencies or timezones.**

## Architecture

```
TenantModel (DB)
  └── default_currency: str   (ISO 4217)
  └── timezone: str            (IANA)

Backend: TenantLocale value object (shared/domain/locale.py)
  └── Injected via get_tenant_locale() FastAPI dependency
  └── Workers load directly from TenantModel

Frontend: useTenantLocale() React hook (features/tenant/context/)
  └── Returns { currency, timezone }
  └── Loaded from GET /api/v1/iam/settings/general
```

## Currency Rules

1. **Store source truth:** ETL data keeps its original currency (official_metrics.currency).
   Never convert on write.
2. **No hardcoded "USD" defaults** in DTOs or domain models.
   Only allowed in: `shared/domain/currency.py`, `iam/domain/tenant.py`, `shared/domain/locale.py`.
3. **Display rules:**
   - Single-source metric: source currency + tenant currency equivalent (if different)
   - Aggregated multi-source: tenant currency + USD equivalent
   - Use `build_money_display()` or `build_aggregated_display()` (backend)
   - Use `formatMoneyDual()` or `formatAggregatedMoney()` (frontend)
4. **Frontend fallback chain:** `data.currency ?? useTenantLocale().currency`
   Never `currency || 'USD'`.
5. **Bidirectional conversion:** Use `convert_currency()` from `shared/domain/currency.py`.
   Old `convert_to_usd()` still available but prefer `convert_currency()` for any new code.

## Timezone Rules

1. **Backend stores UTC always.** Use `utc_now()` from `shared/domain/datetime_utils.py`.
   Never `datetime.utcnow()` (deprecated).
2. **All DateTime columns** must use `DateTime(timezone=True)`.
3. **Frontend converts for display** using `formatTenantDate()` / `formatTenantDateTime()` /
   `formatTenantTime()` from `lib/format-date.ts`. Never `toLocaleDateString()`.
4. **Timezone source:** `useTenantLocale().timezone` (frontend), `TenantLocale.timezone` (backend).

## When Adding New Monetary Fields

1. DTO must include a `currency: str` field alongside the amount
2. Service must resolve currency from data source or `TenantLocale`
3. Frontend must use `formatMoneyDual()` or `formatAggregatedMoney()`

## When Adding New Date Displays

1. Backend returns ISO 8601 UTC strings
2. Frontend uses `formatTenantDate(isoString, timezone)` with `useTenantLocale().timezone`

## Prohibited

- `datetime.utcnow()` anywhere
- `DateTime()` without `timezone=True` in models
- `= "USD"` as Pydantic field default (outside allowed files)
- `toLocaleDateString()` or `toLocaleTimeString()` for data display
- `currency || 'USD'` in frontend components
- `"America/Bogota"` or any hardcoded timezone in services
```

- [ ] **Step 2: Commit**

```bash
git add .claude/rules/master-data.md
git commit -m "docs: add master-data enforcement rule (currency + timezone)"
```

---

### Task 17: Full CI Verification

- [ ] **Step 1: Run backend lint + tests**

Run: `cd backend && .venv/bin/ruff check src/ tests/ --no-cache && .venv/bin/pytest -x -q --tb=short`
Expected: all pass

- [ ] **Step 2: Run frontend types + lint + tests**

Run: `cd frontend && npx tsc --noEmit && npx vitest run`
Expected: all pass

- [ ] **Step 3: Run architecture tests specifically**

Run: `cd backend && .venv/bin/pytest tests/architecture/ -v`
Expected: all pass, including new `test_master_data.py`

- [ ] **Step 4: Final commit if any fixes needed**

```bash
git add -A
git commit -m "fix: address lint/test issues from master data migration"
```

---

## Summary

| Phase | Tasks | What it does |
|-------|-------|-------------|
| 1 | 1–5 | Backend shared infrastructure (value objects, utilities, DI, arch tests) |
| 2 | 6–9 | Backend migration (fix utcnow, DateTime columns, USD defaults, hardcoded timezones) |
| 3 | 10–13 | Frontend infrastructure (date utils, money display, context provider, format util) |
| 4 | 14–15 | Frontend migration (fix all browser timezone + USD fallback violations) |
| 5 | 16–17 | Enforcement rule + full CI verification |

**Total: 17 tasks, ~39 violations fixed, 8 new files, 6 extended files, 27 migrated files.**
