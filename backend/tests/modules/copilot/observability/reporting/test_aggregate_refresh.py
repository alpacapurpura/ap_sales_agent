"""Tests for the daily-cost MV refresh ARQ task."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest


class TestAggregateRefreshTask:
    @pytest.mark.asyncio
    async def test_invokes_refresh_concurrently(self, monkeypatch) -> None:
        """Task issues ``REFRESH MATERIALIZED VIEW CONCURRENTLY`` SQL."""
        from src.modules.copilot.observability.workers import aggregate_refresh_task

        executed: list[str] = []

        class _FakeSession:
            def execute(self, stmt, *_args, **_kwargs):
                executed.append(str(stmt))
                return MagicMock()

            def commit(self) -> None:
                executed.append("__commit__")

            def rollback(self) -> None:
                executed.append("__rollback__")

            def close(self) -> None:
                executed.append("__close__")

        def _make_session() -> _FakeSession:
            return _FakeSession()

        monkeypatch.setattr(aggregate_refresh_task, "SessionLocal", _make_session)

        result = await aggregate_refresh_task.refresh_daily_cost_mv({})

        assert any("REFRESH MATERIALIZED VIEW CONCURRENTLY" in cmd for cmd in executed)
        assert "mv_daily_llm_cost_per_tenant" in " ".join(executed)
        assert "__commit__" in executed
        assert "__close__" in executed
        assert result["ok"] is True

    @pytest.mark.asyncio
    async def test_swallows_exceptions_and_rollbacks(self, monkeypatch) -> None:
        """Failure in refresh must NOT propagate; rollback + close called."""
        from src.modules.copilot.observability.workers import aggregate_refresh_task

        class _BoomSession:
            def execute(self, *_args, **_kwargs):
                msg = "boom"
                raise RuntimeError(msg)

            def commit(self) -> None:  # pragma: no cover
                pass

            def rollback(self) -> None:
                self.rolled = True

            def close(self) -> None:
                self.closed = True

        sess = _BoomSession()

        def _factory() -> _BoomSession:
            return sess

        monkeypatch.setattr(aggregate_refresh_task, "SessionLocal", _factory)

        result = await aggregate_refresh_task.refresh_daily_cost_mv({})

        assert result["ok"] is False
        assert sess.rolled is True
        assert sess.closed is True


class TestSchedulerRegistration:
    def test_task_listed_in_worker_settings(self) -> None:
        from src.modules.copilot.observability.workers.aggregate_refresh_task import (
            refresh_daily_cost_mv,
        )
        from src.workers.settings import SchedulerSettings, WorkerSettings

        assert refresh_daily_cost_mv in WorkerSettings.functions
        assert refresh_daily_cost_mv in SchedulerSettings.functions

    def test_cron_job_present_for_hourly_refresh(self) -> None:
        from src.modules.copilot.observability.workers.aggregate_refresh_task import (
            refresh_daily_cost_mv,
        )
        from src.workers.settings import SchedulerSettings

        # The arq Cron object stores its callable on ``coroutine``.
        scheduled_callables = [getattr(job, "coroutine", None) for job in SchedulerSettings.cron_jobs]
        assert refresh_daily_cost_mv in scheduled_callables
