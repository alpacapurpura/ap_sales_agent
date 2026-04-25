"""LLMClassifier — F8 fallback when rule classifier defers.

Invoked only when ``RuleClassifier.classify`` returned ``None`` (no regex
match). Calls a single ``ModelRole.NANO`` LLM with a structured-output
prompt asking for ``{tier, confidence, reason}``. Returns a
``RoutingDecision`` only when ``confidence >= threshold`` — otherwise
``None`` so the chain falls through to ``policy.default_tier``.

Design notes (see learnings/F8-routing.md):

* Sync ``classify`` matches the existing ``IntentClassifier`` Protocol; the
  NANO call latency target is sub-300ms p95, acceptable inline cost for the
  ~10% of turns the rule chain doesn't catch.
* JSON parsing is permissive (fenced or bare) but tier validation is strict —
  the LLM cannot invent tiers. Any parse / validation failure returns
  ``None`` (defers to default), never raises.
* No catalogue of allowed reasons — the LLM is free to phrase it (logged
  for observability, not enforced).

# [COPILOT-LLM-CLASSIFIER-F8] -> docs/domains/copilot/redesign-2026-04/phases/F8-routing-cost-optim.md
"""

from __future__ import annotations

import contextlib
import json
import re
from typing import TYPE_CHECKING, Any

import structlog
from langchain_core.messages import HumanMessage, SystemMessage

from src.core.enums import ModelRole
from src.modules.copilot.domain.model_tier import ModelTier
from src.modules.copilot.domain.routing_policy import (
    ClassifierType,
    RoutingDecision,
    RoutingPolicy,
)

if TYPE_CHECKING:
    from src.modules.copilot.application.router.model_router import RoutingRequest

logger = structlog.get_logger()

DEFAULT_THRESHOLD: float = 0.7

_FENCED_JSON_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)
_BARE_JSON_RE = re.compile(r"(\{.*\})", re.DOTALL)

_VALID_TIERS: dict[str, ModelTier] = {tier.value: tier for tier in ModelTier}

_SYSTEM_PROMPT_ES = """Eres el clasificador de routing de Nicolify Copilot.
Recibes un mensaje del usuario + ruta actual y devuelves UN JSON con el tier
de modelo apropiado. NO conversas, NO explicas — solo el JSON.

Tiers (de menor a mayor capacidad/costo):
- ``nano``: respuestas triviales, acuses de recibo, saludos, confirmaciones
  cortas, preguntas que no requieren razonamiento.
- ``mini``: chat estándar, edición simple, descripción de campos, generación
  ligera de copy con instrucciones claras.
- ``reasoning``: comparaciones, análisis causal ("por qué"), planes de pasos,
  razonamiento explícito. No llega a auditoría completa.
- ``heavy``: auditorías, diagnósticos profundos, planes estratégicos
  multi-módulo, decisiones que cruzan brand + offer + analytics.

Devuelve EXACTAMENTE este shape, sin texto adicional:
{
  "tier": "nano" | "mini" | "reasoning" | "heavy",
  "confidence": number,
  "reason": "snake_case_short_label"
}

``confidence`` es 0.0..1.0. Si dudas entre dos tiers, baja confidence — el
sistema cae al default (mini) cuando confidence < threshold."""


def _extract_json(text: str) -> str | None:
    fenced = _FENCED_JSON_RE.search(text)
    if fenced:
        return fenced.group(1)
    bare = _BARE_JSON_RE.search(text)
    if bare:
        return bare.group(1)
    return None


def _coerce_confidence(value: Any) -> float | None:  # noqa: ANN401 — JSON value, untyped
    if value is None:
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    if f < 0.0 or f > 1.0:
        return None
    return f


class LLMClassifier:
    """LLM fallback intent classifier (NANO + structured output).

    Implements the ``IntentClassifier`` protocol. Only invoked by the
    ``ModelRouter`` chain when prior classifiers (typically ``RuleClassifier``)
    returned ``None``.
    """

    def __init__(
        self,
        policy: RoutingPolicy,
        *,
        threshold: float = DEFAULT_THRESHOLD,
        llm: object | None = None,
    ) -> None:
        """Build the classifier.

        ``threshold`` (0.0..1.0) is the minimum confidence required to emit
        a decision; below this, ``classify`` returns ``None`` so the
        ``ModelRouter`` chain falls through to ``policy.default_tier``.

        ``llm`` is injectable for tests; production resolves
        ``LLMFactory.get_service().get_client(ModelRole.NANO)`` lazily on
        first ``classify`` call.
        """
        if not 0.0 <= threshold <= 1.0:
            msg = f"threshold must be in [0.0, 1.0], got {threshold!r}"
            raise ValueError(msg)
        self._policy = policy
        self.threshold = threshold
        self._llm = llm

    def _resolve_llm(self) -> object:
        if self._llm is not None:
            return self._llm
        from src.shared.infrastructure.llm.factory import LLMFactory

        client = LLMFactory.get_service().get_client(ModelRole.NANO)
        with contextlib.suppress(AttributeError):
            client = client.bind(temperature=0.0)
        self._llm = client
        return client

    def classify(self, req: RoutingRequest) -> RoutingDecision | None:
        """Return a ``RoutingDecision`` or ``None`` to defer."""
        llm = self._resolve_llm()
        user_payload = (
            f"route: {req.route or '/'}\n"
            f"mode: {req.mode}\n"
            f"available_tools: {req.available_tool_count}\n"
            f"user_msg: {req.user_msg}"
        )
        messages = [
            SystemMessage(content=_SYSTEM_PROMPT_ES),
            HumanMessage(content=user_payload),
        ]
        try:
            response = llm.invoke(messages)  # type: ignore[attr-defined]
        except Exception:
            logger.exception("llm_classifier_invoke_failed", msg_preview=req.user_msg[:120])
            return None

        text = getattr(response, "content", None) or str(response)
        if isinstance(text, list):
            text = "\n".join(str(part) for part in text)

        blob = _extract_json(str(text))
        if blob is None:
            logger.info("llm_classifier_no_json", raw=str(text)[:200])
            return None

        try:
            parsed = json.loads(blob)
        except json.JSONDecodeError:
            logger.info("llm_classifier_invalid_json", raw=blob[:200])
            return None

        tier_value = parsed.get("tier")
        tier = _VALID_TIERS.get(tier_value) if isinstance(tier_value, str) else None
        if tier is None:
            logger.info("llm_classifier_unknown_tier", tier=tier_value)
            return None

        confidence = _coerce_confidence(parsed.get("confidence"))
        if confidence is None or confidence < self.threshold:
            logger.info(
                "llm_classifier_below_threshold",
                tier=tier_value,
                confidence=confidence,
                threshold=self.threshold,
            )
            return None

        reason = parsed.get("reason")
        reason_str = reason if isinstance(reason, str) and reason.strip() else "llm_inferred"

        return RoutingDecision(
            tier=tier,
            reason=reason_str,
            confidence=confidence,
            classifier_used=ClassifierType.LLM,
            fallback_tier=self._policy.default_tier,
        )


__all__ = ("DEFAULT_THRESHOLD", "LLMClassifier")
