"""Tests for `_record_active_extraction_job` helper.

Covers the best-effort persist behaviour introduced in commit 8d0a63d3:
copy `paused_at_block` from guided state, skip when IDs are missing,
tolerate read/write exceptions.
"""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.modules.copilot.application.extraction.active_job_state import (
    ActiveExtractionJob,
)
from src.modules.copilot.application.guided.state import GuidedState
from src.modules.copilot.application.tools.extraction_tools import (
    _record_active_extraction_job,
)

_TENANT_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
_CONV_ID = "00000000-0000-0000-0000-000000000001"


@pytest.fixture()
def patched_persistence() -> Any:
    """Patch guided read + active-job write for in-memory verification."""
    with (
        patch(
            "src.modules.copilot.application.tools.extraction_tools.read_guided_state",
        ) as read_mock,
        patch(
            "src.modules.copilot.application.tools.extraction_tools.write_active_job",
        ) as write_mock,
    ):
        yield read_mock, write_mock


def _kwargs(**overrides: Any) -> dict[str, Any]:
    base = {
        "conversation_id": _CONV_ID,
        "tenant_id": _TENANT_ID,
        "job_id": "job-123",
        "module": "brand",
        "entity_id": None,
        "source_kind": "url",
        "source_ref": "https://example.com",
        "scope": "full",
        "mode": "initial",
        "started_at": "2026-04-23T00:00:00+00:00",
    }
    base.update(overrides)
    return base


# ── Guard clauses ────────────────────────────────────────────────────


def test_skipped_when_conversation_id_missing(patched_persistence: Any) -> None:
    read_mock, write_mock = patched_persistence
    _record_active_extraction_job(**_kwargs(conversation_id=None))
    read_mock.assert_not_called()
    write_mock.assert_not_called()


def test_skipped_when_tenant_id_missing(patched_persistence: Any) -> None:
    read_mock, write_mock = patched_persistence
    _record_active_extraction_job(**_kwargs(tenant_id=None))
    read_mock.assert_not_called()
    write_mock.assert_not_called()


# ── Happy path + paused_at_block propagation ─────────────────────────


def test_writes_with_paused_at_block_from_guided_state(
    patched_persistence: Any,
) -> None:
    read_mock, write_mock = patched_persistence
    read_mock.return_value = GuidedState(
        domain="brand",
        entity_id=None,
        current_block_id="identity",
        completed_blocks=["narrative"],
        started_at="2026-04-23T00:00:00+00:00",
    )

    _record_active_extraction_job(**_kwargs())

    read_mock.assert_called_once_with(_CONV_ID, _TENANT_ID)
    write_mock.assert_called_once()
    conv_arg, job_arg, tenant_arg = write_mock.call_args[0]
    assert conv_arg == _CONV_ID
    assert tenant_arg == _TENANT_ID
    assert isinstance(job_arg, ActiveExtractionJob)
    assert job_arg.paused_at_block == "identity"
    assert job_arg.module == "brand"
    assert job_arg.source_ref == "https://example.com"


def test_writes_without_paused_block_when_guided_inactive(
    patched_persistence: Any,
) -> None:
    read_mock, write_mock = patched_persistence
    read_mock.return_value = None

    _record_active_extraction_job(**_kwargs(module="offer", entity_id="offer-uuid"))

    write_mock.assert_called_once()
    job_arg = write_mock.call_args[0][1]
    assert job_arg.paused_at_block is None
    assert job_arg.module == "offer"
    assert job_arg.entity_id == "offer-uuid"


# ── Best-effort failure handling ─────────────────────────────────────


def test_continues_when_guided_read_raises(patched_persistence: Any) -> None:
    """A read glitch must not block the write — the job ran successfully."""
    read_mock, write_mock = patched_persistence
    read_mock.side_effect = RuntimeError("db blip")

    _record_active_extraction_job(**_kwargs())

    write_mock.assert_called_once()
    job_arg = write_mock.call_args[0][1]
    assert job_arg.paused_at_block is None


def test_swallows_write_exception(patched_persistence: Any) -> None:
    """A persistence glitch post-dispatch must not raise to the caller."""
    _read_mock, write_mock = patched_persistence
    write_mock.side_effect = RuntimeError("unreachable DB")

    # Must not raise — best-effort persist.
    _record_active_extraction_job(**_kwargs())

    write_mock.assert_called_once()


def test_active_job_state_serializes_roundtrip() -> None:
    """Sanity: ActiveExtractionJob passes through load/write intact."""
    job = ActiveExtractionJob(
        job_id="job-xyz",
        module="brand",
        entity_id=None,
        source_kind="doc",
        source_ref="asset-42",
        scope="full",
        mode="update",
        paused_at_block=None,
        started_at="2026-04-23T00:00:00+00:00",
    )
    dumped = job.to_json()
    assert isinstance(dumped, dict)
    assert dumped["module"] == "brand"
    assert dumped["source_kind"] == "doc"


# ── Regression: tenant_id propagation ─────────────────────────────────


def test_tenant_id_passed_through_to_read_and_write(
    patched_persistence: Any,
) -> None:
    """Both persistence calls must receive the tenant_id — no cross-tenant leaks."""
    read_mock, write_mock = patched_persistence
    read_mock.return_value = None

    _record_active_extraction_job(**_kwargs())

    read_mock.assert_called_once()
    assert read_mock.call_args[0] == (_CONV_ID, _TENANT_ID)
    assert write_mock.call_args[0][2] == _TENANT_ID
