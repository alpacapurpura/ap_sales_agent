"""Tests for the retention ARQ task."""

from __future__ import annotations

import datetime as dt
from unittest.mock import MagicMock

import pytest


class TestRetentionTaskRunner:
    @pytest.mark.asyncio
    async def test_invokes_delete_per_agent_table(self, monkeypatch) -> None:
        """One DELETE per (agent, table). With 2 registered agents that's 4 DELETEs."""
        from src.shared.agent_observability.workers import retention_task

        executed: list[tuple[str, dict]] = []

        class _FakeResult:
            rowcount = 7

        class _FakeSession:
            def execute(self, stmt, params=None):
                executed.append((str(stmt), dict(params) if params else {}))
                return _FakeResult()

            def commit(self) -> None:
                executed.append(("__commit__", {}))

            def rollback(self) -> None:
                executed.append(("__rollback__", {}))

            def close(self) -> None:
                executed.append(("__close__", {}))

        def _make_session() -> _FakeSession:
            return _FakeSession()

        monkeypatch.setattr(retention_task, "SessionLocal", _make_session)

        result = await retention_task.purge_expired_trace_rows({})

        statements = [s for s, _ in executed if s.startswith("DELETE")]
        # Cross-agent: copilot + sales_agent (+ campaign registered by Sub-C).
        assert any("FROM copilot_trace_event" in s for s in statements)
        assert any("FROM copilot_llm_call" in s for s in statements)
        assert any("FROM sales_agent_trace_event" in s for s in statements)
        assert any("FROM sales_agent_llm_call" in s for s in statements)
        assert any(s == "__commit__" for s, _ in executed)
        assert result["ok"] is True
        # Registry now has 3 agents (copilot + sales_agent + campaign); each
        # contributes 2 tables * 7 fake rows = 7 per table. Assert totals scale
        # linearly with the registry rather than hard-coding 2-agent counts.
        n_agents = len(result["per_agent"])
        assert result["trace_event_deleted"] == 7 * n_agents
        assert result["llm_call_deleted"] == 7 * n_agents
        assert "copilot" in result["per_agent"]
        assert "sales_agent" in result["per_agent"]
        assert "campaign" in result["per_agent"]

    @pytest.mark.asyncio
    async def test_respects_env_var_overrides(self, monkeypatch) -> None:
        """Env vars per-agent (COPILOT_* / SALES_AGENT_*) override defaults.

        Registry now includes campaign (Sub-C); the test only asserts that
        copilot and sales_agent respect their overrides — campaign rows are
        also present but use default retention (no env vars set here).
        """
        from src.shared.agent_observability.workers import retention_task

        # Track (agent_kind, table_kind, cutoff) from stmts + params.
        captured_stmts: list[tuple[str, dict]] = []

        class _FakeResult:
            rowcount = 0

        class _FakeSession:
            def execute(self, stmt, params=None):
                captured_stmts.append((str(stmt), dict(params) if params else {}))
                return _FakeResult()

            def commit(self) -> None:
                pass

            def rollback(self) -> None:
                pass

            def close(self) -> None:
                pass

        monkeypatch.setattr(retention_task, "SessionLocal", _FakeSession)
        monkeypatch.setenv("COPILOT_TRACE_RETENTION_DAYS", "7")
        monkeypatch.setenv("COPILOT_LLM_CALL_RETENTION_DAYS", "30")
        monkeypatch.setenv("SALES_AGENT_TRACE_RETENTION_DAYS", "60")
        monkeypatch.setenv("SALES_AGENT_LLM_CALL_RETENTION_DAYS", "180")

        await retention_task.purge_expired_trace_rows({})

        now = dt.datetime.now(tz=dt.UTC)

        # 2 tables per registered agent: 3 agents = 6 execute() calls minimum.
        assert len(captured_stmts) >= 4  # at least copilot + sales_agent

        # Extract cutoffs by table name rather than relying on order.
        def _cutoff_for(table: str) -> dt.datetime:
            hit = next((p["cutoff"] for stmt, p in captured_stmts if table in stmt), None)
            assert hit is not None, f"No execute() call found for table {table}"
            return hit

        copilot_trace = _cutoff_for("copilot_trace_event")
        copilot_llm = _cutoff_for("copilot_llm_call")
        sales_trace = _cutoff_for("sales_agent_trace_event")
        sales_llm = _cutoff_for("sales_agent_llm_call")

        assert (now - copilot_trace).days >= 7
        assert (now - copilot_llm).days >= 30
        assert (now - sales_trace).days >= 60
        assert (now - sales_llm).days >= 180

    @pytest.mark.asyncio
    async def test_swallows_exceptions_per_table(self, monkeypatch) -> None:
        """Failure on one table is logged, other tables continue."""
        from src.shared.agent_observability.workers import retention_task

        class _BoomSession:
            def __init__(self) -> None:
                self.rolled = False
                self.closed = False

            def execute(self, *_a, **_k):
                msg = "boom"
                raise RuntimeError(msg)

            def rollback(self) -> None:
                self.rolled = True

            def commit(self) -> None:
                pass

            def close(self) -> None:
                self.closed = True

        sess = _BoomSession()
        monkeypatch.setattr(retention_task, "SessionLocal", lambda: sess)

        result = await retention_task.purge_expired_trace_rows({})
        # Per-table errors are caught; the run still commits (no rows deleted).
        # Result is ok=True with zero deletions across all agents.
        assert result["ok"] is True
        assert result["trace_event_deleted"] == 0
        assert result["llm_call_deleted"] == 0
        assert sess.closed is True


class TestPreservesErrors:
    @pytest.mark.asyncio
    async def test_trace_event_delete_preserves_errors(self, monkeypatch) -> None:
        """trace_event deletion must NOT touch rows where status='error'."""
        from src.shared.agent_observability.workers import retention_task

        captured: list[str] = []

        class _FakeResult:
            rowcount = 0

        class _FakeSession:
            def execute(self, stmt, _params=None):
                captured.append(str(stmt))
                return _FakeResult()

            def commit(self) -> None:
                pass

            def rollback(self) -> None:
                pass

            def close(self) -> None:
                pass

        monkeypatch.setattr(retention_task, "SessionLocal", _FakeSession)
        await retention_task.purge_expired_trace_rows({})

        trace_stmt = next(s for s in captured if "copilot_trace_event" in s)
        assert "status != 'error'" in trace_stmt or "status <> 'error'" in trace_stmt


class TestSchedulerRegistration:
    def test_task_listed_in_settings(self) -> None:
        from src.shared.agent_observability.workers.retention_task import (
            purge_expired_trace_rows,
        )
        from src.workers.settings import SchedulerSettings, WorkerSettings

        assert purge_expired_trace_rows in WorkerSettings.functions
        assert purge_expired_trace_rows in SchedulerSettings.functions

    def test_cron_job_present(self) -> None:
        from src.shared.agent_observability.workers.retention_task import (
            purge_expired_trace_rows,
        )
        from src.workers.settings import SchedulerSettings

        scheduled = [getattr(j, "coroutine", None) for j in SchedulerSettings.cron_jobs]
        assert purge_expired_trace_rows in scheduled
