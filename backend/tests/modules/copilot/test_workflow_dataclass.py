"""F6 — domain workflow types.

Validates the public Workflow + WorkflowNode + WorkflowTrigger + WorkflowExecutionState
contract. These dataclasses are the SSoT for the unified workflow model that
subsumes ``guided`` + ``procedure`` + ``extraction_card_flow`` (cutover happens
in F-pos; F6 ships the declarative skeleton + 2 pilots).
"""

from __future__ import annotations

import pytest
from pydantic import BaseModel, ValidationError

from src.modules.copilot.domain.workflow import (
    NodeOutput,
    Workflow,
    WorkflowExecutionState,
    WorkflowNode,
    WorkflowTrigger,
)


class _StubState(BaseModel):
    name: str = ""


def _node(node_id: str, *, handler_ref: str = "src.x:y", next_id: str | None = None) -> WorkflowNode:
    return WorkflowNode(id=node_id, handler_ref=handler_ref, next=next_id)


def _workflow(workflow_id: str = "wf_demo", *, nodes: list[WorkflowNode] | None = None) -> Workflow:
    nodes = nodes or [_node("a", next_id="b"), _node("b")]
    return Workflow(
        id=workflow_id,
        domain="brand",
        description_es="Demo wf",
        trigger=WorkflowTrigger.USER_INTENT,
        nodes=tuple(nodes),
        state_schema=_StubState,
        ui_progress_kind="plan_card",
    )


class TestWorkflowTrigger:
    def test_trigger_values_match_contract(self) -> None:
        assert WorkflowTrigger.URL_PASTED.value == "url_pasted"
        assert WorkflowTrigger.DOC_UPLOADED.value == "doc_uploaded"
        assert WorkflowTrigger.USER_INTENT.value == "user_intent"
        assert WorkflowTrigger.WIZARD_BUTTON.value == "wizard_button"


class TestWorkflowNode:
    def test_node_is_frozen(self) -> None:
        node = _node("a")
        with pytest.raises((AttributeError, TypeError)):
            node.id = "z"  # type: ignore[misc]

    def test_node_default_timeout(self) -> None:
        assert _node("a").timeout_s == 30

    def test_node_static_next_optional(self) -> None:
        # When `next` is None, handler decides via NodeOutput.next_node_id
        assert _node("a").next is None
        assert _node("a", next_id="b").next == "b"


class TestWorkflowDataclass:
    def test_workflow_is_frozen(self) -> None:
        wf = _workflow()
        with pytest.raises((AttributeError, TypeError)):
            wf.id = "other"  # type: ignore[misc]

    def test_workflow_required_fields(self) -> None:
        wf = _workflow("design_offer_from_url")
        assert wf.id == "design_offer_from_url"
        assert wf.domain == "brand"
        assert wf.description_es
        assert wf.trigger is WorkflowTrigger.USER_INTENT
        assert wf.ui_progress_kind == "plan_card"
        assert wf.max_clarify_questions == 5

    def test_workflow_nodes_is_tuple(self) -> None:
        wf = _workflow()
        assert isinstance(wf.nodes, tuple)
        # frozen tuples ensure no in-place mutation of node order.
        with pytest.raises((AttributeError, TypeError)):
            wf.nodes = ()  # type: ignore[misc]

    def test_workflow_state_schema_is_pydantic_model(self) -> None:
        wf = _workflow()
        assert issubclass(wf.state_schema, BaseModel)

    def test_workflow_get_node_returns_node(self) -> None:
        wf = _workflow()
        node = wf.get_node("a")
        assert node is not None
        assert node.id == "a"

    def test_workflow_get_node_missing_returns_none(self) -> None:
        wf = _workflow()
        assert wf.get_node("zzz") is None

    def test_workflow_first_node_returns_first(self) -> None:
        wf = _workflow()
        assert wf.first_node().id == "a"

    def test_workflow_validates_unique_node_ids(self) -> None:
        with pytest.raises(ValueError, match="duplicate"):
            Workflow(
                id="bad",
                domain="brand",
                description_es="x",
                trigger=WorkflowTrigger.USER_INTENT,
                nodes=(_node("a"), _node("a")),
                state_schema=_StubState,
                ui_progress_kind="plan_card",
            )

    def test_workflow_validates_static_next_exists(self) -> None:
        with pytest.raises(ValueError, match="unknown next"):
            Workflow(
                id="bad",
                domain="brand",
                description_es="x",
                trigger=WorkflowTrigger.USER_INTENT,
                nodes=(_node("a", next_id="zzz"),),
                state_schema=_StubState,
                ui_progress_kind="plan_card",
            )

    def test_workflow_validates_at_least_one_node(self) -> None:
        with pytest.raises(ValueError, match="at least one node"):
            Workflow(
                id="bad",
                domain="brand",
                description_es="x",
                trigger=WorkflowTrigger.USER_INTENT,
                nodes=(),
                state_schema=_StubState,
                ui_progress_kind="plan_card",
            )


class TestNodeOutput:
    def test_default_empty_data_patch(self) -> None:
        out = NodeOutput()
        assert out.data_patch == {}
        assert out.next_node_id is None
        assert out.is_terminal is False

    def test_custom_payload(self) -> None:
        out = NodeOutput(data_patch={"x": 1}, next_node_id="b", is_terminal=False)
        assert out.data_patch == {"x": 1}
        assert out.next_node_id == "b"


class TestWorkflowExecutionState:
    def test_minimal_construction(self) -> None:
        st = WorkflowExecutionState(
            workflow_id="setup_brand_minimal",
            current_node="analyze",
        )
        assert st.workflow_id == "setup_brand_minimal"
        assert st.current_node == "analyze"
        assert st.completed_nodes == []
        assert st.data == {}
        assert st.is_complete is False

    def test_to_jsonb_dict_roundtrip(self) -> None:
        st = WorkflowExecutionState(
            workflow_id="wf",
            current_node="b",
            completed_nodes=["a"],
            data={"foo": "bar"},
            is_complete=False,
        )
        payload = st.to_jsonb_dict()
        # Must be JSON-serializable shape.
        assert payload["workflow_id"] == "wf"
        assert payload["current_node"] == "b"
        assert payload["completed_nodes"] == ["a"]
        assert payload["data"] == {"foo": "bar"}
        assert payload["is_complete"] is False
        # Roundtrip.
        restored = WorkflowExecutionState.from_jsonb_dict(payload)
        assert restored == st

    def test_from_jsonb_none_returns_none(self) -> None:
        assert WorkflowExecutionState.from_jsonb_dict(None) is None

    def test_from_jsonb_malformed_returns_none(self) -> None:
        assert WorkflowExecutionState.from_jsonb_dict({}) is None
        assert WorkflowExecutionState.from_jsonb_dict({"workflow_id": "x"}) is None

    def test_extra_keys_rejected(self) -> None:
        with pytest.raises(ValidationError):
            WorkflowExecutionState(
                workflow_id="x",
                current_node="y",
                bogus="value",  # type: ignore[call-arg]
            )
