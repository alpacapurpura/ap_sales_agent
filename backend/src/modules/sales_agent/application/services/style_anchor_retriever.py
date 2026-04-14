"""Per-turn Qdrant similarity search for personality style anchors.

Injects 2-3 example exchanges similar to the current prospect message
into the sales agent prompt. This combats personality drift in long
conversations by providing fresh anchors every turn.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uuid import UUID

    from src.modules.brand.infrastructure.qdrant.style_anchor_store import StyleAnchorStore

logger = logging.getLogger(__name__)


class StyleAnchorRetriever:
    """Retrieves per-turn style anchors from Qdrant for anti-drift injection."""

    def __init__(self, style_anchor_store: StyleAnchorStore) -> None:
        """Initialize with an injected StyleAnchorStore."""
        self.store = style_anchor_store

    async def retrieve(
        self,
        tenant_id: UUID,
        profile_id: UUID,
        prospect_message: str,
        top_k: int = 3,
    ) -> list[dict]:
        """Search for similar style anchors for the given prospect message.

        Returns a list of dicts with keys:
            context_type, other_message, author_response, score.

        Returns an empty list if the store is unavailable (graceful degradation).
        """
        try:
            return await self.store.search_similar(
                tenant_id=tenant_id,
                profile_id=profile_id,
                query_text=prospect_message,
                top_k=top_k,
            )
        except Exception:  # noqa: BLE001 — agent resilience: Qdrant must never crash the agent
            logger.warning(
                "StyleAnchorRetriever: Qdrant unavailable, skipping style anchors",
                exc_info=True,
            )
            return []

    def format_as_few_shot(self, anchors: list[dict]) -> str:
        """Format anchors as few-shot examples for the system prompt.

        Returns an empty string when the anchors list is empty so callers
        can safely include the result in prompts without extra checks.
        """
        if not anchors:
            return ""

        lines: list[str] = [
            "## EJEMPLOS DE CÓMO RESPONDES (imita estos patrones):",
            "",
        ]
        for anchor in anchors:
            lines.append(f"[{anchor['context_type']}]")
            lines.append(f'Prospecto: "{anchor["other_message"]}"')
            lines.append(f'Tú: "{anchor["author_response"]}"')
            lines.append("")

        return "\n".join(lines)
