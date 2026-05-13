"""Judge registry — 3 heterogeneous LLM judges (T-4 Story E).

D2 cement: weights ``sonnet=0.4`` / ``gpt4o=0.4`` / ``kimi=0.2`` (sum 1.0).
D15 cement: models pinned (claude-sonnet-4-6 / gpt-4o-2024-11-20 / kimi-k2.6) —
NOT floating tags. Chris ratifies upgrades + re-calibration.
D-AG-17 cement: dispatch via LiteLLM Proxy ONLY — direct ``openai`` /
``anthropic`` SDK imports forbidden in ``grader/`` (validator
``agentic_litellm_proxy_dispatch_only`` enforces).

Architecture
============

Registry pattern (NOT class hierarchy) — :class:`_JudgeAdapter` is a thin
adapter wrapping ``LiteLLMService`` with judge-specific routing metadata
(``model_override`` per judge_id). One ``LiteLLMService`` instance shared
process-wide; one ``_JudgeAdapter`` cached per judge_id.

Cost recording bridge
=====================

Judge LLM calls dispatch through the LiteLLM Proxy. ``cost_recorder``
(shared, ``litellm.callbacks`` registered process-wide) stashes
``response_cost`` keyed by ``litellm_call_id``. The shared
``BaseAgentCallbackHandler`` (Story B's ``EvalSimulatorCallbackHandler``
subclass) extracts the call_id from the LangChain response metadata and
calls :func:`pop_cost` to attach ``cost_usd`` onto the persisted
``eval_simulator_llm_call`` row. Cost-bucket invariant H7: judge calls
write to ``eval_simulator_llm_call`` ONLY (verified by arch fitness gate
``test_grader_writes_eval_only_bucket.py``, T-8 scope).

Anti-duplication §0
===================

REUSE shared abstractions verbatim:

* :class:`~src.shared.infrastructure.llm.providers.litellm.LiteLLMService`
  — canonical async dispatch via ``LangChain ainvoke`` (Story B post T-4
  cement; legacy adapters deleted PI-12 S1 T-4).
* :func:`~src.shared.agent_observability.recording.cost_recorder.pop_cost`
  — cost extraction bridge (handled by Story B callback handler, exposed
  here for type clarity).

NO mirror created. Registry pattern is local to eval test-infra.
"""

# voseo-allowed: docstring cites D-AG-17 cement glosario reference for arch fitness gate

# from __future__ import annotations PERMITTED here (judge_registry NOT in
# LangGraph compose path) per 05-guidelines.md line 17.
from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Final

import structlog

from luana_core_llm.providers.litellm import LiteLLMService

if TYPE_CHECKING:
    from tests.agentic_evals.sales_agent.grader.result import JudgeOpinion
    from tests.agentic_evals.sales_agent.simulator._internal.observability import (
        EvalSimulatorObservabilityContext,
    )

logger = structlog.get_logger()


# ──────────────────────────────────────────────────────────────────────────────
# D2 / D15 cement constants — Final to enforce module-level immutability.
# ──────────────────────────────────────────────────────────────────────────────


JUDGE_WEIGHTS: Final[dict[str, float]] = {
    "sonnet": 0.4,
    "gpt4o": 0.4,
    "kimi": 0.2,
}
"""Weighted-average coefficients per judge (D2). Must sum to 1.0."""


JUDGE_MODELS: Final[dict[str, str]] = {
    "sonnet": "claude-sonnet-4-6",  # D15 — pinned via Story B litellm canonicalization
    "gpt4o": "gpt-4o-2024-11-20",  # D15/Q3 — Chris ratifies upgrades + re-calibration
    "kimi": "kimi-k2.6",  # D15 — Kimi K2.6 production-pinned
}
"""LiteLLM Proxy model identifiers per judge_id (D15). NOT auto-tracking latest."""


# Public read-only judge_id set — convenience for callers that need to iterate
# all 3 judges without depending on JUDGE_WEIGHTS dict shape.
JUDGE_IDS: Final[tuple[str, ...]] = ("sonnet", "gpt4o", "kimi")


# ──────────────────────────────────────────────────────────────────────────────
# _JudgeAdapter — thin LiteLLM Proxy wrapper per judge.
# ──────────────────────────────────────────────────────────────────────────────


class _JudgeAdapter:
    """Thin per-judge adapter — dispatches via LiteLLM Proxy (D-AG-17 cement).

    NOT a class hierarchy — registry pattern. Reuses
    :class:`LiteLLMService` directly with ``model_override`` metadata
    propagated to LiteLLM Proxy via the LangChain ``config`` dict.

    Cost recording is handled by the shared callback handler chain wired
    on ``obs_context.langchain_config()`` — judge calls automatically
    populate ``eval_simulator_llm_call`` rows with ``cost_usd`` extracted
    via ``cost_recorder.pop_cost(litellm_call_id)`` (Story B canonical
    bridge inherited via :class:`EvalSimulatorCallbackHandler`).
    """

    def __init__(self, judge_id: str, model: str, llm_service: LiteLLMService) -> None:
        """Bind the adapter to a judge_id, pinned model, and shared LLM service."""
        if judge_id not in JUDGE_MODELS:
            msg = f"Unknown judge_id {judge_id!r}. Valid: {sorted(JUDGE_MODELS)}"
            raise KeyError(msg)
        self.judge_id = judge_id
        self.model = model
        self._llm = llm_service

    async def grade(
        self,
        prompt: list[dict[str, str]],
        *,
        weight: float,
        round_n: int,
        obs_context: EvalSimulatorObservabilityContext,
        rubric_id: str,
        rubric_version: int,
        cache_hit: bool = False,
    ) -> JudgeOpinion:
        """Dispatch judge prompt via LiteLLM Proxy and return a :class:`JudgeOpinion`.

        Best-effort: any LLM dispatch failure or JSON parse error returns a
        :class:`JudgeOpinion` with ``score=None`` (judge fail per result.py
        contract). The :class:`MajEvalScore` aggregator excludes None scores
        from variance and weighted-average computation.

        ``round_n``, ``rubric_id``, ``rubric_version``, ``cache_hit`` are
        woven into ``eval_metadata`` so the persisted ``eval_simulator_llm_call``
        row carries the 5 NEW Story E keys (grader / rubric_id / rubric_version
        / judge_id / round_n / cache_hit / injection_attempt_detected) per
        ``03-arch.md§4.7``.
        """
        from tests.agentic_evals.sales_agent.grader.result import JudgeOpinion

        # ── Build extended eval_metadata (Story E 5 NEW keys + Story B/C base) ──
        extended_eval_metadata: dict[str, Any] = dict(obs_context.eval_metadata)
        extended_eval_metadata["grader"] = "maj_eval"
        extended_eval_metadata["rubric_id"] = rubric_id
        extended_eval_metadata["rubric_version"] = str(rubric_version)
        extended_eval_metadata["judge_id"] = self.judge_id
        extended_eval_metadata["round_n"] = str(round_n)
        extended_eval_metadata["cache_hit"] = str(cache_hit).lower()

        # ── Dispatch via LiteLLM Proxy (canonical async path post Story B T-4) ──
        # LangChain BaseChatModel.ainvoke is the only async dispatch surface
        # on LiteLLMService (no .acompletion direct method — Story B pattern).
        from langchain_core.messages import (
            AIMessage,
            BaseMessage,
            HumanMessage,
            SystemMessage,
        )
        from luana_core_platform.core.enums import ModelRole

        role_map: dict[str, type[BaseMessage]] = {
            "system": SystemMessage,
            "user": HumanMessage,
            "assistant": AIMessage,
        }
        lc_messages: list[BaseMessage] = []
        for msg in prompt:
            cls_ = role_map.get(msg.get("role", ""))
            if cls_ is not None:
                lc_messages.append(cls_(content=msg.get("content", "")))

        latency_start = datetime.now(tz=timezone.utc)
        score: float | None
        confidence: float
        reasoning: str
        injection_attempt_detected: bool
        tokens_input: int = 0
        tokens_output: int = 0
        cost_usd: Decimal = Decimal(0)

        try:
            client = self._llm.get_client(role=ModelRole.AGENT)
            # Merge obs_context callbacks so cost_recorder + observability
            # rows fire automatically on LLM end. Pass model_override so
            # LiteLLM Proxy routes to the pinned judge model.
            config: dict[str, Any] = dict(obs_context.langchain_config())
            config.setdefault("metadata", {})
            config["metadata"]["eval_metadata"] = extended_eval_metadata
            config["metadata"]["model_override"] = self.model
            # ``RunnableConfig`` is a TypedDict — passing a plain dict is the
            # canonical pattern across the codebase (Story B customer_node.py
            # follows the same shape).
            response = await client.ainvoke(lc_messages, config=config)  # type: ignore[arg-type]
            content = response.content
            raw_text = content.strip() if isinstance(content, str) else ""

            # JSON-parse judge output: {score, confidence, reasoning, injection_attempt_detected}
            parsed = _parse_judge_response(raw_text)
            score = parsed["score"]
            confidence = parsed["confidence"]
            reasoning = parsed["reasoning"]
            injection_attempt_detected = parsed["injection_attempt_detected"]

            # Token usage extraction is best-effort — LangChain BaseMessage
            # response shapes vary across providers. ``response_metadata``
            # carries usage counts when surfaced by LiteLLM Proxy.
            usage = getattr(response, "response_metadata", {}) or {}
            tokens_input = int(usage.get("input_tokens", 0) or usage.get("prompt_tokens", 0) or 0)
            tokens_output = int(usage.get("output_tokens", 0) or usage.get("completion_tokens", 0) or 0)
            # ``cost_usd`` populated automatically on the persisted
            # ``eval_simulator_llm_call`` row via cost_recorder bridge —
            # we mirror Decimal(0) here as the per-opinion audit value
            # since the cost is double-tracked at the call_log level (H7).
            cost_usd = Decimal(0)
        except Exception as exc:  # noqa: BLE001 — judge fail = best-effort degradation
            logger.warning(
                "judge_registry.grade_failed",
                judge_id=self.judge_id,
                model=self.model,
                round_n=round_n,
                rubric_id=rubric_id,
                error_class=type(exc).__name__,
                error=str(exc),
            )
            score = None
            confidence = 0.0
            reasoning = f"judge_failed: {type(exc).__name__}"
            injection_attempt_detected = False

        latency_ms = int((datetime.now(tz=timezone.utc) - latency_start).total_seconds() * 1000)

        return JudgeOpinion(
            judge_id=self.judge_id,  # type: ignore[arg-type]
            model_used=self.model,
            weight=weight,
            score=score,
            reasoning=reasoning,
            confidence=confidence,
            latency_ms=latency_ms,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            cost_usd=cost_usd,
            round_n=round_n,  # type: ignore[arg-type]
            cache_hit=cache_hit,
            injection_attempt_detected=injection_attempt_detected,
        )


# ──────────────────────────────────────────────────────────────────────────────
# Process-scoped registry — single LiteLLMService + 3 cached adapters.
# ──────────────────────────────────────────────────────────────────────────────


_LLM_SERVICE: LiteLLMService | None = None
_ADAPTERS: dict[str, _JudgeAdapter] = {}


def _get_llm_service() -> LiteLLMService:
    """Process-scoped LiteLLMService singleton (lazy build).

    LiteLLMService is itself a singleton via MultiRoleLLMRouter in production,
    but here we instantiate directly since the registry is not threaded
    through the router (judges are eval-side infra, not consumer roles).
    """
    global _LLM_SERVICE  # noqa: PLW0603 — process-scoped lazy singleton (test-infra registry)
    if _LLM_SERVICE is None:
        _LLM_SERVICE = LiteLLMService()
    return _LLM_SERVICE


def get_judge(judge_id: str) -> _JudgeAdapter:
    """Resolve judge by id. Raises :class:`KeyError` on unknown.

    Process-scoped factory — :class:`_JudgeAdapter` instances are cached
    per ``judge_id`` so multiple ``get_judge('sonnet')`` calls return the
    same object. The underlying :class:`LiteLLMService` is shared across
    all 3 adapters (one HTTP client pool process-wide).
    """
    if judge_id not in JUDGE_MODELS:
        msg = f"Unknown judge_id {judge_id!r}. Valid: {sorted(JUDGE_MODELS)}"
        raise KeyError(msg)
    if judge_id not in _ADAPTERS:
        _ADAPTERS[judge_id] = _JudgeAdapter(
            judge_id=judge_id,
            model=JUDGE_MODELS[judge_id],
            llm_service=_get_llm_service(),
        )
    return _ADAPTERS[judge_id]


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────


def _parse_judge_response(raw: str) -> dict[str, Any]:
    """Parse judge JSON output. Defensive: fall back to score=None on malformed JSON.

    Expected schema (per 05-guidelines.md judge output contract):

    .. code-block:: json

        {
          "score": 0.85,
          "confidence": 0.9,
          "reasoning": "voice fidelity high; agent maintained warmth",
          "injection_attempt_detected": false
        }

    Returns a dict with all 4 keys populated. On parse failure or missing
    fields, ``score=None`` and ``reasoning`` carries the parse-failure
    diagnostic. Field clamping enforces ``0.0 <= score <= 1.0`` and
    ``0.0 <= confidence <= 1.0``.
    """
    try:
        parsed = json.loads(raw)
    except (json.JSONDecodeError, ValueError) as exc:
        return {
            "score": None,
            "confidence": 0.0,
            "reasoning": f"judge_response_parse_failed: {type(exc).__name__}: {raw[:200]}",
            "injection_attempt_detected": False,
        }

    if not isinstance(parsed, dict):
        return {
            "score": None,
            "confidence": 0.0,
            "reasoning": f"judge_response_not_object: {type(parsed).__name__}",
            "injection_attempt_detected": False,
        }

    score_raw = parsed.get("score")
    score: float | None = (
        float(score_raw) if isinstance(score_raw, (int, float)) and 0.0 <= float(score_raw) <= 1.0 else None
    )

    confidence_raw = parsed.get("confidence", 0.0)
    confidence: float = max(0.0, min(1.0, float(confidence_raw))) if isinstance(confidence_raw, (int, float)) else 0.0

    reasoning = str(parsed.get("reasoning", ""))
    injection_attempt_detected = bool(parsed.get("injection_attempt_detected", False))

    return {
        "score": score,
        "confidence": confidence,
        "reasoning": reasoning,
        "injection_attempt_detected": injection_attempt_detected,
    }
