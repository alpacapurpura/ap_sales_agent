"""F6 — workflow engine state machine.

Engine = pure Python deterministic stepper. Resolves handler via importlib at
step time (lazy — avoids circular imports on workflow declaration). Keeps the
LLM call decision inside the handler (engine never invokes LLMs directly,
preserving the F5 lesson: LLM calls are explicit and auditable).
"""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import BaseModel

from src.modules.copilot.application.workflows.engine import (
    WorkflowEngine,
    WorkflowExecutionError,
)
from src.modules.copilot.domain.workflow import (
    NodeOutput,
    Workflow,
    WorkflowExecutionState,
    WorkflowNode,
    WorkflowTrigger,
)


class _DemoState(BaseModel):
    model_config = {"extra": "forbid"}

    score: int = 0
    note: str = ""


# ── Handlers used by tests (referenced via dotted path) ─────────────────────


async def handler_set_score(data: dict[str, Any], context: dict[str, Any]) -> NodeOutput:
    _ = context
    return NodeOutput(data_patch={"score": data.get("score", 0) + 5})


async def handler_finish(data: dict[str, Any], context: dict[str, Any]) -> NodeOutput:
    _ = (data, context)
    return NodeOutput(data_patch={"note": "done"}, is_terminal=True)


async def handler_branch(data: dict[str, Any], context: dict[str, Any]) -> NodeOutput:
    _ = context
    next_id = "high" if data.get("score", 0) >= 5 else "low"
    return NodeOutput(next_node_id=next_id)


async def handler_high(data: dict[str, Any], context: dict[str, Any]) -> NodeOutput:
    _ = (data, context)
    return NodeOutput(data_patch={"note": "high path"}, is_terminal=True)


async def handler_low(data: dict[str, Any], context: dict[str, Any]) -> NodeOutput:
    _ = (data, context)
    return NodeOutput(data_patch={"note": "low path"}, is_terminal=True)


async def handler_raise(data: dict[str, Any], context: dict[str, Any]) -> NodeOutput:
    _ = (data, context)
    msg = "boom"
    raise RuntimeError(msg)


_PREFIX = "tests.modules.copilot.test_workflow_engine"


def _linear_workflow() -> Workflow:
    return Workflow(
        id="wf_linear",
        domain="brand",
        description_es="Linear demo",
        trigger=WorkflowTrigger.USER_INTENT,
        nodes=(
            WorkflowNode(id="set_score", handler_ref=f"{_PREFIX}:handler_set_score", next="finish"),
            WorkflowNode(id="finish", handler_ref=f"{_PREFIX}:handler_finish"),
        ),
        state_schema=_DemoState,
        ui_progress_kind="plan_card",
    )


def _branching_workflow() -> Workflow:
    return Workflow(
        id="wf_branch",
        domain="offer",
        description_es="Branching demo",
        trigger=WorkflowTrigger.USER_INTENT,
        nodes=(
            WorkflowNode(id="branch", handler_ref=f"{_PREFIX}:handler_branch"),
            WorkflowNode(id="high", handler_ref=f"{_PREFIX}:handler_high"),
            WorkflowNode(id="low", handler_ref=f"{_PREFIX}:handler_low"),
        ),
        state_schema=_DemoState,
        ui_progress_kind="plan_card",
    )


# ── Tests ───────────────────────────────────────────────────────────────────


class TestWorkflowEngineStart:
    def test_start_returns_state_with_first_node(self) -> None:
        engine = WorkflowEngine()
        wf = _linear_workflow()
        state = engine.start(wf, initial_data={"score": 0})
        assert state.workflow_id == "wf_linear"
        assert state.current_node == "set_score"
        assert state.completed_nodes == []
        assert state.data["score"] == 0  # schema defaults filled (note="")
        assert state.is_complete is False

    def test_start_validates_initial_data_against_schema(self) -> None:
        engine = WorkflowEngine()
        wf = _linear_workflow()
        # _DemoState accepts arbitrary defaults; passing extra rejected.
        with pytest.raises(ValueError, match="initial_data"):
            engine.start(wf, initial_data={"unknown_field": 42})

    def test_start_with_empty_data_uses_schema_defaults(self) -> None:
        engine = WorkflowEngine()
        wf = _linear_workflow()
        state = engine.start(wf, initial_data={})
        assert state.data == {"score": 0, "note": ""}


@pytest.mark.asyncio
class TestWorkflowEngineStep:
    async def test_step_executes_handler_and_advances(self) -> None:
        engine = WorkflowEngine()
        wf = _linear_workflow()
        state = engine.start(wf, initial_data={"score": 0})
        new_state, output = await engine.step(wf, state, context={})
        assert output.data_patch == {"score": 5}
        assert new_state.current_node == "finish"
        assert new_state.completed_nodes == ["set_score"]
        assert new_state.data["score"] == 5
        assert new_state.is_complete is False
        assert new_state.last_updated_at is not None

    async def test_step_terminal_marks_complete(self) -> None:
        engine = WorkflowEngine()
        wf = _linear_workflow()
        # Skip first node — start at finish to test terminal marker.
        state = WorkflowExecutionState(
            workflow_id="wf_linear",
            current_node="finish",
            completed_nodes=["set_score"],
            data={"score": 5},
        )
        new_state, output = await engine.step(wf, state, context={})
        assert output.is_terminal is True
        assert new_state.is_complete is True
        assert new_state.completed_nodes == ["set_score", "finish"]

    async def test_step_branching_via_node_output(self) -> None:
        engine = WorkflowEngine()
        wf = _branching_workflow()
        state = engine.start(wf, initial_data={"score": 7})
        # Branch handler picks "high" because score >= 5.
        new_state, _ = await engine.step(wf, state, context={})
        assert new_state.current_node == "high"
        assert new_state.completed_nodes == ["branch"]

    async def test_step_branching_low_path(self) -> None:
        engine = WorkflowEngine()
        wf = _branching_workflow()
        state = engine.start(wf, initial_data={"score": 0})
        new_state, _ = await engine.step(wf, state, context={})
        assert new_state.current_node == "low"

    async def test_step_handler_exception_wrapped(self) -> None:
        engine = WorkflowEngine()
        wf = Workflow(
            id="wf_err",
            domain="brand",
            description_es="x",
            trigger=WorkflowTrigger.USER_INTENT,
            nodes=(WorkflowNode(id="boom", handler_ref=f"{_PREFIX}:handler_raise"),),
            state_schema=_DemoState,
            ui_progress_kind="plan_card",
        )
        state = engine.start(wf, initial_data={})
        with pytest.raises(WorkflowExecutionError, match="boom"):
            await engine.step(wf, state, context={})

    async def test_step_unknown_current_node_raises(self) -> None:
        engine = WorkflowEngine()
        wf = _linear_workflow()
        state = WorkflowExecutionState(
            workflow_id="wf_linear",
            current_node="ghost",
        )
        with pytest.raises(WorkflowExecutionError, match="unknown node"):
            await engine.step(wf, state, context={})

    async def test_step_unknown_handler_raises(self) -> None:
        engine = WorkflowEngine()
        wf = Workflow(
            id="wf_bad",
            domain="brand",
            description_es="x",
            trigger=WorkflowTrigger.USER_INTENT,
            nodes=(WorkflowNode(id="a", handler_ref="src.does.not.exist:fn"),),
            state_schema=_DemoState,
            ui_progress_kind="plan_card",
        )
        state = engine.start(wf, initial_data={})
        with pytest.raises(WorkflowExecutionError, match="resolve handler"):
            await engine.step(wf, state, context={})

    async def test_step_when_already_complete_is_idempotent(self) -> None:
        engine = WorkflowEngine()
        wf = _linear_workflow()
        state = WorkflowExecutionState(
            workflow_id="wf_linear",
            current_node="finish",
            completed_nodes=["set_score", "finish"],
            is_complete=True,
        )
        # Stepping a complete workflow returns same state without invoking handler.
        new_state, output = await engine.step(wf, state, context={})
        assert new_state == state
        assert output is None or output.data_patch == {}


@pytest.mark.asyncio
class TestWorkflowEngineRun:
    async def test_run_executes_until_terminal(self) -> None:
        engine = WorkflowEngine()
        wf = _linear_workflow()
        final = await engine.run(wf, initial_data={"score": 0}, context={})
        assert final.is_complete is True
        assert final.completed_nodes == ["set_score", "finish"]
        assert final.data["score"] == 5
        assert final.data["note"] == "done"

    async def test_run_caps_iterations(self) -> None:
        engine = WorkflowEngine(max_iterations=2)
        # Self-looping infinite workflow (set_score → set_score).
        wf = Workflow(
            id="wf_loop",
            domain="brand",
            description_es="Loop",
            trigger=WorkflowTrigger.USER_INTENT,
            nodes=(WorkflowNode(id="set_score", handler_ref=f"{_PREFIX}:handler_set_score", next="set_score"),),
            state_schema=_DemoState,
            ui_progress_kind="plan_card",
        )
        with pytest.raises(WorkflowExecutionError, match="max_iterations"):
            await engine.run(wf, initial_data={}, context={})


class TestWorkflowEngineIsComplete:
    def test_is_complete_true_when_state_complete(self) -> None:
        engine = WorkflowEngine()
        wf = _linear_workflow()
        state = WorkflowExecutionState(workflow_id="wf_linear", current_node="finish", is_complete=True)
        assert engine.is_complete(wf, state) is True

    def test_is_complete_false_otherwise(self) -> None:
        engine = WorkflowEngine()
        wf = _linear_workflow()
        state = engine.start(wf, initial_data={})
        assert engine.is_complete(wf, state) is False
