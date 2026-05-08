"""Promueve un candidato de simulación a golden YAML verificado (Story D / T-3).

Pipeline (per spec Scenario 1 + D14):
  1. Carga artefacto JSON desde {artifact_dir}/sim_{simulation_id}.json
  2. Auto-deriva expected_*:
     - termination_reason  ← artifact.termination_reason
     - tools_invoked       ← unión de tool_calls de agent turns (transcript)
     - forbidden_tools     ← según persona_kind (D17 mapa):
       * "unqualified" → ["enroll_immediate", "send_payment_link", "confirm_appointment"]
       * "happy"/"nurture" → []
     - voice_attributes    ← keys del dict personality_profile.dimensions via
                             Story A loader (TenantContext — read-only, sin mutar)
  3. Construye GoldenMetadataModel + GoldenScenarioModel (schema v1 D6 cement)
  4. Escribe en:
       backend/tests/agentic_evals/sales_agent/goldens/
         {tenant_slug}/{persona_kind}/{golden_id}.yaml
     Idempotente: sobreescribe si existe.
     Formato YAML: pyyaml safe_dump, sort_keys=True, allow_unicode=True.
  5. --notes opcional para override freeform de Chris (D14)

Anti-duplication (`.claude/rules/anti-duplication.md`):
  - Reutiliza GoldenScenarioModel (Story D §3.1 / T-1)
  - Reutiliza Story A loader read-only (`load_eval_tenant(slug)` para personality_profile)
  - Sin duplication de PII patterns (T-2 `_pii_patterns.py` — scanner separado)

Tenant isolation:
  - Cada golden contiene datos de EXACTAMENTE UN tenant (GoldenTenantSlug Literal).
  - Integridad referencial verificada en T-4.

Exit codes:
  0 — promoción exitosa
  2 — artefacto no encontrado, persona_kind fuera de scope, o error de validación
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Final
from uuid import UUID

import structlog
import yaml

from tests.agentic_evals.sales_agent.goldens._schema import (
    GoldenMetadataModel,
    GoldenPersonaKind,
    GoldenScenarioModel,
    GoldenTurnModel,
)
from tests.fixtures.eval.tenants.loader import load_eval_tenant

logger = structlog.get_logger()

# Raíz canónica de goldens (relativo a este script en backend/scripts/)
_GOLDENS_ROOT: Final[Path] = Path(__file__).resolve().parents[1] / "tests" / "agentic_evals" / "sales_agent" / "goldens"

# D17 — mapa declarativo de herramientas prohibidas por persona_kind
_FORBIDDEN_TOOLS_BY_KIND: Final[dict[str, list[str]]] = {
    "unqualified": ["confirm_appointment", "enroll_immediate", "send_payment_link"],
    "happy": [],
    "nurture": [],
}

# Conjunto de persona_kinds en scope para Story D
_GOLDENS_SCOPE_KINDS: Final[frozenset[str]] = frozenset({"happy", "nurture", "unqualified"})


def _extract_voice_attributes(tenant_slug: str) -> list[str]:
    """Auto-extrae keys de voice attributes desde personality_profile (D14).

    Lee el dict `personality_profile.dimensions` via Story A loader (TenantContext).
    Retorna lista de keys en orden alfabético para reproducibilidad.
    NUNCA muta el perfil — operación read-only.

    Args:
        tenant_slug: Slug del tenant (Story A seed).

    Returns:
        Lista sorted de keys de dimensions. Lista vacía si no hay dimensions.
    """
    ctx = load_eval_tenant(tenant_slug)
    personality = ctx.personality_profile or {}
    if not isinstance(personality, dict):
        return []
    dimensions = personality.get("dimensions", {})
    if isinstance(dimensions, dict):
        return sorted(str(k) for k in dimensions)
    return []


def _derive_expected_tools_invoked(transcript: list[dict[str, object]]) -> list[str]:
    """Unión de tool_calls observados en todos los agent turns del transcript.

    Solo considera turns con role=="agent". Ignora customer turns.
    Retorna lista sorted sin duplicados.

    Args:
        transcript: Lista de dicts de turno (role, content, tool_calls, ...).

    Returns:
        Lista sorted de nombres de tools invocadas.
    """
    seen: set[str] = set()
    for turn in transcript:
        if turn.get("role") != "agent":
            continue
        calls = turn.get("tool_calls") or []
        if isinstance(calls, list):
            seen.update(str(c) for c in calls)
    return sorted(seen)


def _build_golden(
    artifact: dict[str, object],
    golden_id: str,
    notes: str,
    actor_profile_id: str,
) -> GoldenScenarioModel:
    """Construye GoldenScenarioModel desde artefacto de simulación.

    Auto-deriva todos los campos expected_* desde el artefacto.
    Valida persona_kind en scope (D3 — solo happy/nurture/unqualified).

    Args:
        artifact: Dict cargado desde sim_{uuid}.json.
        golden_id: Slug identificador del golden (e.g. "coach-lat-happy-001").
        notes: Nota freeform de Chris (D14). Vacío = sin override.
        actor_profile_id: ID del ActorProfile Story C (referencial T-4).

    Returns:
        GoldenScenarioModel validado (schema v1 frozen).

    Raises:
        ValueError: Si persona_kind fuera de scope D3 (adversarial/edge/negative).
        pydantic.ValidationError: Si el artefacto produce un golden inválido.
    """
    tenant_slug = str(artifact.get("tenant_archetype_slug", ""))
    persona_kind_raw = str(artifact.get("persona_kind", "happy"))

    # Validar scope — adversarial=Story I, edge/negative=loader-only
    if persona_kind_raw not in _GOLDENS_SCOPE_KINDS:
        msg = (
            f"persona_kind {persona_kind_raw!r} not in goldens scope. "
            f"adversarial → Story I; edge/negative → loader-only (sin graph). "
            f"Solo se aceptan: {sorted(_GOLDENS_SCOPE_KINDS)}"
        )
        raise ValueError(msg)
    persona_kind: GoldenPersonaKind = persona_kind_raw  # type: ignore[assignment]

    # Construir transcript validando cada turno
    transcript_raw = artifact.get("transcript", [])
    if not isinstance(transcript_raw, list):
        msg = "Artifact transcript debe ser una lista"
        raise TypeError(msg)

    transcript: list[GoldenTurnModel] = []
    for i, t in enumerate(transcript_raw):
        if not isinstance(t, dict):
            continue
        transcript.append(
            GoldenTurnModel(
                role=t.get("role", "customer"),  # type: ignore[arg-type]
                content=str(t.get("content", "")),
                turn_number=int(t.get("turn_number", i)),
                tool_calls=t.get("tool_calls"),  # type: ignore[arg-type]
                latency_ms=t.get("latency_ms"),  # type: ignore[arg-type]
            )
        )

    # Extraer costo del resumen (Decimal — sin drift de float)
    cost_summary = artifact.get("cost_summary", {})
    cost_usd = Decimal(str(cost_summary.get("total_cost_usd", "0"))) if isinstance(cost_summary, dict) else Decimal(0)

    # Resolver seed — el generador escribe "_cell_seed"; fixture tests usan "seed"
    seed_val = artifact.get("seed") or artifact.get("_cell_seed") or 0

    # Resolver generated_at desde el artefacto (si está disponible).
    # Fallback a epoch UTC para estabilidad determinística cuando el artefacto
    # no incluye timestamp (fixture tests + versiones antiguas del generador).
    generated_at_raw = artifact.get("generated_at")
    if isinstance(generated_at_raw, str):
        try:
            generated_at = datetime.fromisoformat(generated_at_raw)
        except ValueError:
            generated_at = datetime.fromtimestamp(0, tz=UTC)
    elif isinstance(generated_at_raw, datetime):
        generated_at = generated_at_raw
    else:
        generated_at = datetime.fromtimestamp(0, tz=UTC)

    metadata = GoldenMetadataModel(
        generated_from_simulation_id=UUID(str(artifact["simulation_id"])),
        generated_at=generated_at,
        curated_by="chris",
        curated_at=datetime.now(tz=UTC),
        generation_run_id=UUID(str(artifact.get("run_id", artifact["simulation_id"]))),
        seed=int(seed_val),
        cost_usd_at_generation=cost_usd,
        notes=notes,
    )

    return GoldenScenarioModel(
        id=golden_id,
        tenant_slug=tenant_slug,  # type: ignore[arg-type]
        persona_kind=persona_kind,
        actor_profile_id=actor_profile_id,
        actor_profile_schema_version=2,
        dialect_code=str(artifact.get("dialect_code", "es-419")),
        transcript=transcript,
        expected_termination_reason=str(  # type: ignore[arg-type]
            artifact.get("termination_reason", "GOAL_COMPLETION")
        ),
        expected_voice_attributes=_extract_voice_attributes(tenant_slug),
        expected_tools_invoked=_derive_expected_tools_invoked(
            transcript_raw  # type: ignore[arg-type]
        ),
        forbidden_tools=_FORBIDDEN_TOOLS_BY_KIND.get(persona_kind, []),
        expected_min_distinct_objections_handled=(5 if persona_kind == "nurture" else None),
        metadata=metadata,
    )


def _write_yaml(model: GoldenScenarioModel, path: Path) -> None:
    """Escribe golden como YAML determinístico (sobreescritura idempotente).

    Usa yaml.safe_dump con sort_keys=True y allow_unicode=True para:
    - Reproducibilidad byte-exacta en CI (sort_keys)
    - Preservar caracteres LatAm sin escape (allow_unicode)
    - Formato bloque legible (default_flow_style=False)

    Args:
        model: GoldenScenarioModel validado.
        path: Ruta destino (se crea parent si no existe).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    data = model.model_dump(mode="json")
    path.write_text(
        yaml.safe_dump(data, sort_keys=True, default_flow_style=False, allow_unicode=True),
        encoding="utf-8",
    )


def main() -> int:
    """Punto de entrada principal para CLI.

    Returns:
        0 — golden escrito exitosamente.
        2 — artefacto no encontrado, persona_kind inválido, o error de validación.
    """
    parser = argparse.ArgumentParser(description="Promueve simulación candidata a golden YAML verificado (Story D)")
    parser.add_argument(
        "--simulation-id",
        type=str,
        required=True,
        help="UUID de la simulación (nombre del artefacto: sim_{uuid}.json).",
    )
    parser.add_argument(
        "--golden-id",
        type=str,
        required=True,
        help="Slug identificador del golden (e.g. 'coach-lat-happy-001').",
    )
    parser.add_argument(
        "--artifact-dir",
        type=Path,
        required=True,
        help="Directorio donde están los artefactos sim_*.json.",
    )
    parser.add_argument(
        "--actor-profile-id",
        type=str,
        required=True,
        help="ID del ActorProfile Story C (e.g. 'lead-frio-impaciente-pe').",
    )
    parser.add_argument(
        "--notes",
        type=str,
        default="",
        help="Nota freeform de Chris para override (D14). Default: sin nota.",
    )
    args = parser.parse_args()

    # Localizar artefacto
    artifact_path = args.artifact_dir / f"sim_{args.simulation_id}.json"
    if not artifact_path.exists():
        sys.stderr.write(f"ERROR: artefacto no encontrado: {artifact_path}\n")
        return 2

    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))

    try:
        model = _build_golden(
            artifact,
            args.golden_id,
            args.notes,
            args.actor_profile_id,
        )
    except (ValueError, Exception) as exc:  # noqa: BLE001
        sys.stderr.write(f"ERROR: no se pudo construir golden: {exc}\n")
        return 2

    out_path = _GOLDENS_ROOT / model.tenant_slug / model.persona_kind / f"{args.golden_id}.yaml"
    _write_yaml(model, out_path)

    logger.info(
        "promote_golden.written",
        golden_id=args.golden_id,
        tenant_slug=model.tenant_slug,
        persona_kind=model.persona_kind,
        path=str(out_path),
    )
    sys.stdout.write(f"Escrito: {out_path}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
