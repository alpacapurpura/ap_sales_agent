"""YAML golden loader + ``GoldenSpec`` dataclass for the sales_agent eval harness.

Per ``03-arch-be.md`` § "Golden YAML schema" + ticket T-5 deliverable 1:
loads a single YAML file produced by hand or by ``regenerate_golden.py``
into a structured ``GoldenSpec`` dataclass consumed by
``test_eval_runner_smoke.py``.

Schema (verbatim from arch-be § "Golden YAML schema"):

    id: <golden_id_str>                           # primary key for the test, e.g. "visionarias-smoke-001"
    version: 1
    schema_version: 1
    tenant_id_env: "VISIONARIAS_TENANT_ID"        # resolved by fixture
    offer_id: <UUID hardcoded — see B2 binding>
    input_message: |                              # Spanish neutro LATAM (no voseo)
      Hola, vi su publicidad sobre {{offer_name}}. ¿Cuánto cuesta y cómo es la metodología?
    expected_specialists: ["qualifier"]            # B-decision: state.next_node[0] post supervisor
    required_tools: []                            # B4: rapport stage has no required tools
    forbidden_tools:                              # B4: deduped names from STAGE_TOOL_SCOPE registry
      - send_payment_link
      - generate_payment_link
      - ...
    must_mention: ["Visionarias", "{{offer_name}}"]  # case-insensitive substrings expected in output
    language: "es"                                # ISO-639-1 prefix; assert_output normalizes "es-AR" → "es"
    max_cost_usd: 0.01                            # capa 4 budget (real LLM smoke)
    max_latency_ms: 30000                         # capa 5 threshold (p95 SLA per spec)
    metadata:
      created_at: "2026-05-05T03:30:00Z"
      regenerated_from: null                     # populated by regenerate_golden.py

Anti-duplication §0:

* This loader is purely test infrastructure (read-only YAML → dataclass).
* No mirror of any production schema — ``GoldenSpec`` is a test-only DTO.
* No mirror of YAML loading helpers — uses standard ``yaml.safe_load``.

Tenant isolation: NOT enforced here (loader is data-only). Resolution of
``tenant_id`` is the fixture's job (``visionarias_tenant_session``).

Spanish neutro LATAM (`.claude/rules/spanish-text.md`):

* Loader error messages are dev-facing diagnostics in Spanish neutro
  (no voseo) so the failure surface stays consistent with the assertion
  library. ``Faltan`` / ``inválido`` / ``no se encontró`` etc.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import structlog
import yaml

logger = structlog.get_logger()


# Required top-level keys per arch-be § "Golden YAML schema".
_REQUIRED_FIELDS: frozenset[str] = frozenset(
    {
        "id",
        "tenant_id",
        "offer_id",
        "input_message",
        "expected_specialists",
        "required_tools",
        "forbidden_tools",
        "must_mention",
        "language",
        "max_cost_usd",
        "max_latency_ms",
    },
)


class GoldenSchemaError(ValueError):
    """Raised when the YAML lacks required keys or has invalid type shapes.

    Subclass of :class:`ValueError` so callers can choose between
    catching the broad parent (legacy) or the narrow loader error
    (preferred — preserves stack-trace context).
    """


@dataclass
class GoldenSpec:
    """Structured representation of a single eval golden YAML file.

    Attributes mirror the YAML schema 1:1 + add ``source_path`` so error
    messages can name the offending file.

    Attributes:
        golden_id: Primary key for the golden (e.g. ``visionarias-smoke-001``).
        tenant_id: Tenant UUID as string. The smoke fixture resolves
            against ``VISIONARIAS_TENANT_ID`` env var; the YAML stores
            the canonical Visionarias UUID literal so a refactor of the
            env-var name does not break the test.
        offer_id: Offer UUID as string (B2: hardcoded; fail-explicit).
        input_message: Free-form user message (Spanish neutro LATAM).
        expected_specialists: Specialist names (subset / order per
            ``mode`` keyword in :func:`assert_trajectory`).
        required_tools: Tool names that MUST appear in tool_calls. Empty
            list permitted (rapport-stage smoke has no required tools).
        forbidden_tools: Tool names that MUST NOT appear in tool_calls
            (deduped from ``STAGE_TOOL_SCOPE`` registry per B4 binding).
        must_mention: Substrings (case-insensitive) expected in output.
        language: ISO-639-1 code or region-tagged form (``"es"`` / ``"es-AR"``).
        max_cost_usd: Budget cap for capa 4 (cost) — :class:`float` for
            YAML compatibility; converted to :class:`Decimal` by caller.
        max_latency_ms: Threshold for capa 5 (latency) in milliseconds.
        metadata: Free-form dict (``regenerated_from``, ``created_at``,
            ``trial_policy``, etc.). Not validated by the loader — caller
            inspects as needed.
        source_path: Filesystem location used in error messages.
    """

    golden_id: str
    tenant_id: str
    offer_id: str
    input_message: str
    expected_specialists: list[str]
    required_tools: list[str]
    forbidden_tools: list[str]
    must_mention: list[str]
    language: str
    max_cost_usd: float
    max_latency_ms: int
    metadata: dict[str, Any] = field(default_factory=dict)
    source_path: Path | None = None


def _validate_payload(payload: Any, source: Path | str) -> None:
    """Verify ``payload`` is a dict with every required key + correct types.

    Raises :class:`GoldenSchemaError` with Spanish-neutro message naming
    the offending field for fast triage.
    """
    if not isinstance(payload, dict):
        msg = f"Golden YAML invalido en {source}: el documento raiz debe ser un dict, se recibio {type(payload).__name__}."
        raise GoldenSchemaError(msg)

    missing = sorted(_REQUIRED_FIELDS - set(payload.keys()))
    if missing:
        msg = f"Golden YAML incompleto en {source}: faltan campos obligatorios {missing}."
        raise GoldenSchemaError(msg)

    # Type validation per field — defensive against YAML quirks (e.g.
    # accidental `null` for a list, scalar where a list is expected).
    for list_field in ("expected_specialists", "required_tools", "forbidden_tools", "must_mention"):
        value = payload[list_field]
        if not isinstance(value, list):
            msg = (
                f"Golden YAML invalido en {source}: el campo '{list_field}' "
                f"debe ser una lista, se recibio {type(value).__name__}."
            )
            raise GoldenSchemaError(msg)
        if any(not isinstance(item, str) for item in value):
            msg = (
                f"Golden YAML invalido en {source}: el campo '{list_field}' "
                f"debe contener solo strings; se observaron tipos no-string."
            )
            raise GoldenSchemaError(msg)

    for str_field in ("id", "tenant_id", "offer_id", "input_message", "language"):
        if not isinstance(payload[str_field], str):
            msg = (
                f"Golden YAML invalido en {source}: el campo '{str_field}' "
                f"debe ser str, se recibio {type(payload[str_field]).__name__}."
            )
            raise GoldenSchemaError(msg)

    cost = payload["max_cost_usd"]
    if not isinstance(cost, (int, float)) or isinstance(cost, bool):
        msg = f"Golden YAML invalido en {source}: 'max_cost_usd' debe ser numerico, se recibio {type(cost).__name__}."
        raise GoldenSchemaError(msg)

    latency = payload["max_latency_ms"]
    if not isinstance(latency, int) or isinstance(latency, bool):
        msg = f"Golden YAML invalido en {source}: 'max_latency_ms' debe ser int, se recibio {type(latency).__name__}."
        raise GoldenSchemaError(msg)


def load_yaml(path: Path) -> GoldenSpec:
    """Load a YAML golden file from disk and return a :class:`GoldenSpec`.

    Args:
        path: Filesystem path to the YAML file.

    Returns:
        Populated :class:`GoldenSpec`.

    Raises:
        FileNotFoundError: When ``path`` does not exist.
        GoldenSchemaError: When required keys are missing or types are
            incorrect.
        yaml.YAMLError: When YAML parsing itself fails (propagated as-is
            — caller chooses the recovery policy).

    Notes:
        Uses :func:`yaml.safe_load` per security best-practice (rejects
        arbitrary Python tags). The loader is read-only — the returned
        dataclass is mutable per Python convention but callers should
        treat it as immutable.
    """
    if not path.exists():
        msg = f"Golden YAML no se encontro en {path}. Verifica la ruta o ejecuta regenerate_golden.py."
        raise FileNotFoundError(msg)

    raw_text = path.read_text(encoding="utf-8")
    try:
        payload = yaml.safe_load(raw_text)
    except yaml.YAMLError as exc:
        logger.warning(
            "eval_golden_yaml_parse_failed",
            path=str(path),
            error=str(exc),
        )
        raise

    _validate_payload(payload, source=path)

    spec = GoldenSpec(
        golden_id=payload["id"],
        tenant_id=payload["tenant_id"],
        offer_id=payload["offer_id"],
        input_message=payload["input_message"],
        expected_specialists=list(payload["expected_specialists"]),
        required_tools=list(payload["required_tools"]),
        forbidden_tools=list(payload["forbidden_tools"]),
        must_mention=list(payload["must_mention"]),
        language=payload["language"],
        max_cost_usd=float(payload["max_cost_usd"]),
        max_latency_ms=int(payload["max_latency_ms"]),
        metadata=dict(payload.get("metadata", {}) or {}),
        source_path=path,
    )
    logger.info(
        "eval_golden_loaded",
        golden_id=spec.golden_id,
        path=str(path),
    )
    return spec


def list_goldens(directory: Path) -> list[Path]:
    """Return sorted list of ``*.yaml`` files in ``directory``.

    Sorted lexicographically so iteration is deterministic across runs
    and platforms — pytest collection order should not affect cost
    accounting in the LLM call recorder.

    Args:
        directory: Path to the goldens directory (e.g.
            ``backend/tests/agentic_evals/sales_agent/goldens/``).

    Returns:
        List of ``Path`` objects. Empty list if the directory does not
        exist or has no YAML files (defensive; caller may interpret
        as "no goldens to run" without raising).
    """
    if not directory.is_dir():
        logger.warning(
            "eval_goldens_directory_missing",
            directory=str(directory),
        )
        return []
    return sorted(directory.glob("*.yaml"))


__all__ = [
    "GoldenSchemaError",
    "GoldenSpec",
    "list_goldens",
    "load_yaml",
]
