"""F9 — LLM-as-judge harness for golden tests + admin quality dashboard.

# [COPILOT-LLM-JUDGE-F9] -> docs/domains/copilot/redesign-2026-04/phases/F9-quality-observability.md

Multi-dimensional rubric (utility / accuracy / brand_coherence / tone) with
G-Eval-style chain-of-thought reasoning per dimension. NANO model (cheap +
fast). Sync ``evaluate`` matches the F8 ``LLMClassifier`` pattern: fail-soft
(returns ``None`` on any exception) + structured JSON output + threshold
gating.

Why multi-dim CoT (not single-score, not pairwise):

* Single-score per dim with one-line reasoning gives a dashboard-ready
  signal AND a debug trail when a regression hits — the per-dim score
  pinpoints whether brand_coherence dropped or accuracy did.
* Pairwise comparison wins for close A/B but is irrelevant for golden
  regression tracking (we have a fixed "ideal" via the rubric, not a
  baseline output).
* CoT short ("evidencia: X | score N/5") keeps tokens bounded — research
  abril 2026 (G-Eval) shows even a single line of reasoning per dim
  improves judge alignment 10-15% over zero-shot scoring.

Bias mitigation:

* Position bias — dimensions are alphabetised in the prompt (deterministic
  order, never input-dependent).
* Length bias — outputs are truncated to ``MAX_OUTPUT_CHARS`` before
  judging so the rubric scores content, not verbosity.
* Self-preference — the judge model (NANO) is intentionally smaller than
  the model under test (MINI/REASONING/HEAVY). Different family, different
  capability tier.

Cost control:

* ``temperature=0`` + ``seed=42`` for determinism. Model name + response_id
  go into ``metadata`` so silent OpenAI updates are diagnosable.
* Single LLM call per ``evaluate`` (NOT one per dimension). The rubric is
  rendered as a single JSON object with all 4 dim scores returned in one
  response.
"""

from __future__ import annotations

import contextlib
import json
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import structlog
from langchain_core.messages import HumanMessage, SystemMessage

from src.core.enums import ModelRole

if TYPE_CHECKING:
    from collections.abc import Sequence

logger = structlog.get_logger()

# Default canonical dimensions (4) — F9 §4.3.
CANONICAL_DIMENSIONS: tuple[str, ...] = (
    "accuracy",
    "brand_coherence",
    "tone",
    "utility",
)

DEFAULT_THRESHOLD: float = 3.5  # avg dim score (1..5 scale) — pass at ≥70%.
MAX_INPUT_CHARS: int = 2_000
MAX_OUTPUT_CHARS: int = 4_000
MAX_BRAND_CHARS: int = 800

_FENCED_JSON_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)
_BARE_JSON_RE = re.compile(r"(\{.*\})", re.DOTALL)

# B13-TP7 — rubric registry. Each entry is the bullet body (without the
# ordinal prefix) used by ``build_system_prompt``. Keep canonical (F9) +
# RAG (F11.5) dims in the same registry so any caller can mix-and-match.
_DIMENSION_RUBRICS: dict[str, str] = {
    # Canonical conversation rubric (F9 §4.3).
    "accuracy": (
        "**accuracy** — la respuesta refleja la verdad del tenant (datos,"
        " decisiones, configuración). Score 5 = factual + verificable; score 1"
        " = alucinación o contradice contexto."
    ),
    "brand_coherence": (
        "**brand_coherence** — la respuesta respeta voz, tono y posicionamiento"
        " de marca del tenant cuando hay brand_summary disponible. Score 5 ="
        " suena como el tenant; score 1 = genérica o inconsistente."
    ),
    "tone": (
        "**tone** — registro adecuado al canal y al rol del usuario. Score 5 ="
        " profesional + claro + español neutro LatAm (sin voseo); score 1 ="
        " robótico, tutorial seco, o usa voseo argentino."
    ),
    "utility": (
        "**utility** — la respuesta resuelve la intención del usuario o avanza"
        " la conversación. Score 5 = acciona o entrega valor; score 1 = vacía,"
        " evasiva o repite contexto."
    ),
    # RAG retrieval rubric (F11.5 weekly_rag_eval).
    "retrieval_relevance": (
        "**retrieval_relevance** — los chunks recuperados son relevantes a la"
        " pregunta. Score 5 = top-3 chunks responden directamente; score 1 ="
        " chunks irrelevantes o vacíos."
    ),
    "citation_accuracy": (
        "**citation_accuracy** — la respuesta cita la metodología o fuente"
        " correcta presente en los chunks. Score 5 = cita explícita ('según"
        " Hormozi value equation', 'aplicando StoryBrand'); score 1 = sin cita"
        " o cita mal la metodología."
    ),
    "answer_groundedness": (
        "**answer_groundedness** — la respuesta está sostenida por los chunks"
        " recuperados (no alucina). Score 5 = cada afirmación trazable al"
        " contexto recuperado; score 1 = inventa o contradice los chunks."
    ),
    "completeness": (
        "**completeness** — la respuesta cubre la pregunta sin gaps mayores."
        " Score 5 = comprehensive + accionable; score 1 = parcial o evasiva."
    ),
}


def build_system_prompt(dimensions: Sequence[str]) -> str:
    """Render the judge system prompt for the requested rubric dimensions.

    Dimensions are alphabetised inside the prompt (bias mitigation —
    deterministic position, independent of caller order). Unknown dims raise
    ``ValueError`` so a typo never silently degrades to a canonical-only run.
    """
    sorted_dims = sorted(dimensions)
    if not sorted_dims:
        msg = "build_system_prompt requires at least one dimension"
        raise ValueError(msg)

    unknown = [d for d in sorted_dims if d not in _DIMENSION_RUBRICS]
    if unknown:
        msg = f"Unknown judge dimensions: {unknown!r}"
        raise ValueError(msg)

    rubric_lines = "\n".join(f"{idx}. {_DIMENSION_RUBRICS[dim]}" for idx, dim in enumerate(sorted_dims, start=1))
    json_lines = ",\n  ".join(f'"{dim}": {{"score": <1-5>, "reason": "evidencia ≤80 chars"}}' for dim in sorted_dims)
    json_shape = "{\n  " + json_lines + "\n}"

    brand_rule = (
        "- Si falta brand_summary, evalúa brand_coherence con score 3"
        ' (neutral) y reason "sin brand_summary disponible".\n'
        if "brand_coherence" in sorted_dims
        else ""
    )

    return (
        "Eres juez de calidad del Nicolify Copilot. Evaluas respuestas del"
        " asistente contra una rúbrica multi-dimensión. Devuelves SOLO un JSON"
        " con scores 1-5 por dimensión + razón en una línea.\n\n"
        f"Dimensiones (orden alfabético, siempre las {len(sorted_dims)}):\n\n"
        f"{rubric_lines}\n\n"
        "Devuelve EXACTAMENTE este shape, sin texto adicional:\n"
        f"{json_shape}\n\n"
        "Reglas:\n"
        f"{brand_rule}"
        '- Spanish neutro siempre — tu propia salida también. Sin "vos",'
        ' "tenés", "podés".\n'
        "- No agregues comentarios fuera del JSON.\n"
    )


@dataclass(frozen=True, slots=True)
class DimensionScore:
    """One rubric dimension result."""

    name: str
    score: float
    reason: str


@dataclass(frozen=True, slots=True)
class JudgeResult:
    """Aggregate judgement for one (input, output) pair."""

    dimensions: tuple[DimensionScore, ...]
    avg_score: float
    passes_threshold: bool
    judge_model: str
    response_id: str | None = None
    raw_response: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


def _truncate(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    return value[:limit] + " [truncated]"


def _extract_json(text: str) -> str | None:
    fenced = _FENCED_JSON_RE.search(text)
    if fenced:
        return fenced.group(1)
    bare = _BARE_JSON_RE.search(text)
    if bare:
        return bare.group(1)
    return None


def _coerce_score(value: Any) -> float | None:  # noqa: ANN401 — JSON value, untyped
    if value is None:
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    if f < 1.0 or f > 5.0:
        return None
    return f


class CopilotJudge:
    """Sync LLM-judge with multi-dim rubric.

    ``llm`` is injectable for tests; production resolves NANO lazily. The
    judge never raises — any failure returns a ``JudgeResult`` with
    ``passes_threshold=False`` and the raw response stored in
    ``metadata`` so the dashboard surfaces the failure mode.
    """

    def __init__(
        self,
        *,
        llm: object | None = None,
        threshold: float = DEFAULT_THRESHOLD,
        dimensions: Sequence[str] | None = None,
    ) -> None:
        """Build the judge.

        ``dimensions`` defaults to ``CANONICAL_DIMENSIONS``; tests may
        override to validate the prompt logic. ``threshold`` is the
        minimum AVG score across dimensions for ``passes_threshold=True``.
        """
        if not 1.0 <= threshold <= 5.0:
            msg = f"threshold must be in [1.0, 5.0], got {threshold!r}"
            raise ValueError(msg)
        self._llm = llm
        self.threshold = threshold
        self.dimensions: tuple[str, ...] = tuple(dimensions) if dimensions is not None else CANONICAL_DIMENSIONS

    def _resolve_llm(self) -> object:
        if self._llm is not None:
            return self._llm
        from src.shared.infrastructure.llm.factory import LLMFactory

        client = LLMFactory.get_service().get_client(ModelRole.NANO)
        with contextlib.suppress(AttributeError):
            client = client.bind(temperature=0.0, seed=42)
        self._llm = client
        return client

    def evaluate(
        self,
        *,
        user_input: str,
        assistant_output: str,
        brand_summary: str | None = None,
        context: str | None = None,
    ) -> JudgeResult:
        """Judge a single (user_input, assistant_output) pair.

        ``brand_summary`` is the F3 lighthouse summary (per tenant). When
        absent, the judge scores ``brand_coherence`` neutral (3).

        ``context`` is optional extra context (e.g. the system prompt
        snapshot or a workflow_id) for accuracy assessment.
        """
        llm = self._resolve_llm()
        truncated_input = _truncate(user_input, MAX_INPUT_CHARS)
        truncated_output = _truncate(assistant_output, MAX_OUTPUT_CHARS)
        brand_block = (
            f"BRAND_SUMMARY:\n{_truncate(brand_summary, MAX_BRAND_CHARS)}"
            if brand_summary
            else "BRAND_SUMMARY: (no disponible — usa score neutral 3)"
        )
        context_block = f"\nCONTEXT:\n{_truncate(context, MAX_BRAND_CHARS)}" if context else ""

        user_payload = (
            f"{brand_block}{context_block}\n\n"
            f"USER_INPUT:\n{truncated_input}\n\n"
            f"ASSISTANT_OUTPUT:\n{truncated_output}\n\n"
            f"Devuelve el JSON con las {len(self.dimensions)} dimensiones."
        )
        messages = [
            SystemMessage(content=build_system_prompt(self.dimensions)),
            HumanMessage(content=user_payload),
        ]

        try:
            response = llm.invoke(messages)  # type: ignore[attr-defined]
        except Exception as exc:  # noqa: BLE001 — judge is best-effort; any failure → result with passes_threshold=False
            logger.warning(
                "copilot_judge_invoke_failed",
                error_type=type(exc).__name__,
                error_message=str(exc)[:200],
            )
            return self._failure_result(
                judge_model=self._model_name(),
                metadata={"error": "llm_invoke_failed"},
            )

        text = getattr(response, "content", None) or str(response)
        if isinstance(text, list):
            text = "\n".join(str(part) for part in text)

        response_id = self._extract_response_id(response)
        blob = _extract_json(str(text))
        if blob is None:
            return self._failure_result(
                judge_model=self._model_name(),
                response_id=response_id,
                raw_response=str(text)[:500],
                metadata={"error": "no_json_in_response"},
            )

        try:
            parsed = json.loads(blob)
        except json.JSONDecodeError:
            return self._failure_result(
                judge_model=self._model_name(),
                response_id=response_id,
                raw_response=blob[:500],
                metadata={"error": "invalid_json"},
            )

        dim_scores: list[DimensionScore] = []
        for dim in self.dimensions:
            entry = parsed.get(dim)
            if not isinstance(entry, dict):
                return self._failure_result(
                    judge_model=self._model_name(),
                    response_id=response_id,
                    raw_response=blob[:500],
                    metadata={"error": f"missing_dimension:{dim}"},
                )
            score = _coerce_score(entry.get("score"))
            if score is None:
                return self._failure_result(
                    judge_model=self._model_name(),
                    response_id=response_id,
                    raw_response=blob[:500],
                    metadata={"error": f"invalid_score:{dim}"},
                )
            reason = entry.get("reason")
            reason_str = reason.strip() if isinstance(reason, str) and reason.strip() else "—"
            dim_scores.append(DimensionScore(name=dim, score=score, reason=reason_str))

        avg = sum(d.score for d in dim_scores) / len(dim_scores)
        return JudgeResult(
            dimensions=tuple(dim_scores),
            avg_score=round(avg, 2),
            passes_threshold=avg >= self.threshold,
            judge_model=self._model_name(),
            response_id=response_id,
            raw_response=blob[:500],
            metadata={},
        )

    def _model_name(self) -> str:
        if self._llm is None:
            return "nano"
        return getattr(self._llm, "model", None) or getattr(self._llm, "model_name", None) or "nano"

    @staticmethod
    def _extract_response_id(response: object) -> str | None:
        for attr in ("id", "response_id"):
            value = getattr(response, attr, None)
            if isinstance(value, str) and value:
                return value
        meta = getattr(response, "response_metadata", None)
        if isinstance(meta, dict):
            for key in ("id", "response_id", "system_fingerprint"):
                value = meta.get(key)
                if isinstance(value, str) and value:
                    return value
        return None

    def _failure_result(
        self,
        *,
        judge_model: str,
        response_id: str | None = None,
        raw_response: str | None = None,
        metadata: dict[str, Any],
    ) -> JudgeResult:
        return JudgeResult(
            dimensions=tuple(DimensionScore(name=dim, score=0.0, reason="judge_failed") for dim in self.dimensions),
            avg_score=0.0,
            passes_threshold=False,
            judge_model=judge_model,
            response_id=response_id,
            raw_response=raw_response,
            metadata=metadata,
        )


__all__ = (
    "CANONICAL_DIMENSIONS",
    "DEFAULT_THRESHOLD",
    "CopilotJudge",
    "DimensionScore",
    "JudgeResult",
    "build_system_prompt",
)
