"""Tests for the daily-cost MV refresh ARQ task."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest


class TestAggregateRefreshTask:
    @pytest.mark.asyncio
    async def test_refreshes_both_mvs_concurrently(self, monkeypatch) -> None:
        """Task issues ``REFRESH MATERIALIZED VIEW CONCURRENTLY`` for both MVs."""
        from luana_core_observability.workers import aggregate_refresh_task

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

        joined = " ".join(executed)
        assert "REFRESH MATERIALIZED VIEW CONCURRENTLY mv_daily_llm_cost_per_tenant" in joined
        assert "REFRESH MATERIALIZED VIEW CONCURRENTLY mv_daily_llm_cost_per_tenant_v2" in joined
        # Each successful refresh commits independently.
        assert executed.count("__commit__") == 2
        assert "__close__" in executed
        assert result["ok"] is True
        assert result["legacy_ok"] is True
        assert result["v2_ok"] is True

    @pytest.mark.asyncio
    async def test_swallows_exceptions_and_rollbacks(self, monkeypatch) -> None:
        """Failure in refresh must NOT propagate; rollback + close called."""
        from luana_core_observability.workers import aggregate_refresh_task

        class _BoomSession:
            def __init__(self) -> None:
                self.rolled_count = 0
                self.closed = False

            def execute(self, *_args, **_kwargs):
                msg = "boom"
                raise RuntimeError(msg)

            def commit(self) -> None:  # pragma: no cover
                pass

            def rollback(self) -> None:
                self.rolled_count += 1

            def close(self) -> None:
                self.closed = True

        sess = _BoomSession()
        monkeypatch.setattr(aggregate_refresh_task, "SessionLocal", lambda: sess)

        result = await aggregate_refresh_task.refresh_daily_cost_mv({})

        assert result["ok"] is False
        assert result["legacy_ok"] is False
        assert result["v2_ok"] is False
        # Each MV failure rolls back independently.
        assert sess.rolled_count == 2
        assert sess.closed is True

    @pytest.mark.asyncio
    async def test_partial_failure_marks_only_failing_mv(self, monkeypatch) -> None:
        """If only legacy MV fails, v2_ok stays True and overall ok=False."""
        from luana_core_observability.workers import aggregate_refresh_task

        class _PartialSession:
            def __init__(self) -> None:
                self.calls = 0

            def execute(self, stmt, *_args, **_kwargs):
                self.calls += 1
                if "mv_daily_llm_cost_per_tenant_v2" not in str(stmt):
                    msg = "legacy boom"
                    raise RuntimeError(msg)
                return MagicMock()

            def commit(self) -> None:
                pass

            def rollback(self) -> None:
                pass

            def close(self) -> None:
                pass

        monkeypatch.setattr(aggregate_refresh_task, "SessionLocal", _PartialSession)

        result = await aggregate_refresh_task.refresh_daily_cost_mv({})
        assert result["ok"] is False
        assert result["legacy_ok"] is False
        assert result["v2_ok"] is True


class TestSchedulerRegistration:
    def test_task_listed_in_worker_settings(self) -> None:
        from luana_core_observability.workers.aggregate_refresh_task import (
            refresh_daily_cost_mv,
        )
        from src.workers.settings import SchedulerSettings, WorkerSettings

        assert refresh_daily_cost_mv in WorkerSettings.functions
        assert refresh_daily_cost_mv in SchedulerSettings.functions

    def test_cron_job_present_for_hourly_refresh(self) -> None:
        from luana_core_observability.workers.aggregate_refresh_task import (
            refresh_daily_cost_mv,
        )
        from src.workers.settings import SchedulerSettings

        # The arq Cron object stores its callable on ``coroutine``.
        scheduled_callables = [getattr(job, "coroutine", None) for job in SchedulerSettings.cron_jobs]
        assert refresh_daily_cost_mv in scheduled_callables
