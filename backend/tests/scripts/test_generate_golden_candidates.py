"""Tests para generate_golden_candidates.py (Story D / T-3).

Suite de tests unitarios para el script de generación de candidatos goldens.
Los tests de run_simulation real están gateados con --run-evals.

Coverage:
    - Parsing argparse con defaults
    - Forma de la matriz 5x3xN
    - Filtros por tenant y persona_kind
    - Pre-flight de presupuesto (exit 2 si se excede)
    - Markdown preview determinístico
    - Aislamiento por celda (1 fallo no detiene la suite)
    - Filtro single-cell para regeneración aislada
    - Reproducibilidad smoke (gateado --run-evals)
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import uuid
from decimal import Decimal
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Ajuste sys.path para importar scripts/ como módulos
_BACKEND_ROOT = Path(__file__).resolve().parents[2]  # backend/
sys.path.insert(0, str(_BACKEND_ROOT / "scripts"))

import generate_golden_candidates as _gen


# ─────────────────────────────────────────────────────────────────────────────
# Helpers de fixtures
# ─────────────────────────────────────────────────────────────────────────────


def _make_mock_simulation_result(
    tenant_slug: str = "tenant_coach_lat",
    persona_kind: str = "happy",
    termination_reason: str = "GOAL_COMPLETION",
    n_turns: int = 4,
) -> MagicMock:
    """Factory — retorna un SimulationResult mock mínimo y válido."""
    sim_id = uuid.uuid4()
    run_id = uuid.uuid4()

    turn = MagicMock()
    turn.role = "customer"
    turn.content = "Hola, me interesa tu servicio"

    agent_turn = MagicMock()
    agent_turn.role = "agent"
    agent_turn.content = "Con gusto te ayudo, ¿qué necesitas?"

    result = MagicMock()
    result.simulation_id = sim_id
    result.run_id = run_id
    result.archetype_slug = tenant_slug
    result.actor_profile_id = f"perfil-{persona_kind}"
    result.transcript = [turn, agent_turn] * (n_turns // 2)
    result.total_turns = n_turns
    result.termination_reason = MagicMock()
    result.termination_reason.value = termination_reason

    cost_summary = MagicMock()
    cost_summary.total_cost_usd = Decimal("0.072")
    result.cost_summary = cost_summary

    # model_dump para escritura JSON
    result.model_dump.return_value = {
        "simulation_id": str(sim_id),
        "run_id": str(run_id),
        "archetype_slug": tenant_slug,
        "actor_profile_id": f"perfil-{persona_kind}",
        "transcript": [
            {"role": "customer", "content": "Hola", "turn_number": 0, "metadata": {}},
            {"role": "agent", "content": "Con gusto", "turn_number": 1, "metadata": {}},
        ],
        "termination_reason": termination_reason,
        "total_turns": n_turns,
        "cost_summary": {"total_cost_usd": "0.072"},
        "schema_version": 1,
    }
    return result


def _make_actor_profile_mock(tenant_slug: str = "tenant_coach_lat", persona_kind: str = "happy") -> MagicMock:
    """Factory — retorna un ActorProfile mock mínimo."""
    profile = MagicMock()
    profile.id = f"perfil-{persona_kind}-{tenant_slug[:5]}"
    profile.persona_kind = persona_kind
    return profile


# ─────────────────────────────────────────────────────────────────────────────
# test_argparse_defaults_validate
# ─────────────────────────────────────────────────────────────────────────────


class TestArgparseDefaults:
    """Valida que el parser tenga los defaults correctos por contrato."""

    def test_defaults_runs_per_cell(self) -> None:
        """--runs-per-cell default debe ser 5."""
        parser = _gen._build_parser()
        args = parser.parse_args(["--output-dir", "/tmp/test_out"])
        assert args.runs_per_cell == 5

    def test_defaults_concurrency(self) -> None:
        """--concurrency default debe ser 10."""
        parser = _gen._build_parser()
        args = parser.parse_args(["--output-dir", "/tmp/test_out"])
        assert args.concurrency == 10

    def test_defaults_cost_budget_usd(self) -> None:
        """--cost-budget-usd default debe ser Decimal('8.00')."""
        parser = _gen._build_parser()
        args = parser.parse_args(["--output-dir", "/tmp/test_out"])
        assert args.cost_budget_usd == Decimal("8.00")

    def test_defaults_seed_base(self) -> None:
        """--seed-base default debe ser 42."""
        parser = _gen._build_parser()
        args = parser.parse_args(["--output-dir", "/tmp/test_out"])
        assert args.seed_base == 42

    def test_defaults_run_id_is_uuid(self) -> None:
        """--run-id default debe ser UUID4 válido."""
        parser = _gen._build_parser()
        args = parser.parse_args(["--output-dir", "/tmp/test_out"])
        uuid.UUID(args.run_id)  # raises si no es UUID válido

    def test_defaults_filters_none(self) -> None:
        """--tenant y --persona-kind default deben ser None (sin filtro)."""
        parser = _gen._build_parser()
        args = parser.parse_args(["--output-dir", "/tmp/test_out"])
        assert args.tenant is None
        assert args.persona_kind is None

    def test_output_dir_required(self) -> None:
        """--output-dir es obligatorio."""
        parser = _gen._build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([])


# ─────────────────────────────────────────────────────────────────────────────
# test_matrix_shape_5x3x5_default
# ─────────────────────────────────────────────────────────────────────────────


class TestMatrixShape:
    """Valida forma correcta de la matriz de celdas."""

    def test_default_matrix_is_75_cells(self) -> None:
        """5 tenants x 3 persona_kinds x 5 runs = 75 celdas."""
        cells = _gen._build_matrix(
            runs_per_cell=5,
            tenant_filter=None,
            persona_kind_filter=None,
        )
        assert len(cells) == 75

    def test_matrix_covers_all_tenants(self) -> None:
        """Todos los 5 tenant slugs deben aparecer en la matriz."""
        cells = _gen._build_matrix(runs_per_cell=1, tenant_filter=None, persona_kind_filter=None)
        slugs_in_matrix = {c.tenant_slug for c in cells}
        expected = set(_gen._TENANT_SLUGS)
        assert slugs_in_matrix == expected

    def test_matrix_covers_all_persona_kinds(self) -> None:
        """Los 3 persona_kinds (happy/nurture/unqualified) deben aparecer."""
        cells = _gen._build_matrix(runs_per_cell=1, tenant_filter=None, persona_kind_filter=None)
        kinds_in_matrix = {c.persona_kind for c in cells}
        assert kinds_in_matrix == {"happy", "nurture", "unqualified"}

    def test_matrix_run_n_range(self) -> None:
        """run_n debe ir de 0 a (runs_per_cell - 1)."""
        cells = _gen._build_matrix(runs_per_cell=3, tenant_filter=None, persona_kind_filter=None)
        # filtrar por un tenant+kind específico para verificar secuencia
        subset = [c for c in cells if c.tenant_slug == "tenant_coach_lat" and c.persona_kind == "happy"]
        assert sorted(c.run_n for c in subset) == [0, 1, 2]

    def test_matrix_with_custom_runs_per_cell(self) -> None:
        """Runs per cell 1 → 5x3x1 = 15 celdas."""
        cells = _gen._build_matrix(runs_per_cell=1, tenant_filter=None, persona_kind_filter=None)
        assert len(cells) == 15


# ─────────────────────────────────────────────────────────────────────────────
# test_matrix_filter_by_tenant_and_persona_kind
# ─────────────────────────────────────────────────────────────────────────────


class TestMatrixFilter:
    """Valida filtros --tenant y --persona-kind."""

    def test_filter_by_tenant_only(self) -> None:
        """Filtro --tenant → solo celdas de ese tenant."""
        cells = _gen._build_matrix(
            runs_per_cell=5,
            tenant_filter="tenant_coach_lat",
            persona_kind_filter=None,
        )
        assert all(c.tenant_slug == "tenant_coach_lat" for c in cells)
        # 3 persona_kinds x 5 runs = 15 celdas
        assert len(cells) == 15

    def test_filter_by_persona_kind_only(self) -> None:
        """Filtro --persona-kind → solo celdas de ese kind."""
        cells = _gen._build_matrix(
            runs_per_cell=5,
            tenant_filter=None,
            persona_kind_filter="happy",
        )
        assert all(c.persona_kind == "happy" for c in cells)
        # 5 tenants x 5 runs = 25 celdas
        assert len(cells) == 25

    def test_filter_by_both_tenant_and_persona_kind(self) -> None:
        """Filtro combinado tenant + persona_kind → celdas mínimas."""
        cells = _gen._build_matrix(
            runs_per_cell=5,
            tenant_filter="tenant_coach_lat",
            persona_kind_filter="happy",
        )
        assert all(c.tenant_slug == "tenant_coach_lat" for c in cells)
        assert all(c.persona_kind == "happy" for c in cells)
        # 1 tenant x 1 kind x 5 runs = 5 celdas
        assert len(cells) == 5

    def test_filter_empty_if_nonexistent_tenant(self) -> None:
        """Filtro con tenant inexistente → lista vacía."""
        cells = _gen._build_matrix(
            runs_per_cell=5,
            tenant_filter="tenant_inexistente",
            persona_kind_filter=None,
        )
        assert cells == []


# ─────────────────────────────────────────────────────────────────────────────
# test_cost_budget_preflight_strict_abort
# ─────────────────────────────────────────────────────────────────────────────


class TestCostBudgetPreflight:
    """Valida el pre-flight de presupuesto (exit 2 si se excede)."""

    def test_preflight_aborts_when_estimated_exceeds_budget(self, tmp_path: Path) -> None:
        """Matrix de 75 celdas x $0.072 = $5.40 < budget $8.00 OK. Budget $3.00 → exit 2."""
        exit_code = asyncio.run(
            _gen._main_async(
                runs_per_cell=5,
                concurrency=1,
                cost_budget_usd=Decimal("3.00"),  # $5.40 > $3.00 → abort
                output_dir=tmp_path,
                run_id="test-run-id",
                seed_base=42,
                tenant_filter=None,
                persona_kind_filter=None,
            )
        )
        assert exit_code == 2

    def test_preflight_passes_when_within_budget(self, tmp_path: Path) -> None:
        """Budget $8 con células mock → pre-flight OK, continue."""
        mock_actor = _make_actor_profile_mock()
        mock_result = _make_mock_simulation_result()

        with (
            patch.object(_gen, "load_actor_profile_for_tenant", return_value=mock_actor),
            patch.object(_gen, "get_max_turns_for_persona_kind", return_value=10),
            patch.object(_gen, "run_simulation", new_callable=AsyncMock, return_value=mock_result),
        ):
            # 1 celda x $0.072 = $0.072 << $8.00 → OK
            exit_code = asyncio.run(
                _gen._main_async(
                    runs_per_cell=1,
                    concurrency=1,
                    cost_budget_usd=Decimal("8.00"),
                    output_dir=tmp_path,
                    run_id="test-run-id",
                    seed_base=42,
                    tenant_filter="tenant_coach_lat",
                    persona_kind_filter="happy",
                )
            )
        # Puede ser 0 (éxito) o 1 (errores parciales), nunca 2
        assert exit_code != 2

    def test_estimated_cost_calculation(self) -> None:
        """Fórmula: n_cells x Decimal('0.072')."""
        cells = _gen._build_matrix(runs_per_cell=5, tenant_filter=None, persona_kind_filter=None)
        expected = Decimal(str(len(cells))) * Decimal("0.072")
        assert expected == Decimal("5.400")  # 75 x 0.072

    def test_preflight_exit_code_is_2_not_1(self, tmp_path: Path) -> None:
        """Exit code de presupuesto excedido es 2, no 1 (fallo = 1)."""
        exit_code = asyncio.run(
            _gen._main_async(
                runs_per_cell=100,  # 1500 celdas x $0.072 >> $8
                concurrency=1,
                cost_budget_usd=Decimal("1.00"),
                output_dir=tmp_path,
                run_id="test-run-id",
                seed_base=42,
            )
        )
        assert exit_code == 2


# ─────────────────────────────────────────────────────────────────────────────
# test_emit_preview_markdown_deterministic_output
# ─────────────────────────────────────────────────────────────────────────────


class TestEmitPreviewMarkdown:
    """Valida generación de Markdown preview determinístico."""

    def _make_cell_result(
        self,
        tenant_slug: str = "tenant_coach_lat",
        persona_kind: str = "happy",
        run_n: int = 0,
        sim_id: str | None = None,
    ) -> _gen.CellResult:
        """Factory para CellResult con datos mínimos."""
        return _gen.CellResult(
            key=_gen.CellKey(tenant_slug=tenant_slug, persona_kind=persona_kind, run_n=run_n),
            simulation_id=sim_id or str(uuid.uuid4()),
            artifact_path=Path(f"/tmp/{sim_id or 'test'}.json"),
            total_turns=4,
            termination_reason="GOAL_COMPLETION",
            cost_usd=Decimal("0.072"),
            transcript_preview="customer: Hola | agent: Con gusto",
        )

    def test_preview_writes_markdown_file(self, tmp_path: Path) -> None:
        """Preview debe escribir archivo .md en la ruta indicada."""
        results = [self._make_cell_result()]
        preview_path = tmp_path / "preview.md"
        _gen._emit_preview_markdown(results, preview_path, run_id="run-test-001")
        assert preview_path.exists()

    def test_preview_contains_run_id_header(self, tmp_path: Path) -> None:
        """Markdown debe incluir run_id en el encabezado."""
        results = [self._make_cell_result()]
        preview_path = tmp_path / "preview.md"
        _gen._emit_preview_markdown(results, preview_path, run_id="run-test-abc123")
        content = preview_path.read_text(encoding="utf-8")
        assert "run-test-abc123" in content

    def test_preview_contains_table_header(self, tmp_path: Path) -> None:
        """Markdown debe incluir encabezado de tabla."""
        results = [self._make_cell_result()]
        preview_path = tmp_path / "preview.md"
        _gen._emit_preview_markdown(results, preview_path, run_id="run-test")
        content = preview_path.read_text(encoding="utf-8")
        assert "| Cell |" in content
        assert "| Sim ID (short) |" in content

    def test_preview_deterministic_same_input_same_output(self, tmp_path: Path) -> None:
        """Mismo input → mismo output byte-igual (determinismo)."""
        fixed_sim_id = "aaaaaaaa-0000-0000-0000-000000000001"
        results = [self._make_cell_result(sim_id=fixed_sim_id)]

        preview_path_1 = tmp_path / "preview1.md"
        preview_path_2 = tmp_path / "preview2.md"

        _gen._emit_preview_markdown(results, preview_path_1, run_id="run-fixed")
        _gen._emit_preview_markdown(results, preview_path_2, run_id="run-fixed")

        content_1 = preview_path_1.read_text(encoding="utf-8")
        content_2 = preview_path_2.read_text(encoding="utf-8")
        assert content_1 == content_2

    def test_preview_sorts_by_tenant_kind_run_n(self, tmp_path: Path) -> None:
        """Resultados deben estar ordenados lexicográficamente."""
        results = [
            self._make_cell_result("tenant_medicina_estetica", "nurture", 0),
            self._make_cell_result("tenant_coach_lat", "happy", 0),
            self._make_cell_result("tenant_coach_lat", "happy", 1),
        ]
        preview_path = tmp_path / "preview.md"
        _gen._emit_preview_markdown(results, preview_path, run_id="run-sort-test")
        content = preview_path.read_text(encoding="utf-8")
        lines = content.splitlines()
        # tenant_coach_lat debe aparecer antes de tenant_medicina_estetica
        coach_lat_lines = [i for i, l in enumerate(lines) if "tenant_coach_lat" in l]
        medicina_lines = [i for i, l in enumerate(lines) if "tenant_medicina_estetica" in l]
        assert coach_lat_lines and medicina_lines
        assert min(coach_lat_lines) < min(medicina_lines)

    def test_preview_escapes_pipe_in_content(self, tmp_path: Path) -> None:
        """Caracteres | en el transcript_preview deben ser escapados para Markdown."""
        result = _gen.CellResult(
            key=_gen.CellKey(tenant_slug="tenant_coach_lat", persona_kind="happy", run_n=0),
            simulation_id=str(uuid.uuid4()),
            artifact_path=Path("/tmp/test.json"),
            total_turns=2,
            termination_reason="GOAL_COMPLETION",
            cost_usd=Decimal("0.072"),
            transcript_preview="texto | con | pipes",
        )
        preview_path = tmp_path / "preview_pipe.md"
        _gen._emit_preview_markdown([result], preview_path, run_id="run-pipe")
        content = preview_path.read_text(encoding="utf-8")
        # El | en el preview debe ser escapado como \\|
        assert "texto \\| con \\| pipes" in content

    def test_preview_contains_promotion_template(self, tmp_path: Path) -> None:
        """Markdown debe incluir template de comando promote_golden."""
        results = [self._make_cell_result()]
        preview_path = tmp_path / "preview.md"
        _gen._emit_preview_markdown(results, preview_path, run_id="run-cmd")
        content = preview_path.read_text(encoding="utf-8")
        assert "promote_golden.py" in content


class TestPerCellIsolation:
    """Valida que una falla en 1 celda no detiene la suite (Rule 5 graceful-degradation)."""

    def test_one_cell_failure_continues_other_cells(self, tmp_path: Path) -> None:
        """1 celda con excepción → otras continúan. Exit != 2 (budget OK)."""
        call_count: list[int] = [0]

        async def _side_effect_sim(*args: Any, **kwargs: Any) -> MagicMock:
            call_count[0] += 1
            if call_count[0] == 1:
                # Primera celda falla
                msg = "Fallo simulado en primera celda"
                raise RuntimeError(msg)
            return _make_mock_simulation_result()

        mock_actor = _make_actor_profile_mock()
        with (
            patch.object(_gen, "load_actor_profile_for_tenant", return_value=mock_actor),
            patch.object(_gen, "get_max_turns_for_persona_kind", return_value=10),
            patch.object(_gen, "run_simulation", side_effect=_side_effect_sim),
        ):
            exit_code = asyncio.run(
                _gen._main_async(
                    runs_per_cell=1,
                    concurrency=1,
                    cost_budget_usd=Decimal("8.00"),
                    output_dir=tmp_path,
                    run_id="test-isolation",
                    seed_base=42,
                    tenant_filter=None,
                    persona_kind_filter="happy",  # 5 celdas: 1 falla + 4 OK
                )
            )
        # 4/5 celdas exitosas → exit 1 (partial failure), no 2 (budget) ni crash
        assert exit_code in (0, 1)

    def test_all_cells_fail_returns_nonzero(self, tmp_path: Path) -> None:
        """Todas las celdas fallan → exit 1 (no crash)."""

        async def _always_fail(*args: Any, **kwargs: Any) -> MagicMock:
            msg = "Todo falla"
            raise RuntimeError(msg)

        mock_actor = _make_actor_profile_mock()
        with (
            patch.object(_gen, "load_actor_profile_for_tenant", return_value=mock_actor),
            patch.object(_gen, "get_max_turns_for_persona_kind", return_value=10),
            patch.object(_gen, "run_simulation", side_effect=_always_fail),
        ):
            exit_code = asyncio.run(
                _gen._main_async(
                    runs_per_cell=1,
                    concurrency=1,
                    cost_budget_usd=Decimal("8.00"),
                    output_dir=tmp_path,
                    run_id="test-all-fail",
                    seed_base=42,
                    tenant_filter="tenant_coach_lat",
                    persona_kind_filter="happy",
                )
            )
        assert exit_code == 1

    def test_successful_cells_write_json_artifacts(self, tmp_path: Path) -> None:
        """Celdas exitosas deben escribir JSON de artefacto en output_dir."""
        mock_actor = _make_actor_profile_mock()
        mock_result = _make_mock_simulation_result()
        with (
            patch.object(_gen, "load_actor_profile_for_tenant", return_value=mock_actor),
            patch.object(_gen, "get_max_turns_for_persona_kind", return_value=10),
            patch.object(_gen, "run_simulation", new_callable=AsyncMock, return_value=mock_result),
        ):
            asyncio.run(
                _gen._main_async(
                    runs_per_cell=1,
                    concurrency=1,
                    cost_budget_usd=Decimal("8.00"),
                    output_dir=tmp_path,
                    run_id="test-artifact",
                    seed_base=42,
                    tenant_filter="tenant_coach_lat",
                    persona_kind_filter="happy",
                )
            )
        # Debe existir al menos 1 JSON
        json_files = list(tmp_path.glob("sim_*.json"))
        assert len(json_files) >= 1

    def test_json_artifact_is_valid_json(self, tmp_path: Path) -> None:
        """JSON escrito por celda exitosa debe ser parseable."""
        mock_actor = _make_actor_profile_mock()
        mock_result = _make_mock_simulation_result()
        with (
            patch.object(_gen, "load_actor_profile_for_tenant", return_value=mock_actor),
            patch.object(_gen, "get_max_turns_for_persona_kind", return_value=10),
            patch.object(_gen, "run_simulation", new_callable=AsyncMock, return_value=mock_result),
        ):
            asyncio.run(
                _gen._main_async(
                    runs_per_cell=1,
                    concurrency=1,
                    cost_budget_usd=Decimal("8.00"),
                    output_dir=tmp_path,
                    run_id="test-json-valid",
                    seed_base=42,
                    tenant_filter="tenant_coach_lat",
                    persona_kind_filter="happy",
                )
            )
        json_files = list(tmp_path.glob("sim_*.json"))
        for f in json_files:
            data = json.loads(f.read_text(encoding="utf-8"))
            assert isinstance(data, dict)


# ─────────────────────────────────────────────────────────────────────────────
# test_single_cell_regen_supported
# ─────────────────────────────────────────────────────────────────────────────


class TestSingleCellRegen:
    """Valida que los filtros permitan regenerar una sola celda (D8 + D15)."""

    def test_single_cell_filter_produces_exactly_n_runs(self) -> None:
        """--tenant X --persona-kind Y → exactamente runs_per_cell celdas."""
        for runs_per_cell in (1, 3, 5):
            cells = _gen._build_matrix(
                runs_per_cell=runs_per_cell,
                tenant_filter="tenant_medicina_estetica",
                persona_kind_filter="nurture",
            )
            assert len(cells) == runs_per_cell

    def test_single_cell_uses_deterministic_seed(self) -> None:
        """Celdas con mismos parámetros producen el mismo seed determinístico."""
        cell = _gen.CellKey(tenant_slug="tenant_coach_lat", persona_kind="happy", run_n=0)
        seed_1 = _gen._compute_seed(cell, seed_base=42)
        seed_2 = _gen._compute_seed(cell, seed_base=42)
        assert seed_1 == seed_2

    def test_different_cells_produce_different_seeds(self) -> None:
        """Celdas distintas deben tener seeds distintos (dispersión)."""
        cell_a = _gen.CellKey(tenant_slug="tenant_coach_lat", persona_kind="happy", run_n=0)
        cell_b = _gen.CellKey(tenant_slug="tenant_coach_lat", persona_kind="nurture", run_n=0)
        cell_c = _gen.CellKey(tenant_slug="tenant_medicina_estetica", persona_kind="happy", run_n=0)
        seeds = {
            _gen._compute_seed(cell_a, seed_base=42),
            _gen._compute_seed(cell_b, seed_base=42),
            _gen._compute_seed(cell_c, seed_base=42),
        }
        # Al menos 2 de 3 seeds distintos (colisión de hash posible pero improbable)
        assert len(seeds) >= 2


# ─────────────────────────────────────────────────────────────────────────────
# test_reproducibility_smoke (CI nightly — --run-evals gateado)
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.skipif(
    not os.environ.get("RUN_EVALS"),
    reason="Smoke de reproducibilidad real requiere --run-evals (costo LLM ~$0.15). Activar: RUN_EVALS=1 pytest ...",
)
class TestReproducibilitySmoke:
    """Tests de humo con run_simulation real (gateados con RUN_EVALS=1)."""

    def test_same_seed_produces_same_simulation_id(self, tmp_path: Path) -> None:
        """Mismo seed + parámetros → mismo simulation_id (D8 UUID5 estable)."""
        # 1 tenant x 1 kind x 2 runs con mismo seed_base
        exit_code_1 = asyncio.run(
            _gen._main_async(
                runs_per_cell=1,
                concurrency=1,
                cost_budget_usd=Decimal("8.00"),
                output_dir=tmp_path / "run1",
                run_id="repro-test-run",
                seed_base=42,
                tenant_filter="tenant_coach_lat",
                persona_kind_filter="happy",
            )
        )
        exit_code_2 = asyncio.run(
            _gen._main_async(
                runs_per_cell=1,
                concurrency=1,
                cost_budget_usd=Decimal("8.00"),
                output_dir=tmp_path / "run2",
                run_id="repro-test-run",
                seed_base=42,
                tenant_filter="tenant_coach_lat",
                persona_kind_filter="happy",
            )
        )
        assert exit_code_1 == 0
        assert exit_code_2 == 0

        jsons_1 = list((tmp_path / "run1").glob("sim_*.json"))
        jsons_2 = list((tmp_path / "run2").glob("sim_*.json"))
        assert jsons_1 and jsons_2
        id_1 = json.loads(jsons_1[0].read_text())["simulation_id"]
        id_2 = json.loads(jsons_2[0].read_text())["simulation_id"]
        assert id_1 == id_2, "simulation_id debe ser determinístico con mismo seed"
