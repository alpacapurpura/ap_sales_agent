"""Synthesizer stage for ``ask_tenant_data``.

Single LLM FAST call that turns the executor result into a Spanish neutro
LatAm answer for the user. Two short-circuits avoid burning an LLM call when
the answer is deterministic:

* ``unknown`` plan kind → static "no entendí, reformulala" reply.
* ``empty_window`` flag (lead_count / conversation_count returned 0) → static
  "No encontré nadie en esa ventana — querés ampliarla?"-style reply.

Channel-awareness in F5 is light: a per-channel ``structure_hint`` is added to
the system prompt. F7 introduces the full ``ChannelFormat`` registry; F5 only
wires the seam (``chat`` + ``whatsapp`` minimum).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import structlog
from langchain_core.messages import HumanMessage, SystemMessage

from src.core.enums import ModelRole

if TYPE_CHECKING:
    from src.modules.copilot.domain.ports import DataQueryPlan, DataQueryResult

logger = structlog.get_logger()


@dataclass(frozen=True, slots=True)
class _ChannelHint:
    """Lightweight channel rules until F7 lands the full registry."""

    label: str
    structure_hint: str
    max_chars: int


_CHANNEL_HINTS: dict[str, _ChannelHint] = {
    "chat": _ChannelHint(
        label="chat",
        structure_hint=(
            "Respuesta directa de 1 a 3 oraciones. Markdown ligero permitido. "
            "Si hay nombres de ofertas, usalos textuales."
        ),
        max_chars=600,
    ),
    "whatsapp": _ChannelHint(
        label="whatsapp",
        structure_hint=(
            "Mensaje corto para WhatsApp: 1 frase con la cifra/respuesta + "
            "1 frase opcional de detalle. Sin markdown. Emoji solo si suma."
        ),
        max_chars=320,
    ),
    "email": _ChannelHint(
        label="email",
        structure_hint=(
            "Párrafo de 2-4 oraciones, tono profesional. Sin markdown. "
            "Si hay cifras, formátalas con separador de miles."
        ),
        max_chars=800,
    ),
}

SUPPORTED_OUTPUT_CHANNELS = frozenset(_CHANNEL_HINTS.keys())


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
        return base + " ¿Querés que pruebe con un período más amplio?"
    return base + " Si querés, probemos con un período más amplio."


def _unknown_intent_reply(channel: str) -> str:
    base = "No entendí del todo la pregunta."
    if channel == "whatsapp":
        return base + " ¿Podrías reformularla?"
    return base + " ¿Podés reformularla con otras palabras?"


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
    channel = output_channel if output_channel in SUPPORTED_OUTPUT_CHANNELS else "chat"

    if plan.kind == "unknown":
        return _unknown_intent_reply(channel)
    if flags.get("empty_window"):
        return _empty_window_reply(plan, channel)

    if llm is None:
        from src.shared.infrastructure.llm.factory import LLMFactory

        llm = LLMFactory.get_service().get_client(ModelRole.FAST)
        llm = llm.bind(temperature=0.2)

    hint = _CHANNEL_HINTS[channel]
    system = (
        _BASE_SYSTEM
        + "\nFormato del canal "
        + hint.label
        + ":\n- "
        + hint.structure_hint
        + f"\n- Máximo {hint.max_chars} caracteres."
    )
    user = f"Pregunta del usuario: {question}\n\nResultado de la búsqueda:\n{_format_payload(plan, result, flags)}"

    messages = [SystemMessage(content=system), HumanMessage(content=user)]
    try:
        response = llm.invoke(messages)  # type: ignore[attr-defined]
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
    if len(answer) > hint.max_chars:
        answer = answer[: hint.max_chars].rstrip() + "…"
    return answer


__all__ = ("SUPPORTED_OUTPUT_CHANNELS", "synthesize_answer")
