"""In-memory ``ConversationalChannelPort`` implementation (Fase 09.D).

Records every ``ask`` call into a list so tests can assert the sequence
of contracts emitted by the conversational loop. NOT for production —
exists to give the algorithm a concrete sink while real channel
adapters (whatsapp, telegram, voice, email) are being built.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from src.shared.links.ports.conversational_channel import ConversationalChannelPort

if TYPE_CHECKING:
    from src.shared.domain.field_contract import FieldContract


__all__ = [
    "InMemoryConversationalChannel",
]


class InMemoryConversationalChannel(ConversationalChannelPort):
    """Captures outbound questions in ``self.outbound``.

    ``outbound`` is a list of ``(FieldContract, context_dict)`` tuples
    in call order. Tests typically assert ``[c.path for c, _ in
    channel.outbound] == [...]``.
    """

    def __init__(self) -> None:
        """Initialize instance."""
        self.outbound: list[tuple[FieldContract, dict[str, Any]]] = []

    async def ask(self, contract: FieldContract, *, context: dict[str, Any] | None = None) -> None:
        """Capture ``contract`` + ``context`` (or ``{}``) in order."""
        self.outbound.append((contract, dict(context or {})))

    def clear(self) -> None:
        """Reset captured outbound."""
        self.outbound.clear()
