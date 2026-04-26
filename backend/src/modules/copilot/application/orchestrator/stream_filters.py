"""Stream event filters for the copilot orchestrator.

Tools that run their own LLM pipeline as part of their body (the F4
URL inspiration analyzer, the F5 ``ask_tenant_data`` synthesizer + intent
classifier, etc.) invoke the LLM via ``llm.invoke(messages, config=...)``.
LangGraph's ``astream_events`` instruments every chat model call inside
the graph context, so without a marker those intermediate tokens leak
to the user-visible ``block_delta`` channel — the user sees JSON
streaming live during the tool execution before the sanitizer drops
it at ``block_end``. That looks like a flash-of-JSON bug in the UI.

The contract is simple: any tool that invokes an LLM internally MUST
pass :data:`INTERNAL_LLM_CONFIG` (or merge it into its own config) so
the events carry the :data:`INTERNAL_LLM_TAG` tag. The chat
orchestrator drops ``on_chat_model_stream`` events that carry the tag.

Detected during TP3 S3.1 — ``fetch_url`` analyzer streamed its full
JSON payload as user-visible deltas.
"""

from __future__ import annotations

INTERNAL_LLM_TAG = "copilot:internal"

INTERNAL_LLM_CONFIG: dict[str, list[str]] = {"tags": [INTERNAL_LLM_TAG]}


def is_internal_llm_event(event: dict) -> bool:
    """Return ``True`` when ``event`` originated from an internal tool LLM call.

    Matches both the top-level ``tags`` field (LangChain v2 events shape)
    and the ``metadata.tags`` fallback that some tracers emit. Either is
    enough — the contract is "any tag in the chain says internal".
    """
    tags = event.get("tags")
    if isinstance(tags, list | tuple) and INTERNAL_LLM_TAG in tags:
        return True
    metadata = event.get("metadata")
    if isinstance(metadata, dict):
        meta_tags = metadata.get("tags")
        if isinstance(meta_tags, list | tuple) and INTERNAL_LLM_TAG in meta_tags:
            return True
    return False


__all__ = [
    "INTERNAL_LLM_CONFIG",
    "INTERNAL_LLM_TAG",
    "is_internal_llm_event",
]
