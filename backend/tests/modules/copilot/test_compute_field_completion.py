"""Tests for `_compute_field_completion` + `_compute_pending_field_paths`.

Covers the path-splitting logic introduced in commit 8d0a63d3 that drives
both the guided-setup "don't re-ask" rule and the free-form studio
snapshot. Uses in-memory payload stubs — no DB.
"""

from __future__ import annotations

import uuid
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.modules.copilot.application.orchestrator.graph import (
    _compute_field_completion,
    _compute_pending_field_paths,
)

_TENANT_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")


def _stub_registry(payload: dict[str, Any]) -> MagicMock:
    """Fake module registry that returns a descriptor yielding ``payload``."""

    class _FakeData:
        def __init__(self, data: dict[str, Any]) -> None:
            self._data = data

        def model_dump(self, mode: str = "json") -> dict[str, Any]:
            return self._data

    class _FakeRepo:
        pass

    descriptor = SimpleNamespace(
        repo_factory=lambda _db: _FakeRepo(),
        read_fn=lambda _repo, _tenant: _FakeData(payload),
    )
    registry = MagicMock()
    registry.get.return_value = descriptor
    return registry


@pytest.fixture()
def patched_session_and_registry() -> Any:
    session_mock = MagicMock()
    session_mock.close = MagicMock()
    with (
        patch(
            "src.modules.copilot.application.orchestrator.graph.get_module_registry",
        ) as reg_mock,
        patch(
            "src.core.database.SessionLocal",
            return_value=session_mock,
        ),
    ):
        yield reg_mock, session_mock


# ── Happy-path path splitting ────────────────────────────────────────


def test_dotted_path_finds_nested_value(patched_session_and_registry: Any) -> None:
    reg_mock, _ = patched_session_and_registry
    reg_mock.return_value = _stub_registry(
        {
            "identity": {"brand_name": "Acme", "tagline": ""},
            "positioning": {"brand_essence": None},
        },
    )

    filled, empty = _compute_field_completion(
        domain="brand",
        entity_id=None,
        field_paths=[
            "identity.brand_name",
            "identity.tagline",
            "positioning.brand_essence",
        ],
        tenant_id=_TENANT_ID,
    )
    assert filled == ["identity.brand_name"]
    # Empty string + None both count as empty.
    assert empty == ["identity.tagline", "positioning.brand_essence"]


def test_flat_path_checks_top_level_key(patched_session_and_registry: Any) -> None:
    reg_mock, _ = patched_session_and_registry
    reg_mock.return_value = _stub_registry(
        {"public_name": "Launch", "primary_outcome": None},
    )

    filled, empty = _compute_field_completion(
        domain="offer",
        entity_id="offer-123",
        field_paths=["public_name", "primary_outcome"],
        tenant_id=_TENANT_ID,
    )
    assert filled == ["public_name"]
    assert empty == ["primary_outcome"]


def test_list_value_is_filled_when_non_empty(
    patched_session_and_registry: Any,
) -> None:
    reg_mock, _ = patched_session_and_registry
    reg_mock.return_value = _stub_registry(
        {"pain_points": ["bored"], "objections": []},
    )

    filled, empty = _compute_field_completion(
        domain="buyer_persona",
        entity_id="p-1",
        field_paths=["pain_points", "objections"],
        tenant_id=_TENANT_ID,
    )
    assert filled == ["pain_points"]
    assert empty == ["objections"]


def test_missing_intermediate_key_returns_empty(
    patched_session_and_registry: Any,
) -> None:
    reg_mock, _ = patched_session_and_registry
    reg_mock.return_value = _stub_registry({"identity": {"brand_name": "Acme"}})

    filled, empty = _compute_field_completion(
        domain="brand",
        entity_id=None,
        field_paths=["identity.brand_name", "unknown.section.deep"],
        tenant_id=_TENANT_ID,
    )
    assert filled == ["identity.brand_name"]
    assert empty == ["unknown.section.deep"]


# ── Guard clauses / fallbacks ────────────────────────────────────────


def test_no_paths_returns_empty_pair() -> None:
    filled, empty = _compute_field_completion(
        domain="brand",
        entity_id=None,
        field_paths=[],
        tenant_id=_TENANT_ID,
    )
    assert filled == [] and empty == []


def test_missing_tenant_id_marks_everything_empty() -> None:
    filled, empty = _compute_field_completion(
        domain="brand",
        entity_id=None,
        field_paths=["identity.brand_name"],
        tenant_id=None,
    )
    assert filled == []
    assert empty == ["identity.brand_name"]


def test_descriptor_without_repo_marks_everything_empty() -> None:
    descriptor = SimpleNamespace(repo_factory=None, read_fn=None)
    registry = MagicMock()
    registry.get.return_value = descriptor
    with patch(
        "src.modules.copilot.application.orchestrator.graph.get_module_registry",
        return_value=registry,
    ):
        filled, empty = _compute_field_completion(
            domain="analytics",
            entity_id=None,
            field_paths=["foo", "bar"],
            tenant_id=_TENANT_ID,
        )
    assert filled == []
    assert empty == ["foo", "bar"]


def test_read_fn_exception_falls_back_to_empty(
    patched_session_and_registry: Any,
) -> None:
    reg_mock, _ = patched_session_and_registry

    def _explode(_repo: Any, _tenant: Any) -> None:
        msg = "boom"
        raise RuntimeError(msg)

    descriptor = SimpleNamespace(repo_factory=lambda _db: object(), read_fn=_explode)
    registry = MagicMock()
    registry.get.return_value = descriptor
    reg_mock.return_value = registry

    filled, empty = _compute_field_completion(
        domain="brand",
        entity_id=None,
        field_paths=["identity.brand_name"],
        tenant_id=_TENANT_ID,
    )
    assert filled == []
    assert empty == ["identity.brand_name"]


# ── Wrapper preservation ─────────────────────────────────────────────


def test_pending_wrapper_returns_only_empty_half(
    patched_session_and_registry: Any,
) -> None:
    reg_mock, _ = patched_session_and_registry
    reg_mock.return_value = _stub_registry(
        {"identity": {"brand_name": "Acme", "tagline": ""}},
    )
    pending = _compute_pending_field_paths(
        domain="brand",
        entity_id=None,
        field_paths=["identity.brand_name", "identity.tagline"],
        tenant_id=_TENANT_ID,
    )
    assert pending == ["identity.tagline"]
