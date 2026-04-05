"""Backwards-compatible re-export. Actual settings live in src/workers/settings.py."""

from src.workers.settings import SchedulerSettings, WorkerSettings  # noqa: F401
