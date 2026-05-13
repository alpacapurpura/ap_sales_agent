"""Domain message value objects for cross-channel communication."""

from typing import Any

from luana_core_platform.domain.base_entity import BaseEntity


class IncomingMessage(BaseEntity):
    """Inbound message from a user across any channel."""

    user_id: str
    text: str
    channel_type: str
    metadata: dict[str, Any] = {}


class OutgoingMessage(BaseEntity):
    """Outbound message to a user across any channel."""

    user_id: str
    text: str  # required: flattened plain-text fallback (invariant 2.2.1 of CONTRACT-MULTIMODAL)
    channel_type: str | None = None
    metadata: dict[str, Any] = {}
    # [COPILOT-OUTGOING-BLOCKS] → docs/domains/copilot/CONTRACT-MULTIMODAL.md §4
    # Rich canonical blocks. None for legacy senders; non-null for copilot/WA/rich senders.
    # Old channel adapters ignore this field and use `text` only (backward-compat).
    # When set, `text` MUST equal the flattened output of these blocks (invariant 4.0).
    blocks: list[dict] | None = None
