"""TitleGenerator — NANO auto-title for new conversations.

Rejects PII-looking titles (email, phone patterns) and caps length.
See CONTRACT §7.2, §8.3.

Post S3 PR-1 convergence: consume ``BaseChatModel`` directly via
``LLMFactory.get_service().get_client(ModelRole.NANO, temperature=0.0)``.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from langchain_core.messages import HumanMessage, SystemMessage
from luana_core_platform.core.enums import ModelRole

if TYPE_CHECKING:
    from langchain_core.language_models.chat_models import BaseChatModel
    from luana_core_copilot.domain.ports import LLMMessage


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
    """NANO auto-title generator with PII guardrails."""

    def __init__(self, llm: BaseChatModel | None = None, max_chars: int = 40) -> None:
        """Wire the LLM and cap length.

        ``llm`` is injectable for tests; production resolves
        ``LLMFactory.get_service().get_client(ModelRole.NANO, temperature=0.0)``
        lazily on first ``generate`` call.
        """
        self._llm = llm
        self._max_chars = max_chars

    def _resolve_llm(self) -> BaseChatModel:
        if self._llm is not None:
            return self._llm
        from luana_core_llm.factory import LLMFactory

        client = LLMFactory.get_service().get_client(ModelRole.NANO, temperature=0.0)
        self._llm = client
        return client

    async def generate(self, first_exchange: list[LLMMessage]) -> str:
        """Return a short title. Rejects PII; falls back to placeholder."""
        if not first_exchange:
            return _FALLBACK_TITLE

        exchange_text = "\n".join(f"[{m.role}] {m.content}" for m in first_exchange)
        system = _TITLE_SYSTEM_PROMPT.format(max_chars=self._max_chars)
        user = f"Resume el tema principal de este intercambio en un título corto.\n\n{exchange_text}"

        llm = self._resolve_llm()
        response = await llm.ainvoke(
            [
                SystemMessage(content=system),
                HumanMessage(content=user),
            ]
        )
        text = getattr(response, "content", None) or str(response)
        if isinstance(text, list):
            text = "\n".join(str(part) for part in text)

        title = str(text).strip().strip('"').strip("'")
        if not title:
            return _FALLBACK_TITLE
        if _EMAIL_RE.search(title) or _PHONE_RE.search(title):
            return _FALLBACK_TITLE
        return title[: self._max_chars]
