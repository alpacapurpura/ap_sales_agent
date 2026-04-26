"""Intent classifier for ``ask_tenant_data``.

Single LLM NANO call (F8 — was FAST until F5 hook activated) that maps a
natural-language tenant question to a structured ``IntentResult`` the rest
of the pipeline can dispatch on. Keeps the LLM stage minimal: name
extraction, period phrase capture, and channel hint. Date parsing and
entity resolution stay in deterministic Python (the ``date_parser`` and
``executor`` stages) so the pipeline only burns one LLM call here
regardless of question complexity.

Tests inject ``llm=`` to bypass the real model; production resolves
``ModelRole.NANO`` via ``LLMFactory``.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

import structlog
from langchain_core.messages import HumanMessage, SystemMessage

from src.core.enums import ModelRole

logger = structlog.get_logger()

SUPPORTED_KINDS: frozenset[str] = frozenset(
    {"offer_lookup", "lead_count", "conversation_count"},
)
_FENCED_JSON_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)
_BARE_JSON_RE = re.compile(r"(\{.*\})", re.DOTALL)


@dataclass(frozen=True, slots=True)
class IntentResult:
    """Structured outcome of the intent classification pass."""

    kind: str
    name_query: str | None
    period_phrase: str | None
    channel: str | None
    raw_question: str
    confidence: float


_SYSTEM_PROMPT_ES = """Eres un clasificador de intenciones para Nicolify.
El usuario es un creador / experto / negocio que pregunta sobre sus propios datos.
Tu único trabajo es devolver UN JSON con la categoría y los slots extraídos.

Categorías posibles:
- ``offer_lookup``: pregunta por una oferta/producto/programa específico (resumen,
  detalle, comparación). Captura ``name_query`` con la mejor referencia textual
  al producto (sin pre-procesar — el motor hace fuzzy match).
- ``lead_count``: pregunta cuántas personas escribieron / contactaron / se
  inscribieron en un período. Captura ``period_phrase`` y ``channel`` si aparecen.
- ``conversation_count``: pregunta cuántas conversaciones tuvo en el copilot en
  un período. Captura ``period_phrase``.

Si no encaja en ninguna categoría → devolver ``"kind": "unknown"`` y
``"confidence": 0.2`` o menos.

Reglas:
- Español latinoamericano neutro tuteo (``tú``). Sin voseo.
- No interpretes fechas relativas — copia el ``period_phrase`` literal del usuario
  ("esta semana", "ayer", "marzo", "Q1 2026"). El siguiente paso lo resuelve.
- ``channel`` es uno de: ``whatsapp`` | ``telegram`` | ``instagram`` | ``email`` |
  ``tiktok``. Si no se menciona, ``null``.
- ``name_query`` solo aplica a ``offer_lookup``; en otras categorías es ``null``.
- ``confidence`` 0.0..1.0.

Devuelve EXACTAMENTE este shape, sin markdown ni texto extra:
{
  "kind": "offer_lookup" | "lead_count" | "conversation_count" | "unknown",
  "name_query": str | null,
  "period_phrase": str | null,
  "channel": str | null,
  "confidence": number
}
"""


def _extract_json_blob(text: str) -> str | None:
    fenced = _FENCED_JSON_RE.search(text)
    if fenced:
        return fenced.group(1)
    bare = _BARE_JSON_RE.search(text)
    if bare:
        return bare.group(1)
    return None


def _coerce_kind(value: Any) -> str:  # noqa: ANN401 — JSON value, untyped by definition
    if isinstance(value, str) and value in SUPPORTED_KINDS:
        return value
    return "unknown"


def _coerce_optional_str(value: Any) -> str | None:  # noqa: ANN401 — JSON value, untyped by definition
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _coerce_confidence(value: Any) -> float:  # noqa: ANN401 — JSON value, untyped by definition
    try:
        f = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, f))


async def classify_intent(
    question: str,
    *,
    llm: object | None = None,
) -> IntentResult:
    """Classify the question and return an ``IntentResult``.

    ``llm`` defaults to ``LLMFactory.get_service().get_client(ModelRole.NANO)``;
    tests pass a stub exposing ``invoke([messages])``.
    """
    if llm is None:
        from src.shared.infrastructure.llm.factory import LLMFactory

        llm = LLMFactory.get_service().get_client(ModelRole.NANO)
        llm = llm.bind(temperature=0.0)

    messages = [
        SystemMessage(content=_SYSTEM_PROMPT_ES),
        HumanMessage(content=question),
    ]
    try:
        from src.modules.copilot.application.orchestrator.stream_filters import (
            INTERNAL_LLM_CONFIG,
        )

        # TP3 B1 — drop intent classifier tokens from the user stream.
        response = llm.invoke(messages, config=INTERNAL_LLM_CONFIG)  # type: ignore[attr-defined]
    except Exception:
        logger.exception("intent_classifier_llm_failed", question=question[:120])
        return IntentResult(
            kind="unknown",
            name_query=None,
            period_phrase=None,
            channel=None,
            raw_question=question,
            confidence=0.0,
        )

    text = getattr(response, "content", None) or str(response)
    if isinstance(text, list):
        text = "\n".join(str(part) for part in text)

    blob = _extract_json_blob(str(text))
    if blob is None:
        return IntentResult(
            kind="unknown",
            name_query=None,
            period_phrase=None,
            channel=None,
            raw_question=question,
            confidence=0.0,
        )

    try:
        parsed = json.loads(blob)
    except json.JSONDecodeError:
        return IntentResult(
            kind="unknown",
            name_query=None,
            period_phrase=None,
            channel=None,
            raw_question=question,
            confidence=0.0,
        )

    kind = _coerce_kind(parsed.get("kind"))
    return IntentResult(
        kind=kind,
        name_query=_coerce_optional_str(parsed.get("name_query")) if kind == "offer_lookup" else None,
        period_phrase=_coerce_optional_str(parsed.get("period_phrase")),
        channel=_coerce_optional_str(parsed.get("channel")),
        raw_question=question,
        confidence=_coerce_confidence(parsed.get("confidence")),
    )


__all__ = ("SUPPORTED_KINDS", "IntentResult", "classify_intent")
