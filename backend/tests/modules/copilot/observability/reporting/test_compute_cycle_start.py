"""Tests for ``compute_cycle_start``.

Two layers:

1. Python equivalent (``compute_cycle_start_py``) lives in
   :mod:`src.shared.agent_observability.reporting.cycle_window` and is
   the single source of truth for cycle math used by the reporting layer
   (``BillingCycleService``). Unit tests here exercise it.
2. The Postgres SQL function ``compute_cycle_start(p_tenant UUID, p_date
   DATE)`` is created by migration ``076_copilot_billing_cycle_function``
   for use in raw SQL contexts (e.g. group-by-cycle queries). We verify
   the migration text is shaped correctly without hitting a live DB
   (consistent with ``test_migration_schema.py``).

The cycle convention: anchor day = first day of the cycle.
- ``anchor=25``, ``date=2026-04-26`` → cycle starts ``2026-04-25``.
- ``anchor=25``, ``date=2026-04-24`` → cycle starts ``2026-03-25``.
- ``anchor=1``, ``date=2026-04-15`` → cycle starts ``2026-04-01``.
- ``anchor=15``, ``date=2026-04-14`` → cycle starts ``2026-03-15``.
- No tenant config → defaults to ``anchor=25``.
"""

from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

import pytest

MIGRATION_FILE = Path(__file__).resolve().parents[5] / "alembic" / "versions" / "076_copilot_billing_cycle_function.py"


def _migration_source() -> str:
    return MIGRATION_FILE.read_text(encoding="utf-8")


# ── Python equivalent ───────────────────────────────────────────────────


class TestComputeCycleStartPy:
    """Unit tests for ``compute_cycle_start_py(anchor_day, target_date)``."""

    @pytest.fixture
    def fn(self):
        from src.shared.agent_observability.reporting.cycle_window import (
            compute_cycle_start_py,
        )

        return compute_cycle_start_py

    def test_anchor_25_date_in_current_cycle_after_anchor(self, fn) -> None:
        # 2026-04-26 with anchor 25 → cycle started 2026-04-25.
        assert fn(25, dt.date(2026, 4, 26)) == dt.date(2026, 4, 25)

    def test_anchor_25_date_on_anchor_day(self, fn) -> None:
        # 2026-04-25 IS the anchor day → cycle starts that same day.
        assert fn(25, dt.date(2026, 4, 25)) == dt.date(2026, 4, 25)

    def test_anchor_25_date_before_anchor(self, fn) -> None:
        # 2026-04-24 → still in the previous cycle (2026-03-25 .. 2026-04-25).
        assert fn(25, dt.date(2026, 4, 24)) == dt.date(2026, 3, 25)

    def test_anchor_1_falls_to_first_of_month(self, fn) -> None:
        assert fn(1, dt.date(2026, 4, 15)) == dt.date(2026, 4, 1)

    def test_anchor_15_before(self, fn) -> None:
        assert fn(15, dt.date(2026, 4, 14)) == dt.date(2026, 3, 15)

    def test_anchor_25_january_wraps_to_december_previous_year(self, fn) -> None:
        # 2026-01-10 with anchor 25 → cycle started 2025-12-25.
        assert fn(25, dt.date(2026, 1, 10)) == dt.date(2025, 12, 25)

    def test_anchor_default_is_25(self, fn) -> None:
        # Passing None as anchor_day defaults to 25.
        assert fn(None, dt.date(2026, 4, 26)) == dt.date(2026, 4, 25)

    @pytest.mark.parametrize("anchor", [0, 32, -1, 100])
    def test_invalid_anchor_raises(self, fn, anchor: int) -> None:
        with pytest.raises(ValueError):
            fn(anchor, dt.date(2026, 4, 1))


# ── Migration source parsing ────────────────────────────────────────────


class TestMigrationFile:
    def test_file_present(self) -> None:
        assert MIGRATION_FILE.exists(), (
            f"Expected migration at {MIGRATION_FILE}; create it before running this test (TDD red)."
        )

    def test_revision_id_and_down_revision(self) -> None:
        src = _migration_source()
        assert 'revision: str = "076_copilot_billing_cycle_function"' in src
        assert 'down_revision: str | None = "075_copilot_observability_rebuild"' in src


class TestComputeCycleStartFunction:
    def test_function_uses_create_or_replace(self) -> None:
        # ``CREATE OR REPLACE`` is the idempotent form for functions.
        src = _migration_source()
        assert re.search(
            r"CREATE OR REPLACE FUNCTION compute_cycle_start",
            src,
        )

    def test_function_signature(self) -> None:
        src = _migration_source()
        assert "p_tenant UUID" in src
        assert "p_date DATE" in src
        assert "RETURNS DATE" in src

    def test_function_is_immutable(self) -> None:
        # IMMUTABLE lets Postgres inline + cache the result; required for
        # use in generated columns and indexes if someone wires it later.
        src = _migration_source()
        assert "IMMUTABLE" in src

    def test_function_falls_back_to_anchor_25(self) -> None:
        src = _migration_source()
        assert re.search(r"anchor\s*:=\s*25", src)

    def test_downgrade_drops_function(self) -> None:
        src = _migration_source()
        assert "DROP FUNCTION IF EXISTS compute_cycle_start" in src
