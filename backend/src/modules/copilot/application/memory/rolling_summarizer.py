"""RollingSummarizer — NANO async summary updater.

See CONTRACT §2.3, §7.2, §8.3.

Post S3 PR-1 convergence: consume ``BaseChatModel`` directly via
``LLMFactory.get_service().get_client(ModelRole.NANO, temperature=0.0)``
(same pattern judge / intent_classifier / synthesizer / url_inspiration
already follow). The legacy ``LLMProvider`` Protocol + streaming
``complete()`` adapter were removed (orphan layer never wired in prod).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from langchain_core.messages import HumanMessage, SystemMessage

from src.core.enums import ModelRole

if TYPE_CHECKING:
    from langchain_core.language_models.chat_models import BaseChatModel

    from src.modules.copilot.domain.ports import LLMMessage


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

    def __init__(self, llm: BaseChatModel | None = None, max_chars: int = 400) -> None:
        """Wire the LLM client and enforce a hard ``max_chars`` cap.

        ``llm`` is injectable for tests; production resolves
        ``LLMFactory.get_service().get_client(ModelRole.NANO, temperature=0.0)``
        lazily on first ``update`` call.
        """
        self._llm = llm
        self._max_chars = max_chars

    @classmethod
    def for_channel(
        cls,
        channel: str | None,
        llm: BaseChatModel | None = None,
    ) -> RollingSummarizer:
        """Return a summarizer with channel-appropriate ``max_chars``.

        PI-5 PR-2 (D-PI5-006): ``"telegram"`` resolves to
        ``SUMMARY_MAX_CHARS=600``; everything else (including ``None``)
        falls back to the default ``400``. ``llm`` flows through
        unchanged for test injection. The legacy ``__init__`` path is
        preserved for tests that want a custom cap.
        """
        from src.modules.copilot.domain.context_window import (
            get_context_window_config,
        )

        cfg = get_context_window_config(channel)
        return cls(llm=llm, max_chars=cfg.SUMMARY_MAX_CHARS)

    def _resolve_llm(self) -> BaseChatModel:
        if self._llm is not None:
            return self._llm
        from src.shared.infrastructure.llm.factory import LLMFactory

        client = LLMFactory.get_service().get_client(ModelRole.NANO, temperature=0.0)
        self._llm = client
        return client

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

        # Hard-cap: LLM may overshoot; truncate defensively.
        return str(text).strip()[: self._max_chars]
