"""F6 — deterministic Python state machine for ``Workflow`` execution.

Engine responsibilities:

- ``start(workflow, initial_data)`` — validate ``initial_data`` against
  ``workflow.state_schema``, return a fresh ``WorkflowExecutionState`` parked
  at the first declared node.
- ``step(workflow, state, context)`` — resolve the current node's handler
  via ``importlib``, await it, merge ``NodeOutput`` into a new state, advance
  to the next node id (handler override > static ``next``), and mark the
  workflow complete when the handler signals ``is_terminal=True`` or no next
  exists.
- ``run(workflow, initial_data, context)`` — convenience driver that chains
  ``start`` + repeated ``step`` until terminal, capped by ``max_iterations``.

The engine **never** invokes an LLM directly — handlers do, when they need to.
F5 demonstrated that pipelines with explicit dispatch beat LLM-driven graphs
on cost / latency for cases where dispatch is enumerable.

[COPILOT-WORKFLOW-F6]
"""

from __future__ import annotations

import importlib
import inspect
from typing import TYPE_CHECKING, Any

import structlog
from luana_core_copilot.domain.workflow import (
    NodeOutput,
    Workflow,
    WorkflowExecutionState,
    WorkflowNode,
)
from luana_core_platform.domain.datetime_utils import utc_now

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Mapping

logger = structlog.get_logger(__name__)


class WorkflowExecutionError(RuntimeError):
    """Raised when a workflow step cannot proceed (bad handler, exception, loop)."""


_DEFAULT_MAX_ITERATIONS = 32


class WorkflowEngine:
    """Stateless executor; can be re-used across requests."""

    def __init__(self, *, max_iterations: int = _DEFAULT_MAX_ITERATIONS) -> None:
        """Construct the engine; ``max_iterations`` caps ``run()`` to avoid loops."""
        self._max_iterations = max_iterations

    # ── Public API ──────────────────────────────────────────────────────────

    def start(
        self,
        workflow: Workflow,
        *,
        initial_data: Mapping[str, Any] | None = None,
    ) -> WorkflowExecutionState:
        """Validate ``initial_data`` against the schema and park at the first node."""
        data = self._validate_initial(workflow, initial_data or {})
        first = workflow.first_node()
        now = utc_now().isoformat()
        return WorkflowExecutionState(
            workflow_id=workflow.id,
            current_node=first.id,
            completed_nodes=[],
            data=data,
            is_complete=False,
            started_at=now,
            last_updated_at=now,
        )

    async def step(
        self,
        workflow: Workflow,
        state: WorkflowExecutionState,
        *,
        context: Mapping[str, Any],
    ) -> tuple[WorkflowExecutionState, NodeOutput | None]:
        """Execute the current node's handler and return the resulting state.

        Idempotent on completed workflows: returns the input state untouched
        + ``None`` output without invoking any handler.
        """
        if state.is_complete:
            return state, None

        node = workflow.get_node(state.current_node)
        if node is None:
            msg = f"Workflow {workflow.id!r}: unknown node {state.current_node!r}"
            raise WorkflowExecutionError(msg)

        handler = self._resolve_handler(workflow, node)
        try:
            output = await handler(dict(state.data), context)
        except WorkflowExecutionError:
            raise
        except Exception as exc:
            logger.exception(
                "copilot.workflow.handler_error",
                workflow_id=workflow.id,
                node_id=node.id,
                handler_ref=node.handler_ref,
            )
            msg = f"Workflow {workflow.id!r}/{node.id!r}: handler raised: {exc}"
            raise WorkflowExecutionError(msg) from exc

        if not isinstance(output, NodeOutput):
            msg = f"Workflow {workflow.id!r}/{node.id!r}: handler must return NodeOutput, got {type(output).__name__}"
            raise WorkflowExecutionError(msg)

        new_data = {**state.data, **dict(output.data_patch)}
        next_id = output.next_node_id if output.next_node_id is not None else node.next
        is_done = output.is_terminal or next_id is None

        completed = [*state.completed_nodes, node.id]
        new_state = state.model_copy(
            update={
                "current_node": next_id if not is_done else state.current_node,
                "completed_nodes": completed,
                "data": new_data,
                "is_complete": is_done,
                "last_updated_at": utc_now().isoformat(),
            },
        )
        return new_state, output

    async def run(
        self,
        workflow: Workflow,
        *,
        initial_data: Mapping[str, Any] | None = None,
        context: Mapping[str, Any],
    ) -> WorkflowExecutionState:
        """Drive the workflow start-to-finish — convenience for tests and CLI."""
        state = self.start(workflow, initial_data=initial_data)
        for _ in range(self._max_iterations):
            if state.is_complete:
                return state
            state, _ = await self.step(workflow, state, context=context)
        msg = (
            f"Workflow {workflow.id!r}: max_iterations={self._max_iterations} reached "
            f"(stuck at node {state.current_node!r})"
        )
        raise WorkflowExecutionError(msg)

    def is_complete(self, workflow: Workflow, state: WorkflowExecutionState) -> bool:
        """Return ``True`` when the workflow run reached a terminal node."""
        _ = workflow  # workflow arg kept for symmetry / future invariants
        return state.is_complete

    # ── Internals ───────────────────────────────────────────────────────────

    @staticmethod
    def _validate_initial(workflow: Workflow, data: Mapping[str, Any]) -> dict[str, Any]:
        try:
            instance = workflow.state_schema.model_validate(dict(data))
        except Exception as exc:
            msg = (
                f"Workflow {workflow.id!r}: initial_data does not match state_schema "
                f"{workflow.state_schema.__name__}: {exc}"
            )
            raise ValueError(msg) from exc
        return instance.model_dump(mode="json")

    @staticmethod
    def _resolve_handler(
        workflow: Workflow,
        node: WorkflowNode,
    ) -> Callable[[dict[str, Any], Mapping[str, Any]], Awaitable[NodeOutput]]:
        ref = node.handler_ref
        if ":" not in ref:
            msg = f"Workflow {workflow.id!r}/{node.id!r}: handler_ref {ref!r} must be 'module:fn'"
            raise WorkflowExecutionError(msg)
        module_path, _, attr = ref.partition(":")
        try:
            module = importlib.import_module(module_path)
        except ModuleNotFoundError as exc:
            msg = f"Workflow {workflow.id!r}/{node.id!r}: cannot resolve handler {ref!r}: {exc}"
            raise WorkflowExecutionError(msg) from exc
        handler = getattr(module, attr, None)
        if handler is None:
            msg = (
                f"Workflow {workflow.id!r}/{node.id!r}: cannot resolve handler {ref!r}: "
                f"module has no attribute {attr!r}"
            )
            raise WorkflowExecutionError(msg)
        if not callable(handler) or not inspect.iscoroutinefunction(handler):
            msg = f"Workflow {workflow.id!r}/{node.id!r}: handler {ref!r} must be an async callable"
            raise WorkflowExecutionError(msg)
        return handler
