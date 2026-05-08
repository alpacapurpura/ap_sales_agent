"""Genera transcripciones candidatas para goldens de evaluación (Story D).

Pipeline (per spec Scenario 1):
  1. Para cada celda (tenant_slug × persona_kind × run_n) en la matriz 5×3×5 = 75:
     - Carga ActorProfile via Story C `load_actor_profile_for_tenant`
     - Calcula max_turns via Story C `get_max_turns_for_persona_kind`
     - Programa coroutine run_simulation(...)
  2. Ejecuta 75 simulaciones en paralelo (asyncio.gather + Semaphore(10))
  3. Persiste artefactos JSON en {output_dir}/sim_{simulation_id}.json
  4. Emite tabla Markdown preview en {output_dir}/preview.md
     (renderable en IDE, terminal-friendly per spec D12/Q3)
  5. Imprime resumen: costo total, conteos por celda, sugerencias de promoción

Presupuesto: ~$5.40 estimado para 75 celdas. Límite $8 (--cost-budget-usd).
Pre-flight aborta si estimado > límite.

Anti-duplication (`.claude/rules/anti-duplication.md`):
  - Consume Story B `run_simulation` (7-name public API, H9 frozen).
  - Consume Story C `load_actor_profile_for_tenant` (internal pin D-AG-2).
  - Semáforo local (no quota global cross-suite).

Aislamiento por celda (tessl__graceful-degradation Rule 5):
  - Una celda con excepción → log + skip + continuar.
  - Suite continúa. Exit 0 si ≥1 éxito, exit 1 si todas fallaron.
  - Exit 2 SOLO para pre-flight de presupuesto.

Tenant isolation:
  - Cada simulación invoca run_simulation con tenant_archetype_slug explícito.
  - El script nunca accede DB directamente (sin queries cross-tenant).

Spanish neutro (`.claude/rules/spanish-text.md`):
  - Mensajes structlog + CLI + comentarios en español neutro LatAm.
  - (Personas YAML puede tener voseo si dialect_code=es-AR — responsabilidad Story C.)

Exit codes:
  0 — éxito (todas las celdas o ≥1 con 0 fallos)
  1 — éxito parcial (≥1 celda exitosa con fallos)
  2 — error de presupuesto (pre-flight abortó) o sin celdas
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import json
import sys
import uuid
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING, Final

import structlog

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

# Consumo API pública Story B (H9 7 nombres frozen)
from tests.agentic_evals.sales_agent.simulator import (
    ActorProfile,
    SimulationResult,
    run_simulation,
)

# Consumo interno Story C (D-AG-2 pin explícito para consumers downstream)
from tests.agentic_evals.sales_agent.simulator._internal.personas_loader import (
    PersonaKind,
    get_max_turns_for_persona_kind,
    load_actor_profile_for_tenant,
)

logger = structlog.get_logger()

# ─────────────────────────────────────────────────────────────────────────────
# Constantes de la matriz
# ─────────────────────────────────────────────────────────────────────────────

_TENANT_SLUGS: Final[tuple[str, ...]] = (
    "tenant_coach_lat",
    "tenant_medicina_estetica",
    "tenant_clinica_dental",
    "tenant_agencia_growth_video",
    "tenant_agencia_automatizacion_ia",
)
_PERSONA_KINDS: Final[tuple[PersonaKind, ...]] = ("happy", "nurture", "unqualified")
_DEFAULT_RUNS_PER_CELL: Final[int] = 5
_DEFAULT_CONCURRENCY: Final[int] = 10
_DEFAULT_COST_BUDGET_USD: Final[Decimal] = Decimal("8.00")
_COST_PER_CELL_USD: Final[Decimal] = Decimal("0.072")


# ─────────────────────────────────────────────────────────────────────────────
# Dataclasses de resultado por celda
# ─────────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class CellKey:
    """Identificador único de una celda en la matriz de generación."""

    tenant_slug: str
    persona_kind: PersonaKind
    run_n: int


@dataclass(frozen=True)
class CellResult:
    """Resultado de una celda exitosa."""

    key: CellKey
    simulation_id: str  # UUID como str
    artifact_path: Path
    total_turns: int
    termination_reason: str
    cost_usd: Decimal
    transcript_preview: str  # últimos 2 turns, max 120 chars


# ─────────────────────────────────────────────────────────────────────────────
# Funciones públicas usadas por tests
# ─────────────────────────────────────────────────────────────────────────────


def _build_matrix(
    runs_per_cell: int,
    tenant_filter: str | None,
    persona_kind_filter: PersonaKind | None,
) -> list[CellKey]:
    """Construye la lista de celdas según filtros opcionales.

    Args:
        runs_per_cell: Número de runs por celda (0-indexed).
        tenant_filter: Si se especifica, solo incluye ese tenant.
        persona_kind_filter: Si se especifica, solo incluye ese persona_kind.

    Returns:
        Lista ordenada de CellKey para ejecutar.
    """
    cells: list[CellKey] = []
    for tenant in _TENANT_SLUGS:
        if tenant_filter and tenant != tenant_filter:
            continue
        for kind in _PERSONA_KINDS:
            if persona_kind_filter and kind != persona_kind_filter:
                continue
            for run_n in range(runs_per_cell):
                cells.append(CellKey(tenant_slug=tenant, persona_kind=kind, run_n=run_n))
    return cells


def _compute_seed(cell: CellKey, seed_base: int) -> int:
    """Calcula seed determinístico por celda (D8 — reproducibilidad).

    Usa hash del tuple (tenant_slug, persona_kind, run_n) módulo 10_000
    para dispersión uniforme dentro del espacio de seeds.

    Args:
        cell: Identificador de celda.
        seed_base: Seed base del run (--seed-base flag).

    Returns:
        Seed entero determinístico.
    """
    return seed_base + hash((cell.tenant_slug, cell.persona_kind, cell.run_n)) % 10_000


def _build_parser() -> argparse.ArgumentParser:
    """Construye el parser de argumentos CLI.

    Expuesto como función para facilitar tests de argparse.
    """
    parser = argparse.ArgumentParser(description="Genera candidatos golden via simulador dual-LLM (Story D)")
    parser.add_argument(
        "--runs-per-cell",
        type=int,
        default=_DEFAULT_RUNS_PER_CELL,
        help="Número de runs por celda (tenant × persona_kind). Default: 5.",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=_DEFAULT_CONCURRENCY,
        help="Máximo de simulaciones concurrentes (Semaphore). Default: 10.",
    )
    parser.add_argument(
        "--cost-budget-usd",
        type=Decimal,
        default=_DEFAULT_COST_BUDGET_USD,
        help="Límite de costo estimado en USD. Aborta si se excede. Default: 8.00.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directorio de salida para artefactos JSON + preview Markdown.",
    )
    parser.add_argument(
        "--run-id",
        type=str,
        default=str(uuid.uuid4()),
        help="Identificador del run (UUID). Default: UUID4 generado.",
    )
    parser.add_argument(
        "--seed-base",
        type=int,
        default=42,
        help="Seed base para reproducibilidad (D8). Default: 42.",
    )
    parser.add_argument(
        "--tenant",
        type=str,
        default=None,
        choices=[*_TENANT_SLUGS, None],  # type: ignore[list-item]
        help="Filtrar por tenant slug (opcional). Sin filtro = todos los tenants.",
    )
    parser.add_argument(
        "--persona-kind",
        type=str,
        default=None,
        choices=[*_PERSONA_KINDS, None],  # type: ignore[list-item]
        help="Filtrar por persona_kind (opcional). Sin filtro = happy/nurture/unqualified.",
    )
    return parser


# ─────────────────────────────────────────────────────────────────────────────
# Ejecución de una celda (con aislamiento por celda — Rule 5)
# ─────────────────────────────────────────────────────────────────────────────


async def _run_one_cell(
    cell: CellKey,
    semaphore: asyncio.Semaphore,
    output_dir: Path,
    run_id: str,
    seed_base: int,
    db_session: Session | None = None,
) -> CellResult:
    """Ejecuta una simulación de celda con aislamiento de errores.

    Implementa tessl__graceful-degradation Rule 5: error de celda individual
    no detiene la suite. El llamador usa asyncio.gather(return_exceptions=True)
    y maneja BaseException en cada resultado.

    Args:
        cell: Identificador de la celda a ejecutar.
        semaphore: Semáforo para limitar concurrencia.
        output_dir: Directorio de salida para artefactos.
        run_id: Identificador del run padre (UUID válido o string arbitrario
            — convertido a UUID5 determinístico via `_run_id_as_uuid`).
        seed_base: Seed base para reproducibilidad.
        db_session: SQLAlchemy sync Session para inyección en run_simulation.
            Requerido para que agent_bridge resuelva la sesión correctamente
            (D8/Bug2: SessionUnavailable si None).

    Returns:
        CellResult con resultado de la simulación.

    Raises:
        Exception: Re-lanza cualquier excepción después de loguear
            (el caller con return_exceptions=True la captura).
    """
    async with semaphore:
        actor: ActorProfile = load_actor_profile_for_tenant(cell.tenant_slug, persona_kind=cell.persona_kind)
        max_turns = get_max_turns_for_persona_kind(cell.persona_kind)
        seed = _compute_seed(cell, seed_base)

        # D8/D-A-15: run_id determinístico via UUID5 preserva simulation_id
        # estable entre ejecuciones con mismos parámetros.
        effective_run_id = _run_id_as_uuid(run_id)

        try:
            result: SimulationResult = await run_simulation(
                tenant_archetype_slug=cell.tenant_slug,
                actor_profile=actor,
                max_turns=max_turns,
                trial_n=cell.run_n,
                run_id=effective_run_id,
                db_session=db_session,
            )
        except Exception as exc:  # noqa: BLE001 — aislamiento por celda (Rule 5)
            logger.warning(
                "generate_goldens.cell_failed",
                tenant_slug=cell.tenant_slug,
                persona_kind=cell.persona_kind,
                run_n=cell.run_n,
                error_class=type(exc).__name__,
                error=str(exc),
            )
            raise

        # Persistir artefacto JSON para que promote_golden.py lo lea
        artifact_path = output_dir / f"sim_{result.simulation_id}.json"
        artifact_data = result.model_dump(mode="json")
        # Agregar metadata de celda para trazabilidad
        artifact_data["_cell_tenant_slug"] = cell.tenant_slug
        artifact_data["_cell_persona_kind"] = cell.persona_kind
        artifact_data["_cell_run_n"] = cell.run_n
        artifact_data["_cell_seed"] = seed
        artifact_path.write_text(
            json.dumps(artifact_data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        # Preview de últimos 2 turns (truncado)
        last_turns = result.transcript[-2:] if len(result.transcript) >= 2 else result.transcript
        preview = " | ".join(f"{t.role}: {t.content[:80]}{'...' if len(t.content) > 80 else ''}" for t in last_turns)

        return CellResult(
            key=cell,
            simulation_id=str(result.simulation_id),
            artifact_path=artifact_path,
            total_turns=result.total_turns,
            termination_reason=result.termination_reason.value,
            cost_usd=Decimal(str(result.cost_summary.total_cost_usd)),
            transcript_preview=preview,
        )


def _is_valid_uuid(value: str) -> bool:
    """Valida que un string sea un UUID válido."""
    try:
        uuid.UUID(value)
        return True
    except (ValueError, AttributeError):
        return False


def _run_id_as_uuid(run_id: str) -> uuid.UUID:
    """Convierte run_id a UUID, derivando UUID5 determinístico si no es UUID válido.

    D8/D-A-15: el run_id debe producir el mismo UUID5 para simulation_id
    en cada ejecución con los mismos parámetros. Si run_id es un string
    arbitrario (ej. "repro-test-run"), lo convierte a UUID5 estable.

    Args:
        run_id: String que puede ser UUID válido o identificador arbitrario.

    Returns:
        UUID determinístico para usar como run_id en run_simulation.
    """
    if _is_valid_uuid(run_id):
        return uuid.UUID(run_id)
    # Derivar UUID5 desde el string para preservar determinismo D8
    return uuid.uuid5(uuid.NAMESPACE_DNS, run_id)


# ─────────────────────────────────────────────────────────────────────────────
# Generación de Markdown preview (D12 cement, Q3 ratificado)
# ─────────────────────────────────────────────────────────────────────────────


def _emit_preview_markdown(results: list[CellResult], preview_path: Path, run_id: str) -> None:
    """Genera tabla Markdown renderable en IDE (D12 — Q3 ratificado Markdown no HTML).

    Formato: agrupado por celda, tabla terminal-friendly, rutas de artefacto
    para inspección detallada. El pipeline de preview es parallel-safe
    (sin estado compartido entre celdas).

    Args:
        results: Lista de CellResult exitosos.
        preview_path: Ruta donde escribir el archivo Markdown.
        run_id: Identificador del run (para el encabezado).
    """
    lines: list[str] = [
        f"# Golden candidate preview — run_id={run_id}",
        "",
        f"Total candidates: {len(results)}",
        "",
        "## Summary by cell",
        "",
        "| Cell | Sim ID (short) | Turns | Termination | Cost USD | Preview |",
        "|---|---|---|---|---|---|",
    ]

    for r in sorted(results, key=lambda x: (x.key.tenant_slug, x.key.persona_kind, x.key.run_n)):
        cell_label = f"{r.key.tenant_slug} / {r.key.persona_kind} / run{r.key.run_n}"
        sid_short = r.simulation_id[:8]
        # Escapar | para celdas de tabla Markdown + truncar a 120 chars
        preview_safe = r.transcript_preview.replace("|", "\\|").replace("\n", " ")[:120]
        lines.append(
            f"| {cell_label} | `{sid_short}` | {r.total_turns} | "
            f"{r.termination_reason} | ${r.cost_usd:.4f} | {preview_safe} |"
        )

    lines.extend(["", "## Promotion command template", ""])
    lines.append("```bash")
    lines.append("# For each candidate Chris selects as winner:")
    lines.append("python backend/scripts/promote_golden.py --simulation-id <sim_uuid> --golden-id <slug>")
    lines.append("```")
    lines.append("")
    lines.append("## Artifact paths (full transcripts)")
    lines.append("")

    for r in sorted(results, key=lambda x: (x.key.tenant_slug, x.key.persona_kind, x.key.run_n)):
        try:
            rel = r.artifact_path.relative_to(preview_path.parent)
        except ValueError:
            rel = r.artifact_path
        lines.append(f"- `{r.key.tenant_slug}/{r.key.persona_kind}/run{r.key.run_n}` → [`{rel}`](./{rel})")

    preview_path.write_text("\n".join(lines), encoding="utf-8")


# ─────────────────────────────────────────────────────────────────────────────
# Punto de entrada async
# ─────────────────────────────────────────────────────────────────────────────


async def _main_async(
    runs_per_cell: int,
    concurrency: int,
    cost_budget_usd: Decimal,
    output_dir: Path,
    run_id: str,
    seed_base: int,
    tenant_filter: str | None = None,
    persona_kind_filter: PersonaKind | None = None,
) -> int:
    """Punto de entrada async principal. Retorna exit code.

    Args:
        runs_per_cell: Runs por celda.
        concurrency: Máximo de simulaciones concurrentes.
        cost_budget_usd: Límite de costo estimado.
        output_dir: Directorio de salida.
        run_id: Identificador del run.
        seed_base: Seed base.
        tenant_filter: Filtro opcional de tenant.
        persona_kind_filter: Filtro opcional de persona_kind.

    Returns:
        0 — éxito (sin fallos)
        1 — éxito parcial (con ≥1 fallo)
        2 — pre-flight abortado (presupuesto excedido o sin celdas)
    """
    cells = _build_matrix(
        runs_per_cell=runs_per_cell,
        tenant_filter=tenant_filter,
        persona_kind_filter=persona_kind_filter,
    )

    if not cells:
        logger.error(
            "generate_goldens.no_cells",
            tenant_filter=tenant_filter,
            persona_kind_filter=persona_kind_filter,
        )
        sys.stderr.write("ERROR: Sin celdas para ejecutar. Verifica --tenant y --persona-kind.\n")
        return 2

    # Pre-flight de presupuesto (D-A-6 — strict abort)
    expected_cost = Decimal(str(len(cells))) * _COST_PER_CELL_USD
    if expected_cost > cost_budget_usd:
        logger.error(
            "generate_goldens.budget_exceeded_preflight",
            estimated_cost_usd=str(expected_cost),
            budget_usd=str(cost_budget_usd),
            cells=len(cells),
        )
        sys.stderr.write(
            f"ERROR: costo estimado ${expected_cost} excede el límite "
            f"${cost_budget_usd}. "
            f"Reduce --runs-per-cell o incrementa --cost-budget-usd.\n"
        )
        return 2

    output_dir.mkdir(parents=True, exist_ok=True)
    semaphore = asyncio.Semaphore(concurrency)

    logger.info(
        "generate_goldens.start",
        run_id=run_id,
        cells=len(cells),
        concurrency=concurrency,
        estimated_cost_usd=str(expected_cost),
    )

    # Bug 2 fix: inyectar SQLAlchemy session en cada celda para que
    # agent_bridge._resolve_session_for_simulation no retorne None.
    # Se importa lazily para no forzar conexión DB cuando se skippe.
    db_session: Session | None = None
    try:
        from src.core.database import SessionLocal  # noqa: PLC0415 — lazy import (no DB at module-level)

        _s = SessionLocal()
        # Probe de conexión — si Postgres no está disponible, log y continuar sin sesión
        import sqlalchemy as _sa  # noqa: PLC0415

        _s.execute(_sa.text("SELECT 1"))
        db_session = _s
        logger.info("generate_goldens.db_session_acquired")
    except Exception as _db_exc:  # noqa: BLE001 — graceful degradation: sin DB = sin cost summary
        logger.warning(
            "generate_goldens.db_session_unavailable",
            error_class=type(_db_exc).__name__,
            error=str(_db_exc),
            hint="Simulaciones continuarán sin DB session — agent_bridge terminará con SessionUnavailable",
        )

    # Crear coroutines para todas las celdas
    coros = [_run_one_cell(cell, semaphore, output_dir, run_id, seed_base, db_session) for cell in cells]

    # Ejecutar con return_exceptions=True para aislamiento por celda (Rule 5)
    gathered = await asyncio.gather(*coros, return_exceptions=True)

    # Cerrar sesión DB después de que todas las celdas completaron
    if db_session is not None:
        with contextlib.suppress(Exception):
            db_session.close()

    results: list[CellResult] = []
    failures: list[CellKey] = []
    for cell, outcome in zip(cells, gathered, strict=True):
        if isinstance(outcome, BaseException):
            failures.append(cell)
        else:
            results.append(outcome)

    # Generar Markdown preview de candidatos exitosos
    preview_path = output_dir / "preview.md"
    if results:
        _emit_preview_markdown(results, preview_path, run_id)

    total_cost = sum((r.cost_usd for r in results), start=Decimal(0))
    logger.info(
        "generate_goldens.completed",
        run_id=run_id,
        success=len(results),
        failures=len(failures),
        total_cost_usd=str(total_cost),
        preview_path=str(preview_path) if results else "N/A",
    )

    sys.stdout.write(
        f"\nGenerados {len(results)} candidatos ({len(failures)} fallos).\nCosto total: ${total_cost:.4f}\n"
    )
    if results:
        sys.stdout.write(f"Preview: {preview_path}\n")

    if not results:
        return 1  # Todas las celdas fallaron
    return 0 if not failures else 1


# ─────────────────────────────────────────────────────────────────────────────
# Punto de entrada CLI
# ─────────────────────────────────────────────────────────────────────────────


def main() -> int:
    """Punto de entrada principal para CLI."""
    parser = _build_parser()
    args = parser.parse_args()
    return asyncio.run(
        _main_async(
            runs_per_cell=args.runs_per_cell,
            concurrency=args.concurrency,
            cost_budget_usd=args.cost_budget_usd,
            output_dir=args.output_dir,
            run_id=args.run_id,
            seed_base=args.seed_base,
            tenant_filter=args.tenant,
            persona_kind_filter=args.persona_kind,
        )
    )


if __name__ == "__main__":
    sys.exit(main())
