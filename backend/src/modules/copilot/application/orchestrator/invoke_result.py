"""CopilotInvokeResult — non-streaming text invocation DTO.

Internal application-layer DTO returned by ``CopilotOrchestrator.invoke_text``
for non-streaming consumers (Telegram worker; future email / Whatsapp). Never
serialized to HTTP. The Telegram worker consumes ``response_text`` and routes
it through ``format_for_channel_impl`` then ``CopilotTelegramBot.send_message``.

# [COPILOT-INVOKE-RESULT-PR2-PI5]
# -> docs/archive/2026/legacy-pis/PI-5-copilot-multicanal-telegram/
#    sprints/S2-telegram-orchestrator-memory-cache/
#    prs/PR-2-telegram-orchestrator-hookup/CONTRACT.md
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class CopilotInvokeResult(BaseModel):
    """Result of ``CopilotOrchestrator.invoke_text()`` — single-turn outcome."""

    model_config = ConfigDict(from_attributes=True, frozen=True)

    conversation_id: str
    response_text: str
    tools_called: list[str] = []
    total_tokens: int = 0
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0
    # None == ok; populated on graceful failure paths so the worker can pick
    # a friendly fallback message without inspecting exception types.
    error_kind: str | None = None


__all__ = ["CopilotInvokeResult"]
