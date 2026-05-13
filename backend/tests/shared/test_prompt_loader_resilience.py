"""Regression guard: PromptLoader must survive DB outages.

Prior bug (deploy run 24553830928): `_get_from_db` only caught
`(KeyError, ValueError)`, so `OperationalError` (DB unreachable in CI test image)
propagated up and broke 7 unrelated tests. Production paths exposed the same risk.

This test ensures that in HYBRID mode a DB failure silently falls back to file
rendering instead of raising.
"""

from unittest.mock import patch

from sqlalchemy.exc import OperationalError

from luana_core_platform.core.config import PromptSource, settings
from luana_core_platform.infrastructure.prompts.base import PromptLoader


def test_get_from_db_catches_operational_error_and_returns_none(monkeypatch):
    """DB connection failure must not propagate out of `_get_from_db`."""
    loader = PromptLoader()

    def _raise_op_error(*_args, **_kwargs):
        stmt = "SELECT 1"
        cause = Exception("connection refused")
        raise OperationalError(stmt, {}, cause)

    monkeypatch.setattr(
        "luana_core_platform.infrastructure.prompts.base.SessionLocal",
        _raise_op_error,
    )
    assert loader._get_from_db("any_key", tenant_id=None) is None


def test_render_hybrid_falls_back_to_file_when_db_unreachable(monkeypatch):
    """HYBRID mode must render from file when DB lookup fails."""
    monkeypatch.setattr(settings, "PROMPT_SOURCE", PromptSource.HYBRID)

    loader = PromptLoader()

    def _raise_op_error(*_args, **_kwargs):
        stmt = "SELECT 1"
        cause = Exception("connection refused")
        raise OperationalError(stmt, {}, cause)

    with patch.object(loader, "_load_from_file", return_value="file-rendered") as file_stub:
        monkeypatch.setattr(
            "luana_core_platform.infrastructure.prompts.base.SessionLocal",
            _raise_op_error,
        )
        result = loader.render("copilot/base.j2")

    assert result == "file-rendered"
    file_stub.assert_called_once()
