"""Architecture fitness tests for master data (currency + timezone) enforcement.

These tests use the ratchet pattern: known legacy violations are in an allowlist
that can only shrink over time. New violations fail the build.
"""

import re
from pathlib import Path

BACKEND_SRC = Path(__file__).resolve().parents[2] / "src"

# ── Currency: no hardcoded "USD" as Pydantic field defaults ──────────

# Files that legitimately define or document USD (currency domain itself)
ALLOWED_USD_DEFAULT_FILES: set[str] = {
    "src/shared/domain/currency.py",
    "src/shared/domain/currency_catalog.py",
    "src/modules/iam/domain/tenant.py",
    "src/modules/iam/api/settings.py",
    "src/shared/domain/locale.py",
    # Per-tenant billing-cycle config (Phase 1 copilot observability rebuild).
    # ``billing_currency`` defaults to USD when no override exists — same role
    # as ``iam/domain/tenant.py``'s ``default_currency``.
    "src/modules/copilot/observability/persistence/models/tenant_billing_config_model.py",
    # Phase 1 observability seams that thread the tenant currency through
    # the recorder pipeline. The literal "USD" is the *fallback default*
    # at module boundaries when the caller (chat.py, tests) doesn't yet
    # know the tenant's locale; the canonical value lives on
    # ``tenant_billing_config.billing_currency`` and overrides the default
    # whenever the orchestrator wires the context (Phase 2). Same role as
    # the tenant_billing_config_model entry above.
    "src/modules/copilot/observability/cost/fx_resolver.py",
    "src/modules/copilot/observability/recording/callback_handler.py",
    "src/modules/copilot/observability/recording/turn_envelope.py",
    # Phase 2 atomic switch: chat.py reads tenant currency from
    # ``tenant_billing_config`` and falls back to "USD" when no row
    # exists. Same role as the model + observability seams above —
    # canonical value lives on tenant_billing_config.billing_currency.
    "src/modules/copilot/application/orchestrator/chat.py",
}

KNOWN_USD_DEFAULT_VIOLATIONS: set[str] = set()


def _find_usd_field_defaults(root: Path) -> set[str]:
    """Find .py files with '= "USD"' or ': str = "USD"' patterns."""
    violations: set[str] = set()
    pattern = re.compile(r"""[:=]\s*["']USD["']""")
    for py_file in root.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
        rel = str(py_file.relative_to(root.parent))
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
            "New hardcoded 'USD' defaults found. Use TenantLocale or remove the default:\n"
            + "\n".join(sorted(new_violations))
        )


# ── Timezone: no datetime.utcnow() usage ────────────────────────────

# Files allowed to mention utcnow (e.g. the module that documents why not to use it)
ALLOWED_UTCNOW_FILES: set[str] = {
    "src/shared/domain/datetime_utils.py",  # defines the canonical utc_now() replacement
}

KNOWN_UTCNOW_VIOLATIONS: set[str] = set()


def _find_utcnow_usage(root: Path) -> set[str]:
    """Find .py files using deprecated datetime.utcnow()."""
    violations: set[str] = set()
    pattern = re.compile(r"\.utcnow\(\)|datetime\.utcnow\b")
    for py_file in root.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
        rel = str(py_file.relative_to(root.parent))
        if not rel.startswith("src/"):
            continue
        if rel in ALLOWED_UTCNOW_FILES:
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
            "New datetime.utcnow() usage found. Use utc_now() from shared.domain.datetime_utils:\n"
            + "\n".join(sorted(new_violations))
        )


# ── Timezone: no DateTime() without timezone=True in models ─────────

KNOWN_NAIVE_DATETIME_MODELS: set[str] = set()


def _find_naive_datetime_columns(root: Path) -> set[str]:
    """Find model files with DateTime() columns missing timezone=True."""
    violations: set[str] = set()
    # Matches Column(DateTime without timezone=True
    naive_pattern = re.compile(r"Column\(\s*DateTime\s*[,)]|Column\(\s*DateTime\(\s*\)")
    tz_pattern = re.compile(r"DateTime\(\s*timezone\s*=\s*True\s*\)")
    for py_file in root.rglob("*model*.py"):
        if "__pycache__" in str(py_file):
            continue
        rel = str(py_file.relative_to(root.parent))
        if not rel.startswith("src/"):
            continue
        text = py_file.read_text()
        for line in text.splitlines():
            if "Column(" in line and "DateTime" in line and naive_pattern.search(line) and not tz_pattern.search(line):
                violations.add(rel)
                break
    return violations


class TestNoNaiveDatetimeColumns:
    def test_no_new_naive_datetime_columns(self) -> None:
        violations = _find_naive_datetime_columns(BACKEND_SRC)
        new_violations = violations - KNOWN_NAIVE_DATETIME_MODELS
        assert not new_violations, "New DateTime columns without timezone=True found:\n" + "\n".join(
            sorted(new_violations)
        )
