"""Reconciliation worker invariants.

Off by default. When env-enabled, compares per-tenant row counts and
flags drift > 1%. Best-effort — DB exception NEVER propagates.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock
from uuid import uuid4

import pytest


class TestEnabledFlag:
    @pytest.mark.asyncio
    async def test_off_by_default_no_op(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.delenv("SALES_AGENT_DUAL_WRITE_RECONCILE", raising=False)
        from src.modules.sales_agent.observability.workers.dual_write_reconciliation_task import (
            run_sales_agent_dual_write_reconcile,
        )

        called = {}

        def _factory() -> object:
            called["yes"] = True
            return MagicMock()

        await run_sales_agent_dual_write_reconcile({"db_factory": _factory})
        assert "yes" not in called  # factory never invoked when disabled

    @pytest.mark.asyncio
    async def test_runs_when_enabled(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("SALES_AGENT_DUAL_WRITE_RECONCILE", "1")
        from src.modules.sales_agent.observability.workers.dual_write_reconciliation_task import (
            run_sales_agent_dual_write_reconcile,
        )

        # Fake DB returns empty results — no exception, just summary log.
        db = MagicMock()
        db.execute.return_value.all.return_value = []
        await run_sales_agent_dual_write_reconcile({"db_factory": lambda: db})
        # close() called after run completes.
        assert db.close.called


class TestReconcileFunction:
    def test_per_tenant_diff_under_1pct_no_alert(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from src.modules.sales_agent.observability.workers import dual_write_reconciliation_task as mod

        tenant_id = uuid4()
        legacy_result = MagicMock()
        legacy_result.all.return_value = [(tenant_id, 100)]
        new_result = MagicMock()
        new_result.all.return_value = [(tenant_id, 100)]

        db = MagicMock()
        db.execute.side_effect = [legacy_result, new_result]

        out = mod.reconcile_per_tenant(db, since=datetime.now(tz=UTC) - timedelta(hours=1))
        key = str(tenant_id)
        assert out[key]["legacy_count"] == 100
        assert out[key]["new_count"] == 100
        assert out[key]["delta_pct"] == 0.0
        assert out[key]["drift_alert"] is False

    def test_diff_over_1pct_flags_drift(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from src.modules.sales_agent.observability.workers import dual_write_reconciliation_task as mod

        tenant_id = uuid4()
        legacy_result = MagicMock()
        legacy_result.all.return_value = [(tenant_id, 100)]
        new_result = MagicMock()
        new_result.all.return_value = [(tenant_id, 50)]

        db = MagicMock()
        db.execute.side_effect = [legacy_result, new_result]

        out = mod.reconcile_per_tenant(db, since=datetime.now(tz=UTC) - timedelta(hours=1))
        key = str(tenant_id)
        assert out[key]["delta_pct"] == 50.0
        assert out[key]["drift_alert"] is True

    def test_tenant_only_in_new_path_reported_with_full_drift(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from src.modules.sales_agent.observability.workers import dual_write_reconciliation_task as mod

        new_only = uuid4()
        legacy_result = MagicMock()
        legacy_result.all.return_value = []
        new_result = MagicMock()
        new_result.all.return_value = [(new_only, 50)]

        db = MagicMock()
        db.execute.side_effect = [legacy_result, new_result]

        out = mod.reconcile_per_tenant(db, since=datetime.now(tz=UTC) - timedelta(hours=1))
        key = str(new_only)
        assert out[key]["legacy_count"] == 0
        assert out[key]["new_count"] == 50
        assert out[key]["delta_pct"] == 100.0
        assert out[key]["drift_alert"] is True


class TestBestEffort:
    @pytest.mark.asyncio
    async def test_db_exception_does_not_propagate(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("SALES_AGENT_DUAL_WRITE_RECONCILE", "1")
        from src.modules.sales_agent.observability.workers.dual_write_reconciliation_task import (
            run_sales_agent_dual_write_reconcile,
        )

        db = MagicMock()
        db.execute.side_effect = RuntimeError("DB down")
        # Must not raise.
        await run_sales_agent_dual_write_reconcile({"db_factory": lambda: db})
        assert db.close.called
