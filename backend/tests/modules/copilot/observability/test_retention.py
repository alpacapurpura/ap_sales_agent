"""Tests for the retention ARQ task."""

from __future__ import annotations

import datetime as dt
from unittest.mock import MagicMock

import pytest


class TestRetentionTaskRunner:
    @pytest.mark.asyncio
    async def test_invokes_two_delete_statements(self, monkeypatch) -> None:
        """One DELETE for trace_event, one for llm_call."""
        from src.modules.copilot.observability.workers import retention_task

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
        assert any("FROM copilot_trace_event" in s for s in statements)
        assert any("FROM copilot_llm_call" in s for s in statements)
        assert any(s == "__commit__" for s, _ in executed)
        assert result["ok"] is True
        assert result["trace_event_deleted"] == 7
        assert result["llm_call_deleted"] == 7

    @pytest.mark.asyncio
    async def test_respects_env_var_overrides(self, monkeypatch) -> None:
        """Env vars COPILOT_TRACE_RETENTION_DAYS / COPILOT_LLM_CALL_RETENTION_DAYS."""
        from src.modules.copilot.observability.workers import retention_task

        captured: list[dict] = []

        class _FakeResult:
            rowcount = 0

        class _FakeSession:
            def execute(self, _stmt, params=None):
                captured.append(dict(params) if params else {})
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

        await retention_task.purge_expired_trace_rows({})

        # Two execute() calls (trace then llm_call); each carries the cutoff.
        assert len(captured) == 2

        trace_cutoff = captured[0]["cutoff"]
        llm_cutoff = captured[1]["cutoff"]
        now = dt.datetime.now(tz=dt.UTC)
        assert (now - trace_cutoff).days >= 7
        assert (now - llm_cutoff).days >= 30

    @pytest.mark.asyncio
    async def test_swallows_exceptions(self, monkeypatch) -> None:
        from src.modules.copilot.observability.workers import retention_task

        class _BoomSession:
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

        def _factory():
            return sess

        monkeypatch.setattr(retention_task, "SessionLocal", _factory)

        result = await retention_task.purge_expired_trace_rows({})
        assert result["ok"] is False
        assert sess.rolled is True
        assert sess.closed is True


class TestPreservesErrors:
    @pytest.mark.asyncio
    async def test_trace_event_delete_preserves_errors(self, monkeypatch) -> None:
        """trace_event deletion must NOT touch rows where status='error'."""
        from src.modules.copilot.observability.workers import retention_task

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
        from src.modules.copilot.observability.workers.retention_task import (
            purge_expired_trace_rows,
        )
        from src.workers.settings import SchedulerSettings, WorkerSettings

        assert purge_expired_trace_rows in WorkerSettings.functions
        assert purge_expired_trace_rows in SchedulerSettings.functions

    def test_cron_job_present(self) -> None:
        from src.modules.copilot.observability.workers.retention_task import (
            purge_expired_trace_rows,
        )
        from src.workers.settings import SchedulerSettings

        scheduled = [getattr(j, "coroutine", None) for j in SchedulerSettings.cron_jobs]
        assert purge_expired_trace_rows in scheduled
