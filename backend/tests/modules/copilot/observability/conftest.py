"""Local conftest — observability tests need the real ObservabilityContext.

The repo-wide ``_disable_copilot_observability`` autouse fixture in
``tests/conftest.py`` flips ``COPILOT_OBS_REBUILD_DISABLED=1`` so the
orchestrator hot path runs without persistence in WSL (no Docker
``postgres`` DNS). Tests in this folder exercise observability directly
and must override that — so we delete the env var with a higher-priority
autouse fixture scoped to this package.
"""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _enable_copilot_observability(monkeypatch):
    """Re-enable the real observability context for tests in this folder."""
    monkeypatch.delenv("COPILOT_OBS_REBUILD_DISABLED", raising=False)
