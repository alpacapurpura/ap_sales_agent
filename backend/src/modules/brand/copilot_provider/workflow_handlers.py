"""F6 — handlers for the ``setup_brand_minimal`` workflow.

Each handler is an async ``(data: dict, context: Mapping) -> NodeOutput``
callable. F6 ships **placeholder handlers**: the legacy guided engine still
runs the live brand setup. Once F-pos cutover wires the orchestrator to
``WorkflowEngine``, these handlers absorb the real logic from
``copilot/application/guided/block_generator.py`` and friends.

The placeholders preserve the contract end-to-end so:
- arch tests that verify ``handler_ref`` resolves at import time pass.
- the engine can run the workflow synthetically (tests + admin smoke).
- F-pos sees a concrete starting point, not an empty file.

[COPILOT-WORKFLOW-F6]
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from src.modules.copilot.domain.workflow import NodeOutput

if TYPE_CHECKING:
    from collections.abc import Mapping


async def probe_brand(data: dict[str, Any], context: Mapping[str, Any]) -> NodeOutput:
    """Discover which brand sections still need the user's attention.

    F6 placeholder: returns an empty ``pending_sections`` list. F-pos calls
    ``check_section_completion`` on the live brand snapshot and populates it.
    """
    _ = context
    pending = list(data.get("pending_sections") or [])
    return NodeOutput(data_patch={"pending_sections": pending})


async def ask_next_section(data: dict[str, Any], context: Mapping[str, Any]) -> NodeOutput:
    """Pick the next pending section and stage a clarify question.

    F6 placeholder: when no pending sections remain, jumps straight to the
    summary node. F-pos delegates to ``guided/block_generator`` for the
    actual question prompt.
    """
    _ = context
    pending = list(data.get("pending_sections") or [])
    if not pending:
        return NodeOutput(next_node_id="finalize_summary")
    next_section = pending[0]
    return NodeOutput(
        data_patch={
            "next_question": f"¿Qué falta en la sección {next_section}?",
        },
    )


async def finalize_summary(data: dict[str, Any], context: Mapping[str, Any]) -> NodeOutput:
    """Mark the workflow done with a snapshot of the brand summary.

    F6 placeholder: copies whatever ``summary_after`` already carries. F-pos
    triggers ``regen_brand_summary`` and stamps the fresh version here.
    """
    _ = context
    summary = data.get("summary_after") or "Marca actualizada."
    return NodeOutput(data_patch={"summary_after": summary}, is_terminal=True)
