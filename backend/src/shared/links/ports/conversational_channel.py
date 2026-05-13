"""ConversationalChannelPort — abstract sink for conversational questioning (Fase 09.D).

Channel-agnostic seam between the algorithm
(:func:`copilot.application.orchestrator.conversational_questioning.next_question`)
and the surfaces that show the question to a user. Each channel
(``WebGuidedChannel``, ``WhatsappChannel``, ``TelegramChannel``,
``VoiceChannel``, ``EmailChannel``) implements ``ask`` to render the
contract in its native medium.

The port lives in ``shared/links/ports/`` so any owning module can
implement it without taking a copilot dependency. The default
in-memory implementation lives in
``copilot.infrastructure.channels.in_memory_channel`` and is meant for
tests + early experiments — it captures outbound asks in a list.

ADR-015. See ``DESIGN.md`` §2.8.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from luana_core_platform.domain.field_contract import FieldContract


__all__ = [
    "ConversationalChannelPort",
]


class ConversationalChannelPort(ABC):
    """Render a ``FieldContract`` question to the end user, channel-agnostic.

    Implementations are responsible for:
    - Selecting the user-facing string (``contract.human_question_es``
      → ``contract.label_es`` → humanized path) — see
      :func:`copilot.application.guided.question_hint.build_question_hint`
      for the canonical precedence.
    - Sending it via the channel-appropriate transport (HTTP response,
      WhatsApp message, Telegram bot reply, voice TTS).
    - Recording / persisting any I/O the caller cares about.

    The port is intentionally minimal. Any extra state needed (lead /
    conversation IDs, locale overrides, branding) flows through the
    optional ``context`` mapping.
    """

    @abstractmethod
    async def ask(self, contract: FieldContract, *, context: dict[str, Any] | None = None) -> None:
        """Emit ``contract`` as a question to the user via this channel."""
