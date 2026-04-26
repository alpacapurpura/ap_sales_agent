"""Synthesizer stage for ``ask_tenant_data``.

Single LLM FAST call that turns the executor result into a Spanish neutro
LatAm answer for the user. Two short-circuits avoid burning an LLM call when
the answer is deterministic:

* ``unknown`` plan kind → static "no entendí, reformulala" reply.
* ``empty_window`` flag (lead_count / conversation_count returned 0) → static
  "No encontré nadie en esa ventana — querés ampliarla?"-style reply.

Channel-awareness comes from the ``ChannelFormat`` registry (F7) — the
``structure_hint`` + ``max_chars`` are pulled per turn. F5 wired the seam;
F7 replaced the inline hints dict with the domain registry shared by the
``format_for_channel`` tool and provider-registered channels.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog
from langchain_core.messages import HumanMessage, SystemMessage

from src.core.enums import ModelRole
from src.modules.copilot.domain.output_channels import (
    SUPPORTED_CHANNELS,
    get_channel_format,
)

if TYPE_CHECKING:
    from src.modules.copilot.domain.ports import DataQueryPlan, DataQueryResult

logger = structlog.get_logger()


# Backwards-compat alias — F5 callers import this name. Kept as an alias to
# the registry-derived ``SUPPORTED_CHANNELS`` so a single source-of-truth
# governs every consumer.
SUPPORTED_OUTPUT_CHANNELS = SUPPORTED_CHANNELS


_BASE_SYSTEM = """Eres el copilot de Nicolify respondiendo una pregunta del usuario
sobre sus propios datos. El sistema ya hizo la búsqueda; tu trabajo es resumir
el resultado en una respuesta clara, breve y honesta.

Reglas de redacción:
- Español latinoamericano neutro tuteo (`tú`). Sin voseo.
- No inventes números: si el resultado dice ``count: 12``, decí "12".
- Si el resultado tiene rows con nombres de ofertas, mencioná los nombres como
  vienen en la fila ``name``.
- No expliques cómo lo calculaste; respondé como si conocieras el dato.
- Si la pregunta no se entiende del todo, decí qué tomaste por defecto.
"""


def _format_payload(plan: DataQueryPlan, result: DataQueryResult, flags: dict[str, Any]) -> str:
    parts: list[str] = [
        f"plan.kind: {plan.kind}",
        f"plan.filters: {dict(plan.filters)}",
        f"result.metadata: {result.metadata}",
    ]
    if result.rows:
        parts.append("result.rows:")
        parts.extend(f"  - {row}" for row in result.rows[:10])
    if flags:
        parts.append(f"flags: {flags}")
    return "\n".join(parts)


def _empty_window_reply(plan: DataQueryPlan, channel: str) -> str:
    base = "No encontré ningún registro en esa ventana de tiempo."
    if channel == "whatsapp":
        return base + " ¿Quieres que pruebe con un período más amplio?"
    return base + " Si quieres, probemos con un período más amplio."


def _unknown_intent_reply(channel: str) -> str:
    base = "No entendí del todo la pregunta."
    if channel == "whatsapp":
        return base + " ¿Podrías reformularla?"
    return base + " ¿Puedes reformularla con otras palabras?"


async def synthesize_answer(
    *,
    question: str,
    plan: DataQueryPlan,
    result: DataQueryResult,
    flags: dict[str, Any],
    output_channel: str = "chat",
    llm: object | None = None,
) -> str:
    """Generate the channel-aware answer."""
    fmt = get_channel_format(output_channel)
    channel = fmt.id

    if plan.kind == "unknown":
        return _unknown_intent_reply(channel)
    if flags.get("empty_window"):
        return _empty_window_reply(plan, channel)

    if llm is None:
        from src.shared.infrastructure.llm.factory import LLMFactory

        llm = LLMFactory.get_service().get_client(ModelRole.FAST)
        llm = llm.bind(temperature=0.2)

    system = (
        _BASE_SYSTEM
        + "\nFormato del canal "
        + fmt.label_es
        + " (id="
        + fmt.id
        + "):\n- "
        + fmt.structure_hint
        + f"\n- Máximo {fmt.max_chars} caracteres."
    )
    user = f"Pregunta del usuario: {question}\n\nResultado de la búsqueda:\n{_format_payload(plan, result, flags)}"

    messages = [SystemMessage(content=system), HumanMessage(content=user)]
    try:
        from src.modules.copilot.application.orchestrator.stream_filters import (
            INTERNAL_LLM_CONFIG,
        )

        # TP3 B1 — tag synthesizer call so its tokens never reach
        # the user-visible block_delta channel.
        response = llm.invoke(messages, config=INTERNAL_LLM_CONFIG)  # type: ignore[attr-defined]
    except Exception:
        logger.exception("synthesizer_llm_failed", question=question[:120])
        # Deterministic fallback so the user is not left without an answer.
        count = result.metadata.get("count")
        if count is not None:
            return f"Encontré {count} resultado(s)."
        return "Tuve un problema generando la respuesta."

    text = getattr(response, "content", None) or str(response)
    if isinstance(text, list):
        text = "\n".join(str(part) for part in text)
    answer = str(text).strip()
    if len(answer) > fmt.max_chars:
        answer = answer[: fmt.max_chars].rstrip() + "…"
    return answer


__all__ = ("SUPPORTED_OUTPUT_CHANNELS", "synthesize_answer")
