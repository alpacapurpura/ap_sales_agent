"""Tests para promote_golden.py (Story D / T-3).

Suite de tests unitarios para el script de promoción de simulaciones a goldens YAML.
Los tests E2E con run_simulation real están gateados con --run-evals (RUN_EVALS=1).

Coverage:
    - Auto-derivación del termination_reason
    - Auto-derivación de expected_tools_invoked (unión)
    - Forbidden tools por persona_kind (D17)
    - Extracción de voice_attributes desde personality_profile
    - Idempotencia: mismos args → mismo YAML (excepto curated_at)
    - YAML safe_dump determinístico
    - Exit code 2 en ValidationError (golden inválido)
    - persona_kind fuera de scope → ValueError
    - E2E smoke (gateado --run-evals)
"""

from __future__ import annotations

import os
import sys
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import yaml

# Ajuste sys.path para importar scripts/ como módulos
_BACKEND_ROOT = Path(__file__).resolve().parents[2]  # backend/
sys.path.insert(0, str(_BACKEND_ROOT / "scripts"))

import promote_golden as _promo


# ─────────────────────────────────────────────────────────────────────────────
# Helpers de fixtures
# ─────────────────────────────────────────────────────────────────────────────


def _make_artifact(
    tenant_slug: str = "tenant_coach_lat",
    persona_kind: str = "happy",
    termination_reason: str = "GOAL_COMPLETION",
    tool_calls_by_turn: list[list[str]] | None = None,
    simulation_id: str | None = None,
    run_id: str | None = None,
    dialect_code: str = "es-PE",
    cost_usd: str = "0.072",
) -> dict[str, Any]:
    """Factory — retorna dict de artefacto de simulación mínimo y válido."""
    sim_id = simulation_id or str(uuid.uuid4())
    rid = run_id or str(uuid.uuid4())

    transcript: list[dict[str, Any]] = [
        {
            "role": "customer",
            "content": "Hola, me interesa tu servicio",
            "turn_number": 0,
            "metadata": {},
        },
        {
            "role": "agent",
            "content": "Con gusto te ayudo, ¿qué necesitas?",
            "turn_number": 1,
            "tool_calls": tool_calls_by_turn[0] if tool_calls_by_turn else None,
            "metadata": {},
        },
        {
            "role": "customer",
            "content": "Cuéntame más",
            "turn_number": 2,
            "metadata": {},
        },
        {
            "role": "agent",
            "content": "Claro, tengo esta oferta...",
            "turn_number": 3,
            "tool_calls": tool_calls_by_turn[1] if tool_calls_by_turn and len(tool_calls_by_turn) > 1 else None,
            "metadata": {},
        },
    ]

    return {
        "simulation_id": sim_id,
        "run_id": rid,
        "archetype_slug": tenant_slug,
        "tenant_archetype_slug": tenant_slug,
        "persona_kind": persona_kind,
        "dialect_code": dialect_code,
        "transcript": transcript,
        "termination_reason": termination_reason,
        "total_turns": len(transcript),
        "cost_summary": {
            "total_cost_usd": cost_usd,
            "agent_cost_usd": "0.036",
            "simulator_cost_usd": "0.036",
        },
        "schema_version": 1,
        "seed": 42,
    }


def _make_mock_tenant_context(
    tenant_slug: str = "tenant_coach_lat",
) -> MagicMock:
    """Factory — TenantContext mock con personality_profile.dimensions."""
    ctx = MagicMock()
    ctx.archetype_slug = tenant_slug
    ctx.personality_profile = {
        "dimensions": {
            "energy": 0.6,
            "warmth": 0.8,
            "humor": 0.3,
            "expressiveness": 0.7,
            "narrative": 0.5,
            "verbosity": 0.4,
        }
    }
    return ctx


# ─────────────────────────────────────────────────────────────────────────────
# test_auto_derive_expected_termination_reason
# ─────────────────────────────────────────────────────────────────────────────


class TestAutoDerivTerminationReason:
    """Valida que expected_termination_reason se derive del artefacto."""

    @pytest.mark.parametrize(
        "termination_reason",
        ["GOAL_COMPLETION", "MAX_TURNS", "CUSTOMER_EXIT"],
    )
    def test_derives_correct_termination_reason(self, termination_reason: str) -> None:
        """expected_termination_reason debe mapear desde artifact.termination_reason."""
        artifact = _make_artifact(termination_reason=termination_reason)
        with patch.object(_promo, "load_eval_tenant", return_value=_make_mock_tenant_context()):
            golden = _promo._build_golden(artifact, "coach-lat-happy-001", notes="", actor_profile_id="perfil-happy")
        assert golden.expected_termination_reason == termination_reason

    def test_termination_reason_preserved_in_yaml(self, tmp_path: Path) -> None:
        """YAML escrito debe preservar el termination_reason."""
        artifact = _make_artifact(termination_reason="CUSTOMER_EXIT")
        with patch.object(_promo, "load_eval_tenant", return_value=_make_mock_tenant_context()):
            golden = _promo._build_golden(artifact, "coach-lat-happy-002", notes="", actor_profile_id="perfil-happy")
        out_path = tmp_path / "golden.yaml"
        _promo._write_yaml(golden, out_path)
        data = yaml.safe_load(out_path.read_text(encoding="utf-8"))
        assert data["expected_termination_reason"] == "CUSTOMER_EXIT"


# ─────────────────────────────────────────────────────────────────────────────
# test_auto_derive_expected_tools_invoked_union
# ─────────────────────────────────────────────────────────────────────────────


class TestAutoDerivToolsInvoked:
    """Valida que expected_tools_invoked sea la unión de tool_calls de todos los agent turns."""

    def test_derives_union_of_tool_calls(self) -> None:
        """Unión de tool_calls en turns del agente → lista sorted sin duplicados."""
        artifact = _make_artifact(
            tool_calls_by_turn=[
                ["buscar_oferta", "consultar_disponibilidad"],
                ["buscar_oferta", "enviar_resumen"],  # buscar_oferta duplicado
            ]
        )
        result = _promo._derive_expected_tools_invoked(artifact["transcript"])
        assert result == sorted({"buscar_oferta", "consultar_disponibilidad", "enviar_resumen"})

    def test_empty_when_no_tool_calls(self) -> None:
        """Sin tool_calls en ningún turn → lista vacía."""
        artifact = _make_artifact()  # sin tool_calls
        result = _promo._derive_expected_tools_invoked(artifact["transcript"])
        assert result == []

    def test_ignores_customer_tool_calls(self) -> None:
        """tool_calls en turns de customer no cuentan (solo agent turns)."""
        transcript = [
            {"role": "customer", "content": "Hola", "turn_number": 0, "tool_calls": ["CUSTOMER_TOOL"]},
            {"role": "agent", "content": "Respuesta", "turn_number": 1, "tool_calls": ["tool_agente"]},
        ]
        result = _promo._derive_expected_tools_invoked(transcript)
        assert result == ["tool_agente"]
        assert "CUSTOMER_TOOL" not in result

    def test_handles_none_tool_calls(self) -> None:
        """tool_calls=None en turn del agente debe ser ignorado sin error."""
        transcript = [
            {"role": "agent", "content": "Respuesta", "turn_number": 0, "tool_calls": None},
        ]
        result = _promo._derive_expected_tools_invoked(transcript)
        assert result == []


# ─────────────────────────────────────────────────────────────────────────────
# test_forbidden_tools_per_persona_kind
# ─────────────────────────────────────────────────────────────────────────────


class TestForbiddenToolsPerPersonaKind:
    """Valida que forbidden_tools siga el mapa D17 por persona_kind."""

    def test_unqualified_has_3_forbidden_tools(self) -> None:
        """unqualified → 3 tools de cierre bloqueados (D17)."""
        artifact = _make_artifact(persona_kind="unqualified")
        with patch.object(_promo, "load_eval_tenant", return_value=_make_mock_tenant_context()):
            golden = _promo._build_golden(artifact, "unq-001", notes="", actor_profile_id="perfil-unq")
        assert len(golden.forbidden_tools) == 3
        assert "enroll_immediate" in golden.forbidden_tools
        assert "send_payment_link" in golden.forbidden_tools
        assert "confirm_appointment" in golden.forbidden_tools

    def test_happy_has_no_forbidden_tools(self) -> None:
        """happy → lista vacía de forbidden_tools."""
        artifact = _make_artifact(persona_kind="happy")
        with patch.object(_promo, "load_eval_tenant", return_value=_make_mock_tenant_context()):
            golden = _promo._build_golden(artifact, "happy-001", notes="", actor_profile_id="perfil-happy")
        assert golden.forbidden_tools == []

    def test_nurture_has_no_forbidden_tools(self) -> None:
        """nurture → lista vacía de forbidden_tools."""
        artifact = _make_artifact(persona_kind="nurture")
        with patch.object(_promo, "load_eval_tenant", return_value=_make_mock_tenant_context()):
            golden = _promo._build_golden(artifact, "nurture-001", notes="", actor_profile_id="perfil-nurture")
        assert golden.forbidden_tools == []

    def test_forbidden_tools_map_is_complete(self) -> None:
        """El mapa _FORBIDDEN_TOOLS_BY_KIND cubre los 3 persona_kinds."""
        assert "unqualified" in _promo._FORBIDDEN_TOOLS_BY_KIND
        assert "happy" in _promo._FORBIDDEN_TOOLS_BY_KIND
        assert "nurture" in _promo._FORBIDDEN_TOOLS_BY_KIND


# ─────────────────────────────────────────────────────────────────────────────
# test_extract_voice_attributes_reads_personality_profile
# ─────────────────────────────────────────────────────────────────────────────


class TestExtractVoiceAttributes:
    """Valida que _extract_voice_attributes lea dimensions del personality_profile."""

    def test_extracts_dimension_keys_sorted(self) -> None:
        """Retorna las keys del dict dimensions en orden alfabético."""
        ctx = _make_mock_tenant_context()
        with patch.object(_promo, "load_eval_tenant", return_value=ctx):
            attrs = _promo._extract_voice_attributes("tenant_coach_lat")
        expected = sorted(["energy", "warmth", "humor", "expressiveness", "narrative", "verbosity"])
        assert attrs == expected

    def test_returns_empty_list_when_no_dimensions(self) -> None:
        """personality_profile sin dimensions → lista vacía (no crash)."""
        ctx = MagicMock()
        ctx.personality_profile = {}  # sin dimensions
        with patch.object(_promo, "load_eval_tenant", return_value=ctx):
            attrs = _promo._extract_voice_attributes("tenant_coach_lat")
        assert attrs == []

    def test_returns_empty_list_when_personality_profile_missing(self) -> None:
        """personality_profile = None → lista vacía (no crash)."""
        ctx = MagicMock()
        ctx.personality_profile = None
        with patch.object(_promo, "load_eval_tenant", return_value=ctx):
            attrs = _promo._extract_voice_attributes("tenant_coach_lat")
        assert attrs == []

    def test_never_mutates_personality_profile(self) -> None:
        """La extracción debe ser read-only (no muta el perfil)."""
        ctx = _make_mock_tenant_context()
        original_keys = sorted(ctx.personality_profile["dimensions"].keys())
        with patch.object(_promo, "load_eval_tenant", return_value=ctx):
            _promo._extract_voice_attributes("tenant_coach_lat")
        # Keys no mutadas
        assert sorted(ctx.personality_profile["dimensions"].keys()) == original_keys


# ─────────────────────────────────────────────────────────────────────────────
# test_idempotent_overwrite_same_args
# ─────────────────────────────────────────────────────────────────────────────


class TestIdempotentOverwrite:
    """Valida que mismos args → mismo YAML (idempotencia modulo curated_at)."""

    def test_same_artifact_same_golden_id_same_actor_produces_same_yaml(self, tmp_path: Path) -> None:
        """Dos llamadas con mismo input → YAMLs con mismos campos (excepto curated_at)."""
        artifact = _make_artifact(
            simulation_id="bbbbbbbb-0000-0000-0000-000000000001",
            run_id="cccccccc-0000-0000-0000-000000000002",
        )
        ctx = _make_mock_tenant_context()

        with patch.object(_promo, "load_eval_tenant", return_value=ctx):
            golden_1 = _promo._build_golden(artifact, "coach-idempotent-001", notes="test", actor_profile_id="perfil-x")
            golden_2 = _promo._build_golden(artifact, "coach-idempotent-001", notes="test", actor_profile_id="perfil-x")

        # Comparar model_dump excluyendo metadata.curated_at (timestamp de ahora)
        dump_1 = golden_1.model_dump(mode="json")
        dump_2 = golden_2.model_dump(mode="json")
        dump_1["metadata"].pop("curated_at", None)
        dump_2["metadata"].pop("curated_at", None)
        assert dump_1 == dump_2

    def test_write_yaml_idempotent_same_file(self, tmp_path: Path) -> None:
        """Escribir mismo golden en mismo path → sobreescritura sin error."""
        artifact = _make_artifact()
        ctx = _make_mock_tenant_context()
        out_path = tmp_path / "golden.yaml"

        with patch.object(_promo, "load_eval_tenant", return_value=ctx):
            golden = _promo._build_golden(artifact, "coach-overwrite-001", notes="", actor_profile_id="perfil-y")

        _promo._write_yaml(golden, out_path)
        content_1 = out_path.read_text(encoding="utf-8")
        _promo._write_yaml(golden, out_path)
        content_2 = out_path.read_text(encoding="utf-8")
        assert content_1 == content_2  # byte-idéntico


# ─────────────────────────────────────────────────────────────────────────────
# test_yaml_safe_dump_deterministic
# ─────────────────────────────────────────────────────────────────────────────


class TestYamlSafeDumpDeterministic:
    """Valida que _write_yaml use safe_dump con parámetros determinísticos."""

    def test_yaml_uses_sort_keys(self, tmp_path: Path) -> None:
        """YAML debe tener keys ordenadas alfabéticamente (sort_keys=True)."""
        artifact = _make_artifact()
        ctx = _make_mock_tenant_context()
        out_path = tmp_path / "golden_sorted.yaml"

        with patch.object(_promo, "load_eval_tenant", return_value=ctx):
            golden = _promo._build_golden(artifact, "coach-sorted-001", notes="", actor_profile_id="perfil-sort")

        _promo._write_yaml(golden, out_path)
        content = out_path.read_text(encoding="utf-8")
        # Verificar que el YAML no tiene sintaxis de flow (curlies/brackets)
        # por default_flow_style=False
        assert "{" not in content.split("\n")[0]  # primera línea no es flow

    def test_yaml_allows_unicode(self, tmp_path: Path) -> None:
        """YAML debe preservar caracteres unicode (allow_unicode=True)."""
        artifact = _make_artifact()
        artifact["transcript"][0]["content"] = "Hola, ¿cómo están? Me llaman Ñoño"
        ctx = _make_mock_tenant_context()
        out_path = tmp_path / "golden_unicode.yaml"

        with patch.object(_promo, "load_eval_tenant", return_value=ctx):
            golden = _promo._build_golden(artifact, "coach-unicode-001", notes="", actor_profile_id="perfil-uni")

        _promo._write_yaml(golden, out_path)
        content = out_path.read_text(encoding="utf-8")
        # Unicode no debe estar escapado (ej. \uXXXX)
        assert "\\u" not in content
        # Los caracteres especiales deben aparecer directamente
        assert "¿" in content or "Ñ" in content or "ó" in content

    def test_yaml_is_parseable_back(self, tmp_path: Path) -> None:
        """YAML escrito debe poder parsearse de vuelta a dict válido."""
        artifact = _make_artifact()
        ctx = _make_mock_tenant_context()
        out_path = tmp_path / "golden_parse.yaml"

        with patch.object(_promo, "load_eval_tenant", return_value=ctx):
            golden = _promo._build_golden(artifact, "coach-parse-001", notes="", actor_profile_id="perfil-parse")

        _promo._write_yaml(golden, out_path)
        data = yaml.safe_load(out_path.read_text(encoding="utf-8"))
        assert isinstance(data, dict)
        assert data["id"] == "coach-parse-001"

    def test_yaml_keys_are_sorted_in_file(self, tmp_path: Path) -> None:
        """Las keys de primer nivel deben estar ordenadas en el YAML."""
        artifact = _make_artifact()
        ctx = _make_mock_tenant_context()
        out_path = tmp_path / "golden_ksorted.yaml"

        with patch.object(_promo, "load_eval_tenant", return_value=ctx):
            golden = _promo._build_golden(artifact, "zzz-last-key", notes="", actor_profile_id="perfil-zzz")

        _promo._write_yaml(golden, out_path)
        data = yaml.safe_load(out_path.read_text(encoding="utf-8"))
        keys = list(data.keys())
        assert keys == sorted(keys), f"Keys no ordenadas: {keys}"


# ─────────────────────────────────────────────────────────────────────────────
# test_validation_error_exit_code_2
# ─────────────────────────────────────────────────────────────────────────────


class TestValidationErrorExitCode:
    """Valida que ValidationError en _build_golden resulte en exit code 2."""

    def test_build_golden_raises_on_invalid_transcript(self) -> None:
        """Transcript vacío → _build_golden debe lanzar ValueError (< 2 turns)."""
        artifact = _make_artifact()
        artifact["transcript"] = []  # viola min_length=2 en GoldenScenarioModel
        ctx = _make_mock_tenant_context()
        with (
            patch.object(_promo, "load_eval_tenant", return_value=ctx),
            pytest.raises((ValueError, Exception)),
        ):
            _promo._build_golden(artifact, "coach-invalid-001", notes="", actor_profile_id="perfil-inv")

    def test_main_returns_exit_2_on_missing_artifact(self, tmp_path: Path) -> None:
        """Artefacto no encontrado → main() retorna exit 2."""
        import sys

        test_args = [
            "promote_golden.py",
            "--simulation-id",
            "no-existe",
            "--golden-id",
            "test",
            "--artifact-dir",
            str(tmp_path),
            "--actor-profile-id",
            "perfil-x",
        ]
        with patch.object(sys, "argv", test_args):
            exit_code = _promo.main()
        assert exit_code == 2


# ─────────────────────────────────────────────────────────────────────────────
# test_persona_kind_out_of_scope_raises
# ─────────────────────────────────────────────────────────────────────────────


class TestPersonaKindOutOfScope:
    """Valida que persona_kind fuera de scope (adversarial/edge/negative) → ValueError."""

    @pytest.mark.parametrize("invalid_kind", ["adversarial", "edge", "negative", "unknown"])
    def test_out_of_scope_persona_kind_raises_value_error(self, invalid_kind: str) -> None:
        """Persona kind fuera de Story D scope → ValueError antes de escritura."""
        artifact = _make_artifact(persona_kind=invalid_kind)
        ctx = _make_mock_tenant_context()
        with (
            patch.object(_promo, "load_eval_tenant", return_value=ctx),
            pytest.raises(ValueError, match=r"not in goldens scope"),
        ):
            _promo._build_golden(artifact, f"{invalid_kind}-001", notes="", actor_profile_id="perfil-test")


# ─────────────────────────────────────────────────────────────────────────────
# test_build_golden_writes_correct_fields
# ─────────────────────────────────────────────────────────────────────────────


class TestBuildGoldenFields:
    """Valida campos del GoldenScenarioModel construido por _build_golden."""

    def test_schema_version_is_1(self) -> None:
        """schema_version debe ser 1 (D6 cement)."""
        artifact = _make_artifact()
        ctx = _make_mock_tenant_context()
        with patch.object(_promo, "load_eval_tenant", return_value=ctx):
            golden = _promo._build_golden(artifact, "coach-fields-001", notes="", actor_profile_id="perfil-f")
        assert golden.schema_version == 1

    def test_actor_profile_schema_version_is_2(self) -> None:
        """actor_profile_schema_version debe ser 2 (D7 cement)."""
        artifact = _make_artifact()
        ctx = _make_mock_tenant_context()
        with patch.object(_promo, "load_eval_tenant", return_value=ctx):
            golden = _promo._build_golden(artifact, "coach-apv-001", notes="", actor_profile_id="perfil-f")
        assert golden.actor_profile_schema_version == 2

    def test_notes_stored_in_metadata(self) -> None:
        """--notes pasado a main() debe guardarse en metadata.notes."""
        artifact = _make_artifact()
        ctx = _make_mock_tenant_context()
        with patch.object(_promo, "load_eval_tenant", return_value=ctx):
            golden = _promo._build_golden(
                artifact, "coach-notes-001", notes="Esta es la nota de Chris", actor_profile_id="perfil-n"
            )
        assert golden.metadata.notes == "Esta es la nota de Chris"

    def test_cost_usd_is_decimal(self) -> None:
        """cost_usd_at_generation debe ser Decimal (no float)."""
        artifact = _make_artifact(cost_usd="0.072")
        ctx = _make_mock_tenant_context()
        with patch.object(_promo, "load_eval_tenant", return_value=ctx):
            golden = _promo._build_golden(artifact, "coach-decimal-001", notes="", actor_profile_id="perfil-d")
        assert isinstance(golden.metadata.cost_usd_at_generation, Decimal)

    def test_nurture_has_expected_min_objections_handled(self) -> None:
        """nurture → expected_min_distinct_objections_handled no debe ser None."""
        artifact = _make_artifact(persona_kind="nurture")
        ctx = _make_mock_tenant_context()
        with patch.object(_promo, "load_eval_tenant", return_value=ctx):
            golden = _promo._build_golden(artifact, "nurture-obj-001", notes="", actor_profile_id="perfil-n")
        assert golden.expected_min_distinct_objections_handled is not None
        assert golden.expected_min_distinct_objections_handled >= 1

    def test_happy_expected_min_objections_is_none(self) -> None:
        """happy → expected_min_distinct_objections_handled debe ser None."""
        artifact = _make_artifact(persona_kind="happy")
        ctx = _make_mock_tenant_context()
        with patch.object(_promo, "load_eval_tenant", return_value=ctx):
            golden = _promo._build_golden(artifact, "happy-obj-001", notes="", actor_profile_id="perfil-h")
        assert golden.expected_min_distinct_objections_handled is None


# ─────────────────────────────────────────────────────────────────────────────
# test_archetype_slug_propagation (DEEPER-B regression — archetype_slug fallback)
# ─────────────────────────────────────────────────────────────────────────────


class TestArchetypeSlugPropagation:
    """Regression: DEEPER-B — archetype_slug empty cuando artifact solo tiene 'archetype_slug'.

    generate_golden_candidates.py escribe result.model_dump() → campo es 'archetype_slug'.
    promote_golden.py leía solo 'tenant_archetype_slug' → devolvía '' → ValidationError.

    Este test reproduce el artefacto real generado por _run_one_cell (sin 'tenant_archetype_slug')
    y verifica que _build_golden resuelve el tenant_slug correctamente.
    """

    def test_artifact_with_only_archetype_slug_resolves_tenant(self) -> None:
        """Artefacto con SOLO 'archetype_slug' (sin 'tenant_archetype_slug') → tenant_slug correcto.

        Simula el artifact JSON escrito por generate_golden_candidates (result.model_dump()),
        que solo contiene 'archetype_slug' (campo de SimulationResult), no 'tenant_archetype_slug'.
        _build_golden debe resolverlo correctamente sin empty-string fallback.
        """
        tenant_slug = "tenant_coach_lat"
        # Artefacto tipo SimulationResult.model_dump() — solo tiene 'archetype_slug'
        artifact = _make_artifact(tenant_slug=tenant_slug)
        # Remover 'tenant_archetype_slug' para simular artifact real del generador
        artifact.pop("tenant_archetype_slug", None)
        assert "archetype_slug" in artifact
        assert "tenant_archetype_slug" not in artifact

        ctx = _make_mock_tenant_context(tenant_slug)
        with patch.object(_promo, "load_eval_tenant", return_value=ctx):
            golden = _promo._build_golden(artifact, "coach-lat-deeperb-001", notes="", actor_profile_id="perfil-reg")

        assert golden.tenant_slug == tenant_slug, (
            f"tenant_slug vacío — bug DEEPER-B: artifact.archetype_slug='{artifact.get('archetype_slug')}' "
            f"no fue resuelto como tenant_slug"
        )

    def test_artifact_missing_both_slug_fields_raises(self) -> None:
        """Artefacto sin ningún campo de slug → _build_golden debe fallar con ValidationError.

        Verifica que la fix no enmascare artefactos genuinamente inválidos.
        """
        artifact = _make_artifact(tenant_slug="tenant_coach_lat")
        artifact.pop("tenant_archetype_slug", None)
        artifact.pop("archetype_slug", None)
        # Sin ningún campo de slug → tenant_slug = "" → ValidationError esperado

        ctx = _make_mock_tenant_context()
        with (
            patch.object(_promo, "load_eval_tenant", return_value=ctx),
            pytest.raises((ValueError, TypeError)),  # pydantic.ValidationError hereda de ValueError
        ):
            _promo._build_golden(artifact, "coach-no-slug-001", notes="", actor_profile_id="perfil-ns")

    def test_generator_artifact_includes_tenant_archetype_slug_field(self, tmp_path: Path) -> None:
        """Artefacto escrito por _run_one_cell debe incluir 'tenant_archetype_slug'.

        Verifica la fix en generate_golden_candidates._run_one_cell:
        artifact_data['tenant_archetype_slug'] debe ser escrito explícitamente
        para que promote_golden no falle en el flujo E2E.
        """
        import asyncio
        import json as _json
        import uuid as _uuid

        sys.path.insert(0, str(_BACKEND_ROOT / "scripts"))
        import generate_golden_candidates as _gen

        tenant_slug = "tenant_coach_lat"
        sim_id = _uuid.uuid4()
        run_id = _uuid.uuid4()

        # Mock SimulationResult mínimo con archetype_slug (como lo retorna run_simulation)
        mock_result = MagicMock()
        mock_result.simulation_id = sim_id
        mock_result.run_id = run_id
        mock_result.archetype_slug = tenant_slug
        mock_result.total_turns = 2

        tr_reason = MagicMock()
        tr_reason.value = "GOAL_COMPLETION"
        mock_result.termination_reason = tr_reason

        cost_summary = MagicMock()
        cost_summary.total_cost_usd = "0.072"
        mock_result.cost_summary = cost_summary

        t1 = MagicMock()
        t1.role = "customer"
        t1.content = "Hola"
        t2 = MagicMock()
        t2.role = "agent"
        t2.content = "Con gusto te ayudo"
        mock_result.transcript = [t1, t2]

        # model_dump() reproduce SimulationResult — archetype_slug presente, tenant_archetype_slug NO
        mock_result.model_dump.return_value = {
            "simulation_id": str(sim_id),
            "run_id": str(run_id),
            "archetype_slug": tenant_slug,  # campo real de SimulationResult
            "transcript": [],
            "termination_reason": "GOAL_COMPLETION",
            "total_turns": 2,
            "cost_summary": {"total_cost_usd": "0.072"},
        }

        mock_actor = MagicMock()
        mock_actor.id = "perfil-happy-coach"
        mock_actor.persona_kind = "happy"

        cell = _gen.CellKey(tenant_slug=tenant_slug, persona_kind="happy", run_n=0)
        semaphore = asyncio.Semaphore(1)

        async def _run() -> _gen.CellResult:
            with (
                patch.object(_gen, "load_actor_profile_for_tenant", return_value=mock_actor),
                patch.object(_gen, "get_max_turns_for_persona_kind", return_value=10),
                patch.object(_gen, "run_simulation", new=AsyncMock(return_value=mock_result)),
            ):
                return await _gen._run_one_cell(
                    cell=cell,
                    semaphore=semaphore,
                    output_dir=tmp_path,
                    run_id="test-gen-slug",
                    seed_base=42,
                )

        from unittest.mock import AsyncMock

        asyncio.run(_run())

        # Verificar que el artefacto JSON escrito tiene 'tenant_archetype_slug'
        artifact_files = list(tmp_path.glob("sim_*.json"))
        assert artifact_files, "No se escribió ningún artefacto"
        artifact_data = _json.loads(artifact_files[0].read_text(encoding="utf-8"))
        assert "tenant_archetype_slug" in artifact_data, (
            "generate_golden_candidates._run_one_cell no escribe 'tenant_archetype_slug' "
            "en el artefacto JSON — promote_golden falla en E2E con empty archetype_slug"
        )
        assert artifact_data["tenant_archetype_slug"] == tenant_slug


# ─────────────────────────────────────────────────────────────────────────────
# test_promote_refuses_crashed_simulation (DEEPER-D regression)
# ─────────────────────────────────────────────────────────────────────────────


class TestPromoteRefusesCrashedSimulation:
    """DEEPER-D: promote_golden debe rechazar simulaciones que terminaron en crash.

    Una simulación con termination_reason='agent_error' no debe ser promovida
    a golden — los goldens son referencias de validación, no capturas de crashes.

    Exit code esperado: 2 con mensaje de error claro en español.
    """

    def test_build_golden_raises_on_agent_error_termination(self) -> None:
        """artifact.termination_reason='agent_error' → ValueError con mensaje claro en español."""
        artifact = _make_artifact(termination_reason="agent_error")
        ctx = _make_mock_tenant_context()
        with (
            patch.object(_promo, "load_eval_tenant", return_value=ctx),
            pytest.raises(ValueError, match=r"(?i)(error|crash|agent_error)"),
        ):
            _promo._build_golden(artifact, "coach-crash-001", notes="", actor_profile_id="perfil-crash")

    def test_build_golden_raises_on_empty_transcript(self) -> None:
        """transcript vacío con termination_reason válido → ValueError por transcript corto.

        Cuando el agente crashea en el turno 0, el transcript queda vacío
        y GoldenScenarioModel no puede construirse (min_length=2).
        El preflight debe capturar este caso antes que Pydantic.
        """
        artifact = _make_artifact()
        artifact["transcript"] = []
        artifact["termination_reason"] = "GOAL_COMPLETION"  # pero sin turns
        ctx = _make_mock_tenant_context()
        with (
            patch.object(_promo, "load_eval_tenant", return_value=ctx),
            pytest.raises((ValueError, Exception)),
        ):
            _promo._build_golden(artifact, "coach-empty-001", notes="", actor_profile_id="perfil-empty")

    def test_main_returns_exit_2_on_agent_error_artifact(self, tmp_path: Path) -> None:
        """main() con artefacto crash → exit code 2 (no escribe YAML)."""
        import json as _json

        # Crear artefacto con crash
        artifact = _make_artifact(termination_reason="agent_error")
        artifact_path = tmp_path / f"sim_{artifact['simulation_id']}.json"
        artifact_path.write_text(_json.dumps(artifact), encoding="utf-8")

        test_args = [
            "promote_golden.py",
            "--simulation-id",
            artifact["simulation_id"],
            "--golden-id",
            "coach-crash-main-001",
            "--artifact-dir",
            str(tmp_path),
            "--actor-profile-id",
            "perfil-crash",
        ]
        with (
            patch.object(_promo, "load_eval_tenant", return_value=_make_mock_tenant_context()),
            patch.object(sys, "argv", test_args),
        ):
            exit_code = _promo.main()
        assert exit_code == 2

    def test_main_does_not_write_yaml_on_agent_error(self, tmp_path: Path) -> None:
        """main() con artefacto crash → ningún archivo YAML escrito."""
        import json as _json

        artifact = _make_artifact(termination_reason="agent_error")
        artifact_path = tmp_path / f"sim_{artifact['simulation_id']}.json"
        artifact_path.write_text(_json.dumps(artifact), encoding="utf-8")

        test_args = [
            "promote_golden.py",
            "--simulation-id",
            artifact["simulation_id"],
            "--golden-id",
            "coach-nowrite-001",
            "--artifact-dir",
            str(tmp_path),
            "--actor-profile-id",
            "perfil-nowrite",
        ]
        with (
            patch.object(_promo, "load_eval_tenant", return_value=_make_mock_tenant_context()),
            patch.object(sys, "argv", test_args),
        ):
            _promo.main()

        # No debe haber escrito ningún YAML
        yaml_files = list(tmp_path.rglob("*.yaml"))
        assert yaml_files == [], f"Se escribió YAML inesperado: {yaml_files}"

    def test_validate_artifact_promotable_rejects_all_invalid_reasons(self) -> None:
        """_validate_artifact_promotable rechaza razones inválidas de terminación."""
        invalid_reasons = ["agent_error", "timeout_error", "system_crash", "unknown", ""]
        for reason in invalid_reasons:
            artifact = _make_artifact(termination_reason=reason)
            with pytest.raises(ValueError, match=r"(?i)(error|crash)"):
                _promo._validate_artifact_promotable(artifact)

    def test_validate_artifact_promotable_accepts_valid_reasons(self) -> None:
        """_validate_artifact_promotable acepta las 3 razones válidas de terminación."""
        valid_reasons = ["GOAL_COMPLETION", "MAX_TURNS", "CUSTOMER_EXIT"]
        for reason in valid_reasons:
            artifact = _make_artifact(termination_reason=reason)
            # No debe lanzar excepción
            _promo._validate_artifact_promotable(artifact)

    def test_validate_artifact_promotable_rejects_empty_transcript(self) -> None:
        """_validate_artifact_promotable rechaza transcript vacío (crash en turno 0)."""
        artifact = _make_artifact(termination_reason="GOAL_COMPLETION")
        artifact["transcript"] = []
        with pytest.raises(ValueError, match=r"(?i)(transcript|turn)"):
            _promo._validate_artifact_promotable(artifact)

    def test_error_message_mentions_crash_reason(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """Mensaje de error de preflight debe mencionar 'agent_error' y ser en español."""
        import json as _json

        artifact = _make_artifact(termination_reason="agent_error")
        artifact_path = tmp_path / f"sim_{artifact['simulation_id']}.json"
        artifact_path.write_text(_json.dumps(artifact), encoding="utf-8")

        test_args = [
            "promote_golden.py",
            "--simulation-id",
            artifact["simulation_id"],
            "--golden-id",
            "coach-errmsg-001",
            "--artifact-dir",
            str(tmp_path),
            "--actor-profile-id",
            "perfil-msg",
        ]
        with (
            patch.object(_promo, "load_eval_tenant", return_value=_make_mock_tenant_context()),
            patch.object(sys, "argv", test_args),
        ):
            exit_code = _promo.main()

        assert exit_code == 2
        captured = capsys.readouterr()
        # El mensaje de error debe estar en stderr y mencionar el motivo del crash
        assert "agent_error" in captured.err
        # Debe ser un mensaje legible (no solo traceback)
        assert "ERROR" in captured.err


# ─────────────────────────────────────────────────────────────────────────────
# test_e2e_smoke (CI nightly — --run-evals gateado)
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.skipif(
    not os.environ.get("RUN_EVALS"),
    reason="E2E smoke requiere --run-evals (costo LLM ~$0.15). Activar: RUN_EVALS=1 pytest ...",
)
class TestE2ESmoke:
    """E2E smoke: generate_golden_candidates → promote_golden → cargar YAML."""

    def test_generate_and_promote_cycle(self, tmp_path: Path) -> None:
        """Generar 1 simulación real → promover a golden YAML → deserializar."""
        import asyncio

        sys.path.insert(0, str(_BACKEND_ROOT / "scripts"))

        # 1. Generar 1 candidato
        import importlib

        _gen_mod = importlib.import_module("generate_golden_candidates")
        exit_code = asyncio.run(
            _gen_mod._main_async(  # type: ignore[attr-defined]
                runs_per_cell=1,
                concurrency=1,
                cost_budget_usd=Decimal("8.00"),
                output_dir=tmp_path / "artifacts",
                run_id="e2e-smoke-run",
                seed_base=42,
                tenant_filter="tenant_coach_lat",
                persona_kind_filter="happy",
            )
        )
        assert exit_code == 0, "Generación falló"

        # 2. Localizar artefacto
        artifact_dir = tmp_path / "artifacts"
        json_files = list(artifact_dir.glob("sim_*.json"))
        assert json_files, "No se generó ningún artefacto"
        artifact_path = json_files[0]
        artifact_data = __import__("json").loads(artifact_path.read_text(encoding="utf-8"))
        sim_id = artifact_data["simulation_id"]

        # 3. Promover a golden YAML
        import sys as _sys

        test_args = [
            "promote_golden.py",
            "--simulation-id",
            sim_id,
            "--golden-id",
            "e2e-smoke-coach-lat-happy-001",
            "--artifact-dir",
            str(artifact_dir),
            "--actor-profile-id",
            "lead-frio-impaciente-pe",
            "--notes",
            "E2E smoke test auto-generated",
        ]
        with patch.object(_sys, "argv", test_args):
            exit_promote = _promo.main()
        assert exit_promote == 0, "Promoción falló"

        # 4. Cargar y deserializar el YAML generado
        from tests.agentic_evals.sales_agent.goldens._schema import GoldenScenarioModel

        golden_path = (
            _BACKEND_ROOT
            / "tests"
            / "agentic_evals"
            / "sales_agent"
            / "goldens"
            / "tenant_coach_lat"
            / "happy"
            / "e2e-smoke-coach-lat-happy-001.yaml"
        )
        assert golden_path.exists(), f"Golden no fue escrito: {golden_path}"
        data = yaml.safe_load(golden_path.read_text(encoding="utf-8"))
        golden = GoldenScenarioModel.model_validate(data)
        assert golden.schema_version == 1
        assert golden.tenant_slug == "tenant_coach_lat"
        assert golden.persona_kind == "happy"
