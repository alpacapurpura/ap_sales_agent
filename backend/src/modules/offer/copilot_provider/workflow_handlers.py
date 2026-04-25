"""F6 — handlers for the ``design_offer_from_url`` workflow.

F6 placeholders: the live URL→offer extraction still runs through
``copilot/application/extraction_card_flow.py`` + the existing offer
extraction pipeline. F-pos cutover absorbs that logic node-by-node into
these handlers, keeping the legacy module untouched until then.

[COPILOT-WORKFLOW-F6]
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from src.modules.copilot.domain.workflow import NodeOutput

if TYPE_CHECKING:
    from collections.abc import Mapping


async def extract_url(data: dict[str, Any], context: Mapping[str, Any]) -> NodeOutput:
    """Pull the source URL through the extraction pipeline.

    F6 placeholder: persists the existing ``source_url``. F-pos delegates to
    ``trafilatura_client`` + the offer-specific LLM extractor.
    """
    _ = context
    return NodeOutput(
        data_patch={
            "extracted_summary": data.get("extracted_summary") or "",
        },
    )


async def ask_clarifications(data: dict[str, Any], context: Mapping[str, Any]) -> NodeOutput:
    """Stage clarify questions when the extraction left gaps.

    F6 placeholder: when no pending questions remain, jumps to ``propose_offer``.
    F-pos drives the adaptive clarify loop (``ClarifyLoopController`` deferred
    to a follow-up phase).
    """
    _ = context
    pending = list(data.get("pending_questions") or [])
    if not pending:
        return NodeOutput(next_node_id="propose_offer")
    return NodeOutput(data_patch={"pending_questions": pending})


async def propose_offer(data: dict[str, Any], context: Mapping[str, Any]) -> NodeOutput:
    """Emit the proposed offer once clarifications are answered.

    F6 placeholder: terminates the workflow with whatever ``proposed_offer``
    already carries. F-pos calls the offer extraction service and stamps the
    final structured payload.
    """
    _ = context
    proposed = dict(data.get("proposed_offer") or {})
    return NodeOutput(data_patch={"proposed_offer": proposed}, is_terminal=True)
