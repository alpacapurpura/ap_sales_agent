"""Tests for stream_provenance classifier + policy matrix.

Validan que ``_process_stream_event`` puede confiar en ``policy_for``
para no leak-ear events de subagentes ni de tools internos.
"""

from __future__ import annotations

import pytest

from src.modules.copilot.application.orchestrator.stream_filters import (
    INTERNAL_LLM_TAG,
)
from src.modules.copilot.application.orchestrator.stream_provenance import (
    EventOrigin,
    StreamPolicy,
    classify_event,
    policy_for,
)


class TestClassifyEvent:
    def test_root_event_no_metadata(self) -> None:
        assert classify_event({"event": "on_chat_model_end"}) is EventOrigin.ROOT

    def test_root_event_empty_checkpoint_ns(self) -> None:
        event = {
            "event": "on_chat_model_end",
            "metadata": {"langgraph_checkpoint_ns": ""},
        }
        assert classify_event(event) is EventOrigin.ROOT

    def test_root_event_unnested_checkpoint_ns(self) -> None:
        # Un solo nivel de namespace (root model node) — no hay ``|``.
        event = {
            "event": "on_chat_model_end",
            "metadata": {"langgraph_checkpoint_ns": "model:abc-123"},
        }
        assert classify_event(event) is EventOrigin.ROOT

    def test_subagent_event_via_checkpoint_ns(self) -> None:
        event = {
            "event": "on_chat_model_end",
            "metadata": {
                "langgraph_checkpoint_ns": "tools:abc|task:xyz|model:qwe",
            },
        }
        assert classify_event(event) is EventOrigin.SUBAGENT

    def test_subagent_event_via_langgraph_path_task_component(self) -> None:
        event = {
            "event": "on_chat_model_stream",
            "metadata": {"langgraph_path": ("__pregel_pull", "task", "model")},
        }
        assert classify_event(event) is EventOrigin.SUBAGENT

    def test_subagent_event_via_langgraph_path_task_with_id(self) -> None:
        event = {
            "event": "on_chat_model_stream",
            "metadata": {"langgraph_path": ("tools", "task:audit_inspector", "model")},
        }
        assert classify_event(event) is EventOrigin.SUBAGENT

    def test_internal_tool_event_via_top_level_tags(self) -> None:
        event = {
            "event": "on_chat_model_stream",
            "tags": [INTERNAL_LLM_TAG],
        }
        assert classify_event(event) is EventOrigin.INTERNAL_TOOL

    def test_internal_tool_event_via_metadata_tags(self) -> None:
        event = {
            "event": "on_chat_model_stream",
            "metadata": {"tags": [INTERNAL_LLM_TAG]},
        }
        assert classify_event(event) is EventOrigin.INTERNAL_TOOL

    def test_internal_tool_takes_precedence_over_subagent(self) -> None:
        # Si una tool interna corre dentro de un subagente, el tag interno
        # gana — ese stream YA se filtraba antes de F2 y queremos preservar
        # el comportamiento (también drop, idénticamente).
        event = {
            "event": "on_chat_model_stream",
            "tags": [INTERNAL_LLM_TAG],
            "metadata": {"langgraph_checkpoint_ns": "tools:abc|task:xyz|model:qwe"},
        }
        assert classify_event(event) is EventOrigin.INTERNAL_TOOL


class TestPolicyMatrix:
    @pytest.mark.parametrize(
        ("event", "expected"),
        [
            (
                {"event": "on_chat_model_stream", "metadata": {}},
                StreamPolicy.EMIT_TO_USER,
            ),
            (
                {"event": "on_chat_model_end", "metadata": {}},
                StreamPolicy.CAPTURE_HISTORY,
            ),
            (
                {
                    "event": "on_chat_model_stream",
                    "metadata": {"langgraph_checkpoint_ns": "tools:a|task:b|model:c"},
                },
                StreamPolicy.DROP,
            ),
            (
                {
                    "event": "on_chat_model_end",
                    "metadata": {"langgraph_checkpoint_ns": "tools:a|task:b|model:c"},
                },
                StreamPolicy.DROP,
            ),
            (
                {"event": "on_chat_model_stream", "tags": [INTERNAL_LLM_TAG]},
                StreamPolicy.DROP,
            ),
            (
                {"event": "on_chat_model_end", "tags": [INTERNAL_LLM_TAG]},
                StreamPolicy.DROP,
            ),
        ],
    )
    def test_matrix_returns_expected_policy(self, event: dict, expected: StreamPolicy) -> None:
        assert policy_for(event) is expected

    def test_unknown_kind_defaults_to_drop(self) -> None:
        # tool_start/tool_end/chain events no están en la matriz — el caller
        # tiene su propio path para esos. Default DROP es safe: no
        # accidentalmente surface algo que aún no clasificamos.
        assert policy_for({"event": "on_tool_start"}) is StreamPolicy.DROP
        assert policy_for({"event": "on_chain_start"}) is StreamPolicy.DROP
        assert policy_for({}) is StreamPolicy.DROP
