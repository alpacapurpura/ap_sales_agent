"""F6 — declarative ``Workflow`` domain types.

Replaces the placeholder ``Workflow`` shim that lived in ``ports.py`` with a
full declarative model that subsumes ``guided`` + ``procedure`` +
``extraction_card_flow`` (cutover happens in F-pos; F6 ships the skeleton +
brand/offer pilots so providers can register workflows via discovery).

Design — informed by F5 learnings:

- A ``Workflow`` is **declarative, immutable** Python data: an id, a list of
  nodes with handler refs, and a Pydantic state schema. No LLM calls happen
  at declaration time.
- The execution engine is a **deterministic Python state machine** (see
  ``application/workflows/engine.py``). Each node's handler is an async
  callable that may invoke an LLM internally — but the engine itself never
  decides *which* node runs next via an LLM. F5 demonstrated that pipelines
  with explicit dispatch beat LLM-driven subgraphs by 2-4x in cost and
  latency for cases where the dispatch domain is enumerable.
- Handlers are referenced by **dotted strings** (``"module.path:fn"``) rather
  than direct callables. This keeps ``Workflow`` instances trivially
  hashable / serialisable, dodges circular-import traps when a module
  registers a workflow whose handler lives in the same package, and lets
  arch tests verify *every* shipped handler resolves before runtime.
- State is a **Pydantic ``BaseModel``** (subclass per workflow) that the
  engine validates on ``start()`` and at every checkpoint. Persisted as
  JSONB in ``copilot_conversations.workflow_state``.

[COPILOT-WORKFLOW-F6]: see
``docs/domains/copilot/redesign-2026-04/02-architecture-target.md §3``.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from src.shared.domain.datetime_utils import utc_now


class WorkflowTrigger(StrEnum):
    """How a workflow gets started.

    Carried in the ``Workflow`` declaration so the orchestrator (F-pos) can
    pick the right workflow when (e.g.) a URL is pasted vs. a doc uploaded.
    """

    URL_PASTED = "url_pasted"
    DOC_UPLOADED = "doc_uploaded"
    USER_INTENT = "user_intent"
    WIZARD_BUTTON = "wizard_button"


@dataclass(frozen=True, slots=True)
class WorkflowNode:
    """One step in a ``Workflow``.

    ``handler_ref`` is a ``"module.path:fn"`` string the engine resolves at
    step time via ``importlib.import_module``. The handler signature is
    ``async (data: dict, context: Mapping) -> NodeOutput``.

    ``next`` is the static next-node id when the handler returns no override.
    Set ``None`` when the handler always picks the next node dynamically (via
    ``NodeOutput.next_node_id``) — useful for branching nodes.
    """

    id: str
    handler_ref: str
    next: str | None = None
    timeout_s: int = 30


@dataclass(frozen=True, slots=True)
class NodeOutput:
    """Result of one node's handler invocation.

    ``data_patch`` is shallow-merged into the workflow state's ``data`` dict.
    ``next_node_id`` overrides ``WorkflowNode.next`` (or fills it when ``next``
    is None). ``is_terminal=True`` short-circuits the engine to mark the
    workflow complete after this node.
    """

    data_patch: Mapping[str, Any] = field(default_factory=dict)
    next_node_id: str | None = None
    is_terminal: bool = False


@dataclass(frozen=True, slots=True)
class Workflow:
    """Declarative multi-step workflow registered by a provider.

    Validated at construction time:
    - At least one node.
    - Node ids are unique within the workflow.
    - Every static ``next`` references an existing node id.
    """

    id: str
    domain: str
    description_es: str
    trigger: WorkflowTrigger
    nodes: tuple[WorkflowNode, ...]
    state_schema: type[BaseModel]
    ui_progress_kind: str
    max_clarify_questions: int = 5
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate node ids unique + every static ``next`` resolvable."""
        if not self.nodes:
            msg = f"Workflow {self.id!r} requires at least one node"
            raise ValueError(msg)

        seen: set[str] = set()
        for node in self.nodes:
            if node.id in seen:
                msg = f"Workflow {self.id!r}: duplicate node id {node.id!r}"
                raise ValueError(msg)
            seen.add(node.id)

        for node in self.nodes:
            if node.next is not None and node.next not in seen:
                msg = f"Workflow {self.id!r}: node {node.id!r} declares unknown next {node.next!r}"
                raise ValueError(msg)

    def get_node(self, node_id: str) -> WorkflowNode | None:
        """Return the node by id, or ``None`` if absent."""
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None

    def first_node(self) -> WorkflowNode:
        """Return the first declared node — entry point for ``engine.start``."""
        return self.nodes[0]


class WorkflowExecutionState(BaseModel):
    """Persisted execution state for one in-flight workflow run.

    Lives at ``copilot_conversations.workflow_state`` (JSONB column added by
    migration ``071_copilot_workflow_state``). The legacy ``procedure_state``
    column stays during cutover; readers use ``ConversationRepository.
    get_workflow_state(..., fallback_to_procedure=True)`` to surface old rows.
    """

    model_config = ConfigDict(extra="forbid")

    workflow_id: str
    current_node: str
    completed_nodes: list[str] = Field(default_factory=list)
    data: dict[str, Any] = Field(default_factory=dict)
    is_complete: bool = False
    started_at: str = Field(default_factory=lambda: utc_now().isoformat())
    last_updated_at: str | None = None

    def to_jsonb_dict(self) -> dict[str, Any]:
        """Serialise to a JSONB-compatible plain dict."""
        return self.model_dump(mode="json")

    @classmethod
    def from_jsonb_dict(cls, payload: Mapping[str, Any] | None) -> WorkflowExecutionState | None:
        """Hydrate from a JSONB payload, returning ``None`` on missing/invalid input."""
        if not payload or not isinstance(payload, Mapping):
            return None
        if "workflow_id" not in payload or "current_node" not in payload:
            return None
        try:
            return cls.model_validate(dict(payload))
        except Exception:  # noqa: BLE001 — tolerant rehydration
            return None
