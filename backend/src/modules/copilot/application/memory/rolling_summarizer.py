"""RollingSummarizer — NANO-tier async summary updater.

See CONTRACT §2.3, §7.2, §8.3.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.modules.copilot.domain.model_tier import ModelTier
from src.modules.copilot.domain.ports import LLMMessage

if TYPE_CHECKING:
    from src.modules.copilot.domain.ports import LLMProvider


_SUMMARY_SYSTEM_PROMPT = (
    "Eres un compresor caveman en español neutro latam. "
    "Actualiza el resumen rolling de una conversación conservando solo hechos "
    "clave del usuario (intenciones, decisiones, datos de marca/oferta, "
    "compromisos pendientes). Sin voseo, usa tuteo. Máximo {max_chars} "
    "caracteres. Sin emojis. Sin floreo. Si no hay cambios significativos, "
    "reescribe el resumen previo tal cual."
)


_SUMMARY_USER_TEMPLATE = (
    "Resumen previo:\n{previous}\n\n"
    "Mensajes desplazados del contexto (más viejos primero):\n{displaced}\n\n"
    "Devuelve solo el resumen actualizado, sin prefijos ni comillas."
)


class RollingSummarizer:
    """Async summary updater invoked when messages fall out of the window."""

    def __init__(self, llm: LLMProvider, max_chars: int = 400) -> None:
        """Wire the LLMProvider and enforce a hard ``max_chars`` cap."""
        self._llm = llm
        self._max_chars = max_chars

    async def update(
        self,
        old_summary: str | None,
        displaced: list[LLMMessage],
    ) -> str:
        """Return a fresh ≤``max_chars`` summary absorbing displaced messages."""
        if not displaced:
            return (old_summary or "").strip()[: self._max_chars]

        displaced_text = "\n".join(f"[{m.role}] {m.content}" for m in displaced)
        system = _SUMMARY_SYSTEM_PROMPT.format(max_chars=self._max_chars)
        user = _SUMMARY_USER_TEMPLATE.format(
            previous=old_summary or "(sin resumen previo)",
            displaced=displaced_text,
        )

        messages: list[LLMMessage] = [
            LLMMessage(role="system", content=system),
            LLMMessage(role="user", content=user),
        ]

        collected: list[str] = []
        async for event in await self._llm.complete(
            tier=ModelTier.NANO,
            messages=messages,
            stream=False,
        ):
            if event.kind == "text":
                chunk = event.data.get("text") or event.data.get("content") or ""
                if isinstance(chunk, str):
                    collected.append(chunk)

        summary = "".join(collected).strip()
        # Hard-cap: LLM may overshoot; truncate defensively.
        return summary[: self._max_chars]
