"""TitleGenerator — NANO-tier auto-title for new conversations.

Rejects PII-looking titles (email, phone patterns) and caps length.
See CONTRACT §7.2, §8.3.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from src.modules.copilot.domain.model_tier import ModelTier
from src.modules.copilot.domain.ports import LLMMessage

if TYPE_CHECKING:
    from src.modules.copilot.domain.ports import LLMProvider


_TITLE_SYSTEM_PROMPT = (
    "Eres un generador de títulos para conversaciones de copilot. "
    "Español neutro latam, sin voseo, en minúsculas excepto nombres propios. "
    "Máximo {max_chars} caracteres. Sin emojis, sin comillas, sin punto final. "
    "Evita incluir emails, teléfonos o datos personales. "
    "Devuelve solo el título."
)


# Matches emails, phone-ish sequences, card-ish sequences (cheap guard).
_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+", re.IGNORECASE)
_PHONE_RE = re.compile(r"(?:\+?\d[\s\-]?){7,}")
_FALLBACK_TITLE = "nueva conversación"


class TitleGenerator:
    """NANO-tier auto-title generator with PII guardrails."""

    def __init__(self, llm: LLMProvider, max_chars: int = 40) -> None:
        """Wire the LLM and cap length."""
        self._llm = llm
        self._max_chars = max_chars

    async def generate(self, first_exchange: list[LLMMessage]) -> str:
        """Return a short title. Rejects PII; falls back to placeholder."""
        if not first_exchange:
            return _FALLBACK_TITLE

        exchange_text = "\n".join(f"[{m.role}] {m.content}" for m in first_exchange)
        system = _TITLE_SYSTEM_PROMPT.format(max_chars=self._max_chars)
        user = f"Resume el tema principal de este intercambio en un título corto.\n\n{exchange_text}"

        messages = [
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

        title = "".join(collected).strip().strip('"').strip("'")
        if not title:
            return _FALLBACK_TITLE
        if _EMAIL_RE.search(title) or _PHONE_RE.search(title):
            return _FALLBACK_TITLE
        return title[: self._max_chars]
