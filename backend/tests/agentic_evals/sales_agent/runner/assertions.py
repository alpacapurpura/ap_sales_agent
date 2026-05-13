"""Multi-layer assertion library for the sales_agent eval harness (T-4).

Per ``03-arch-be.md`` § "Multi-layer assertions" + ticket T-4 acceptance
criteria A1-A4 + spec § "Story-7 placeholder", this module exposes the
five evaluative layers consumed by the smoke runner (T-5):

    Capa 1 — ``assert_trajectory``  (specialist routing audit)
    Capa 2 — ``assert_tool_calls``  (required + forbidden tool names)
    Capa 3 — ``assert_output``      (language + must_mention substrings)
    Capa 4 — ``assert_cost_recorded`` (DB row cost > 0 + ≤ budget + model match)
    Capa 5 — ``assert_latency``     (sum span durations ≤ threshold)

    Story 7 — ``assert_voice_fidelity`` placeholder (raises NotImplementedError)

Each assertion raises a typed subclass of ``LayerAssertionError`` carrying
``.layer_name`` + ``.observed`` + ``.expected`` so the smoke runner can
serialise the failure into ``assertions.json`` + emit an accionable message
naming the failing capa.

Anti-duplication §0 (``.claude/rules/anti-duplication.md``):

* PII sanitisation is applied by the artifacts writer (``runner/artifacts.py``)
  via shared canonical ``shared.agent_observability.recording.sanitization``.
  This file does NOT duplicate sanitisation.
* Cost calculation is handled by the production callback handler + shared
  ``cost_recorder``. This file READS the persisted ``cost_usd`` column;
  it does NOT recompute cost.
* Tool name registry SSoT is ``modules/sales_agent/application/tools/registry.py``.
  This file does NOT hardcode tool name lists — callers pass them via
  ``required`` / ``forbidden`` keyword args.

Tessl ``graceful-degradation`` Rule 6 (lazy import + fallback):

* ``langdetect`` is a dev-only optional dep. ``_detect_language_safe``
  imports it via ``importlib.import_module("langdetect")`` ONLY inside
  the function body — top-level ``import langdetect`` is forbidden by
  Decision B5 + ``test_assertions_module_no_top_level_langdetect_import``.
* ``ImportError`` (dep missing) and ``LangDetectException`` (no features
  extracted) both fall back to ``"unknown"``. The assertion never
  propagates language-detection exceptions.

Tenant isolation (``.claude/rules/tenant-isolation.md``):

* ``assert_cost_recorded`` filters every query by ``tenant_id`` — cross-
  tenant leakage is a security failure. The fixture
  ``visionarias_tenant_session`` provides the canonical Visionarias UUID.

Spanish neutro LATAM (``.claude/rules/spanish-text.md``):

* Assertion error messages are dev-facing diagnostics; layer names + the
  ``observed`` / ``expected`` payloads are kept ASCII to ease grep, but
  human-readable phrases use Spanish neutro (no voseo: "se esperó",
  "se observó", "no aparece").
"""

from __future__ import annotations

import fnmatch
import importlib
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Literal, Protocol, runtime_checkable

import structlog
from sqlalchemy import select

if TYPE_CHECKING:
    from uuid import UUID

logger = structlog.get_logger()


# ──────────────────────────────────────────────────────────────────────────
# Exception hierarchy
# ──────────────────────────────────────────────────────────────────────────


class LayerAssertionError(Exception):
    """Base class for every multi-layer assertion failure.

    Subclasses set ``layer_name`` as a class attribute matching the
    semantic capa (trajectory / tool_calls / output / cost / latency).
    Instances carry diagnostic ``observed`` + ``expected`` payloads so
    the smoke runner can serialise the failure verbatim into
    ``_artifacts/{run_id}/assertions.json``.
    """

    layer_name: str = "base"

    def __init__(
        self,
        message: str,
        *,
        observed: Any = None,
        expected: Any = None,
    ) -> None:
        """Construct the error with diagnostic context.

        The string form prefixes ``[capa: <layer_name>]`` so a one-line
        pytest output already names the failing layer.
        """
        prefixed = f"[capa: {self.layer_name}] {message}"
        super().__init__(prefixed)
        self.observed = observed
        self.expected = expected


class TrajectoryAssertionError(LayerAssertionError):
    """Capa 1 — specialist routing did not match the expected sequence."""

    layer_name = "trajectory"


class ToolCallAssertionError(LayerAssertionError):
    """Capa 2 — required tool absent or forbidden tool fired."""

    layer_name = "tool_calls"


class OutputAssertionError(LayerAssertionError):
    """Capa 3 — response text failed language or must_mention check."""

    layer_name = "output"


class CostAssertionError(LayerAssertionError):
    """Capa 4 — persisted LLM cost row missing, mismatched, or above budget."""

    layer_name = "cost"


class LatencyAssertionError(LayerAssertionError):
    """Capa 5 — total observed span latency exceeds threshold."""

    layer_name = "latency"


# ──────────────────────────────────────────────────────────────────────────
# Internal helpers
# ──────────────────────────────────────────────────────────────────────────


@runtime_checkable
class _SpyLike(Protocol):
    """Minimal duck-typed contract consumed by the assertion functions.

    The production spy is :class:`~tests.agentic_evals.sales_agent.runner.trajectory_spy.TrajectorySpy`,
    but the assertion API only relies on the public attributes below so
    test fixtures can inject lightweight stand-ins.
    """

    specialist_history: list[str]
    tool_calls: list[dict[str, Any]]


def _detect_language_safe(text: str) -> str:
    """Detect the language of ``text`` via ``langdetect`` with full graceful fallback.

    Two failure modes both yield ``"unknown"`` per Tessl ``graceful-
    degradation`` Rule 6:

    1. ``langdetect`` package not installed (e.g. evals optional deps
       not present in the active venv) → ``ImportError``.
    2. ``langdetect.detect`` raises ``LangDetectException`` (empty input,
       no features extracted, ambiguous) → fallback.

    Args:
        text: Free-form text to classify.

    Returns:
        ISO-639-1 language code (e.g. ``"es"``, ``"en"``) or
        ``"unknown"`` when detection is unavailable.
    """
    try:
        # Lazy import — top-level ``import langdetect`` is forbidden by
        # Decision B5 (see module docstring).
        langdetect = importlib.import_module("langdetect")
    except ImportError as exc:
        logger.warning(
            "eval_assertions_langdetect_unavailable",
            error=str(exc),
        )
        return "unknown"

    try:
        # Resolve LangDetectException lazily too — it lives in a sub-
        # module that may not load if the parent package is partially
        # broken.
        lang_exc_module = importlib.import_module("langdetect.lang_detect_exception")
        lang_detect_exception_cls: type[Exception] = lang_exc_module.LangDetectException
    except ImportError:
        # Fallback to a generic Exception — defensive only; in practice
        # langdetect.lang_detect_exception is importable whenever
        # langdetect is.
        lang_detect_exception_cls = Exception

    try:
        return langdetect.detect(text)
    except lang_detect_exception_cls as exc:
        logger.warning(
            "eval_assertions_langdetect_failed",
            error=str(exc),
        )
        return "unknown"


def _normalise_language_code(code: str) -> str:
    """Normalise a language code to its ISO-639-1 prefix.

    Caller may pass region-tagged forms (``"es-AR"``, ``"es_MX"``) but
    ``langdetect`` returns plain ``"es"``. Normalisation strips after
    the first ``-`` or ``_`` and lowercases.
    """
    return code.split("-", maxsplit=1)[0].split("_", maxsplit=1)[0].lower()


# ──────────────────────────────────────────────────────────────────────────
# Capa 1 — Trajectory
# ──────────────────────────────────────────────────────────────────────────


def assert_trajectory(
    spy: _SpyLike,
    expected_specialists: list[str],
    *,
    mode: Literal["includes", "exact"] = "includes",
) -> None:
    """Verify ``spy.specialist_history`` matches ``expected_specialists``.

    Args:
        spy: Object exposing ``specialist_history: list[str]`` (typically
            :class:`TrajectorySpy`).
        expected_specialists: Ordered list of specialist names the smoke
            test expects.
        mode: Comparison strategy.

            * ``"includes"`` (default): every name in
              ``expected_specialists`` appears at least once in
              ``spy.specialist_history`` (subset check, order-insensitive).
            * ``"exact"``: ``spy.specialist_history == expected_specialists``
              (ordered equality).

    Raises:
        TrajectoryAssertionError: when the comparison fails. The error
            carries ``observed = spy.specialist_history`` and
            ``expected = expected_specialists`` for downstream artifact
            writing.
    """
    history = list(spy.specialist_history)
    if mode == "includes":
        missing = [name for name in expected_specialists if name not in history]
        if missing:
            error_msg = f"Trayectoria incompleta: faltan especialistas {missing} en historial observado {history}."
            raise TrajectoryAssertionError(
                error_msg,
                observed=history,
                expected=expected_specialists,
            )
        return

    if mode == "exact":
        if history != list(expected_specialists):
            error_msg = f"Trayectoria no coincide exactamente. Se esperó {expected_specialists}, se observó {history}."
            raise TrajectoryAssertionError(
                error_msg,
                observed=history,
                expected=expected_specialists,
            )
        return

    invalid_mode_msg = f"mode debe ser 'includes' o 'exact', se recibió '{mode}'."
    raise ValueError(invalid_mode_msg)


# ──────────────────────────────────────────────────────────────────────────
# Capa 2 — Tool calls
# ──────────────────────────────────────────────────────────────────────────


def assert_tool_calls(
    spy: _SpyLike,
    *,
    required: list[str],
    forbidden: list[str],
) -> None:
    """Verify required tools fired and forbidden tools did NOT fire.

    Per Decision B4 (forbidden tool names sourced from
    ``modules/sales_agent/application/tools/registry.py::STAGE_TOOL_SCOPE``),
    callers pass concrete name lists — this function does NOT hardcode
    them inline so registry refactors do not break assertions silently.

    Args:
        spy: Object exposing ``tool_calls: list[dict[str, Any]]`` where
            each entry carries at least a ``"name"`` key.
        required: Tool names that MUST appear in ``spy.tool_calls``.
        forbidden: Tool names that MUST NOT appear in ``spy.tool_calls``.

    Raises:
        ToolCallAssertionError: when a required tool is missing OR a
            forbidden tool fired. ``observed`` carries the offending
            list (missing or forbidden-present); ``expected`` carries
            the input lists for context.
    """
    observed_names = {tc.get("name", "") for tc in spy.tool_calls if isinstance(tc, dict)}

    # Forbidden first — security-critical (B4 binding decision).
    forbidden_present = sorted(observed_names & set(forbidden))
    if forbidden_present:
        error_msg = (
            f"Herramientas prohibidas dispararon en este turno: {forbidden_present}. "
            f"B4 — estas tools no deben ejecutarse en el alcance del golden actual."
        )
        raise ToolCallAssertionError(
            error_msg,
            observed=forbidden_present,
            expected={"required": required, "forbidden": forbidden},
        )

    # Then required — completeness check.
    missing_required = sorted(set(required) - observed_names)
    if missing_required:
        error_msg = (
            f"Herramientas requeridas no aparecen en tool_calls observados: "
            f"{missing_required}. Tools observadas: {sorted(observed_names)}."
        )
        raise ToolCallAssertionError(
            error_msg,
            observed=sorted(observed_names),
            expected={"required": required, "forbidden": forbidden},
        )


# ──────────────────────────────────────────────────────────────────────────
# Capa 3 — Output
# ──────────────────────────────────────────────────────────────────────────


def assert_output(
    text: str,
    *,
    language: str,
    must_mention: list[str],
) -> None:
    """Verify response ``text`` is in the expected language and mentions key phrases.

    Args:
        text: Final agent response.
        language: Expected ISO-639-1 code (or region-tagged form like
            ``"es-AR"``). Comparison is case-insensitive on the prefix
            ('es' matches both 'es' and 'es-AR'). When language detection
            is unavailable (langdetect missing or returns 'unknown'),
            this check is skipped with a warning — graceful degradation.
        must_mention: Substrings (case-insensitive) that MUST each appear
            in ``text``. Empty list is accepted (skip mention check).

    Raises:
        OutputAssertionError: when language mismatch (and detection
            succeeded) OR a substring is missing. ``observed`` is the
            text + detected language; ``expected`` is the input config.
    """
    detected = _detect_language_safe(text)
    expected_lang_prefix = _normalise_language_code(language)

    if detected not in {"unknown", expected_lang_prefix}:
        error_msg = (
            f"Idioma del output no coincide. Se esperó '{language}' "
            f"(prefijo '{expected_lang_prefix}'), se detectó '{detected}'."
        )
        raise OutputAssertionError(
            error_msg,
            observed={"text": text, "language_detected": detected},
            expected={"language": language, "must_mention": must_mention},
        )

    if detected == "unknown":
        logger.warning(
            "eval_assertions_output_language_unknown",
            expected_language=language,
            text_length=len(text),
        )

    text_lower = text.lower()
    missing_phrases = [phrase for phrase in must_mention if phrase.lower() not in text_lower]
    if missing_phrases:
        error_msg = (
            f"El output no menciona las frases requeridas: {missing_phrases}. "
            f"Se esperó cada una como substring (case-insensitive) en el texto."
        )
        raise OutputAssertionError(
            error_msg,
            observed={"text": text, "language_detected": detected},
            expected={"language": language, "must_mention": must_mention},
        )


# ──────────────────────────────────────────────────────────────────────────
# Capa 4 — Cost recorded
# ──────────────────────────────────────────────────────────────────────────


def _build_cost_query(
    run_id: UUID,
    tenant_id: UUID,
) -> Any:
    """Build the SELECT against ``sales_agent_llm_call`` for the cost capa.

    Per spec § "Tenant isolation" + ``.claude/rules/tenant-isolation.md``,
    the WHERE clause MUST filter by ``tenant_id`` — cross-tenant leakage
    in cost reads is a security failure. The eval ``run_id`` maps to the
    canonical ``turn_id`` column (sales_agent persists one turn per
    eval invocation; the eval fixture's ``run_id`` is the agent's
    ``turn_id`` returned by ``sales_agent_entrypoint``).
    """
    # Lazy import — keeps the module loadable in environments where the
    # SQLAlchemy model registry is not yet configured (e.g. linter pass).
    from luana_core_sales_agent.observability.persistence.models.llm_call_model import (
        SalesAgentLlmCallModel,
    )

    return select(SalesAgentLlmCallModel).where(
        SalesAgentLlmCallModel.tenant_id == tenant_id,
        SalesAgentLlmCallModel.turn_id == run_id,
    )


def assert_cost_recorded(
    run_id: UUID,
    *,
    db_session: Any,
    tenant_id: UUID,
    model_pattern: str,
    max_cost_usd: Decimal,
) -> None:
    """Verify cost rows for ``run_id`` exist, sum > 0, sum ≤ budget, all match pattern.

    Reads ``sales_agent_llm_call`` filtered by ``tenant_id`` AND
    ``turn_id == run_id``. For each row:

    * ``cost_usd`` MUST be non-NULL and ≥ 0 (NULL = unknown cost path
      per T-1 cost_recorder canonicalization — caller must distinguish).
    * ``model_responded`` MUST match ``model_pattern`` (fnmatch glob —
      e.g. ``"kimi/*"`` matches ``"kimi/kimi-k2.6"``).

    The aggregate SUM is compared against ``max_cost_usd`` so the smoke
    test catches both regression-up (cost spike) and regression-to-zero
    (degraded path that produced 0-cost rows because LiteLLM did not
    return ``response_cost``).

    Args:
        run_id: Eval invocation id — maps to ``sales_agent_llm_call.turn_id``.
        db_session: SQLAlchemy ``Session`` (sync or duck-typed). Caller
            owns lifecycle (the ``visionarias_tenant_session`` fixture
            yields the session and closes it in teardown).
        tenant_id: Canonical Visionarias UUID; mandatory for tenant
            isolation.
        model_pattern: ``fnmatch`` glob pattern. Every persisted row's
            ``model_responded`` MUST match. ``"*"`` accepts any model.
        max_cost_usd: Inclusive upper bound on the sum of ``cost_usd``
            across rows. Smoke budget is typically ``Decimal("0.05")``.

    Raises:
        CostAssertionError: on any of:
            * No rows for ``(tenant_id, run_id)`` → cost recording broken.
            * Any row with ``cost_usd is None`` or ``cost_usd <= 0``
              → degraded path captured (T-1 cost_recorder regression).
            * Any row whose ``model_responded`` does not match
              ``model_pattern`` → unexpected provider used.
            * Sum cost > ``max_cost_usd`` → smoke budget exceeded.
    """
    stmt = _build_cost_query(run_id, tenant_id)
    rows = list(db_session.execute(stmt).all())

    # Unpack from Result rows tuple form (when using full ORM select +
    # .scalars()-less call, .all() yields tuple[1] entries). Duck-type:
    # accept either model instances (test fakes) or tuples of length 1.
    extracted: list[Any] = []
    for row in rows:
        if hasattr(row, "cost_usd") and hasattr(row, "model_responded"):
            extracted.append(row)
        elif isinstance(row, tuple) and len(row) >= 1:
            extracted.append(row[0])
        else:
            extracted.append(row)

    if not extracted:
        error_msg = (
            f"No se encontraron filas en sales_agent_llm_call para "
            f"tenant_id={tenant_id} turn_id={run_id}. El callback handler "
            f"no escribió rows — capa 4 (cost) rota."
        )
        raise CostAssertionError(
            error_msg,
            observed={"row_count": 0},
            expected={
                "tenant_id": str(tenant_id),
                "turn_id": str(run_id),
                "model_pattern": model_pattern,
                "max_cost_usd": str(max_cost_usd),
            },
        )

    total_cost = Decimal(0)
    for row in extracted:
        # cost_usd may be None (T-1 degraded path) — explicit fail per docstring.
        cost = row.cost_usd
        if cost is None or Decimal(cost) <= 0:
            error_msg = (
                f"Fila con cost_usd inválido (None o ≤ 0) detectada: "
                f"model={row.model_responded} cost={cost}. "
                f"T-1 degraded path — LiteLLM no proporcionó response_cost."
            )
            raise CostAssertionError(
                error_msg,
                observed={"model_responded": row.model_responded, "cost_usd": cost},
                expected={
                    "min_cost_usd_per_row": "> 0",
                    "model_pattern": model_pattern,
                },
            )

        # Pattern check via fnmatch (glob style — caller passes "kimi/*").
        if not fnmatch.fnmatchcase(row.model_responded, model_pattern):
            error_msg = (
                f"Modelo no coincide con patrón. Se esperó '{model_pattern}', se observó '{row.model_responded}'."
            )
            raise CostAssertionError(
                error_msg,
                observed=row.model_responded,
                expected=model_pattern,
            )

        total_cost += Decimal(cost)

    if total_cost > Decimal(max_cost_usd):
        error_msg = (
            f"Suma de costos excede presupuesto del smoke. "
            f"Se observó {total_cost} USD, máximo permitido {max_cost_usd} USD."
        )
        raise CostAssertionError(
            error_msg,
            observed=total_cost,
            expected={"max_cost_usd": max_cost_usd},
        )


# ──────────────────────────────────────────────────────────────────────────
# Capa 5 — Latency
# ──────────────────────────────────────────────────────────────────────────


_NUMERIC_TYPES: tuple[type, ...] = (int, float, Decimal)


def _coerce_duration_ms(value: Any) -> int:
    """Coerce a duration-like value to integer milliseconds.

    Accepts ``int``, ``float``, ``Decimal``. Other types yield 0
    (defensive — bad data in spy should never raise here).
    """
    if isinstance(value, _NUMERIC_TYPES):
        try:
            return int(value)
        except (ValueError, TypeError):
            return 0
    return 0


def _sum_spy_duration_ms(spy: _SpyLike) -> int:
    """Sum span durations from the spy, falling back through three signals.

    1. ``spy.duration_ms`` — single aggregate provided by the caller.
    2. Per-tool ``duration_ms`` keys inside ``spy.tool_calls``.
    3. Default ``0`` (no time signal — passes any threshold).

    Returns ``int`` milliseconds.
    """
    aggregate = getattr(spy, "duration_ms", None)
    if aggregate is not None and isinstance(aggregate, _NUMERIC_TYPES):
        return _coerce_duration_ms(aggregate)

    tool_calls = getattr(spy, "tool_calls", None)
    if isinstance(tool_calls, list) and tool_calls:
        spans_total = 0
        any_signal = False
        for tc in tool_calls:
            if isinstance(tc, dict) and "duration_ms" in tc:
                any_signal = True
                spans_total += _coerce_duration_ms(tc["duration_ms"])
        if any_signal:
            return spans_total

    return 0


def assert_latency(spy: _SpyLike, *, max_ms: int) -> None:
    """Verify the sum of observed spans is ≤ ``max_ms``.

    Time signals are duck-typed (see :func:`_sum_spy_duration_ms`). When
    the spy carries no time data at all, the assertion returns silently
    so callers can invoke it unconditionally — the smoke test is allowed
    to skip latency on a spy that did not capture timing.

    Args:
        spy: Object with optional ``duration_ms`` attribute or
            ``tool_calls`` items carrying ``duration_ms`` keys.
        max_ms: Inclusive upper bound on summed milliseconds.

    Raises:
        LatencyAssertionError: when the summed signal exceeds ``max_ms``.
            ``observed`` is the summed value; ``expected`` is the
            threshold.
    """
    total_ms = _sum_spy_duration_ms(spy)
    if total_ms > max_ms:
        error_msg = (
            f"Latencia observada excede el límite del smoke. Se sumó {total_ms} ms, máximo permitido {max_ms} ms."
        )
        raise LatencyAssertionError(
            error_msg,
            observed=total_ms,
            expected=max_ms,
        )


# ──────────────────────────────────────────────────────────────────────────
# Story 7 placeholder (NOT implemented in Story 1)
# ──────────────────────────────────────────────────────────────────────────


def assert_voice_fidelity(
    text: str,
    *,
    brand_voice_template: str,
) -> None:
    """Story 7 — voice fidelity grader (NOT implemented in Story 1).

    Future-proof signature so the smoke runner (T-5) can wire the call
    site without a code change later. The Story 1 smoke test MUST NOT
    invoke this function — calling it raises ``NotImplementedError``
    explicitly to fail fast if a future refactor accidentally enables
    voice fidelity before the grader lands.

    Per spec § "Out of scope" (line 277, T-4) + arch-be:

    * Story 7 introduces the LLM-judge grader against
      ``personality_profiles.system_instruction``.
    * Until then, callers MUST stub-out voice checks (or rely on
      ``assert_output`` for static markers).

    Args:
        text: Final agent response (passed through verbatim — not used).
        brand_voice_template: Compiled voice template (T-2 fixture
            ``visionarias_tenant_session["brand_voice"]``).

    Raises:
        NotImplementedError: Always. Mentions "Story 7" + "future" so
            the caller knows where the implementation lives. The smoke
            test asserts this contract via
            ``test_assert_voice_fidelity_is_placeholder``.
    """
    del text, brand_voice_template  # explicitly unused — Story 7 future scope
    error_msg = (
        "assert_voice_fidelity es un placeholder de Story 7 — el grader "
        "real (LLM judge contra personality_profiles.system_instruction) "
        "se implementará en una future story. El smoke de Story 1 NO debe "
        "invocar esta función."
    )
    raise NotImplementedError(error_msg)


# ──────────────────────────────────────────────────────────────────────────
# Public API surface
# ──────────────────────────────────────────────────────────────────────────


__all__ = [
    "CostAssertionError",
    "LatencyAssertionError",
    "LayerAssertionError",
    "OutputAssertionError",
    "ToolCallAssertionError",
    "TrajectoryAssertionError",
    "_detect_language_safe",
    "assert_cost_recorded",
    "assert_latency",
    "assert_output",
    "assert_tool_calls",
    "assert_trajectory",
    "assert_voice_fidelity",
]
