"""Golden baseline for buyer-persona catalog — locks in pre/post-Fase-07 invariants.

Captured 2026-04-24 (sub-step 07.A) from
``BUYER_PERSONA_EDITABLE_FIELDS`` (legacy hand-written tuples) so the
Fase 07 migration can be validated as **byte-identical UX** (INVARIANT 4).

Post-Fase-07 the catalog must:

1. Project the same 12 paths from ``BUYER_PERSONA_FIELD_CONTRACTS``.
2. Preserve every Spanish label (system prompt enumeration intacto).
3. Preserve every description text (LLM context unchanged).
4. Continue to validate via
   ``schema_introspection.validate_field_path("buyer_persona", path)``.

refs: docs/refactors/field-contract-platform/phases/07-buyer-migration/PRE_INVESTIGATION.md
"""

from __future__ import annotations

from src.modules.brand.domain.copilot_editable_fields_buyer_persona import (
    BUYER_PERSONA_EDITABLE_FIELDS,
)
from src.modules.copilot.domain.schema_introspection import validate_field_path

# ---------------------------------------------------------------------------
# Baseline — frozen pre-Fase-07
# ---------------------------------------------------------------------------

# Every path that lives in the catalog right now, with its curated Spanish
# label + description. Fase 07 must preserve this exact projection (the
# copilot system prompt enumerates these — drift breaks UX).
"""Tuple shape: ``(path, section, label, description)``."""
BUYER_PERSONA_CATALOG_BASELINE: tuple[tuple[str, str, str, str], ...] = (
    (
        "name",
        "identity",
        "Nombre",
        "Nombre interno del avatar. Identifica la persona, no aparece al cliente.",
    ),
    (
        "tagline",
        "identity",
        "Tagline",
        "Una línea que describe quién es esta persona.",
    ),
    (
        "demographics.age_range",
        "demographics",
        "Rango etario",
        "Rango de edades del cliente ideal.",
    ),
    (
        "demographics.location",
        "demographics",
        "Ubicación",
        "Ciudad o región principal del avatar.",
    ),
    (
        "demographics.occupation",
        "demographics",
        "Ocupación",
        "Profesión o rol del cliente ideal.",
    ),
    (
        "demographics.income",
        "demographics",
        "Nivel de ingresos",
        "Rango de ingresos aproximado del avatar.",
    ),
    (
        "psychographics.values",
        "psychographics",
        "Valores centrales",
        "Principios que guían las decisiones del avatar.",
    ),
    (
        "psychographics.aspirations",
        "psychographics",
        "Aspiraciones",
        "A dónde quiere llegar este avatar.",
    ),
    (
        "psychographics.lifestyle",
        "psychographics",
        "Estilo de vida",
        "Cómo organiza su día y qué consume.",
    ),
    (
        "buyer_journey.awareness",
        "journey",
        "Etapa de awareness",
        "Cómo descubre que tiene un problema o que existes.",
    ),
    (
        "buyer_journey.consideration",
        "journey",
        "Etapa de consideración",
        "Cómo evalúa opciones antes de decidir.",
    ),
    (
        "buyer_journey.decision",
        "journey",
        "Etapa de decisión",
        "Qué lo lleva al sí final.",
    ),
)


WORKING_PATHS_BASELINE: frozenset[str] = frozenset(p for p, *_ in BUYER_PERSONA_CATALOG_BASELINE)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestBuyerPersonaCatalogBaseline:
    """Pre-Fase-07 catalog shape — must remain byte-identical post-migration."""

    def test_catalog_entry_count(self) -> None:
        """Catalog has exactly 12 entries pre-Fase-07."""
        assert len(BUYER_PERSONA_EDITABLE_FIELDS) == len(BUYER_PERSONA_CATALOG_BASELINE), (
            f"Catalog size drifted: expected {len(BUYER_PERSONA_CATALOG_BASELINE)}, "
            f"got {len(BUYER_PERSONA_EDITABLE_FIELDS)}."
        )

    def test_catalog_paths_match_baseline(self) -> None:
        """Every baseline path is present in the catalog."""
        catalog_paths = {f.path for f in BUYER_PERSONA_EDITABLE_FIELDS}
        baseline_paths = {p for p, *_ in BUYER_PERSONA_CATALOG_BASELINE}
        diff = catalog_paths.symmetric_difference(baseline_paths)
        assert not diff, (
            f"BUYER_PERSONA_EDITABLE_FIELDS path drift.\n"
            f"In catalog only: {sorted(catalog_paths - baseline_paths)}\n"
            f"In baseline only: {sorted(baseline_paths - catalog_paths)}"
        )

    def test_catalog_labels_preserved(self) -> None:
        """Spanish labels survive any projection refactor."""
        catalog_by_path = {f.path: f.label for f in BUYER_PERSONA_EDITABLE_FIELDS}
        mismatches: list[str] = []
        for path, _section, expected_label, _desc in BUYER_PERSONA_CATALOG_BASELINE:
            actual = catalog_by_path.get(path)
            if actual != expected_label:
                mismatches.append(f"{path}: expected {expected_label!r}, got {actual!r}")
        assert not mismatches, "Label drift in catalog:\n  " + "\n  ".join(mismatches)

    def test_catalog_sections_preserved(self) -> None:
        """Section assignments survive any projection refactor."""
        catalog_by_path = {f.path: f.section for f in BUYER_PERSONA_EDITABLE_FIELDS}
        mismatches: list[str] = []
        for path, expected_section, _label, _desc in BUYER_PERSONA_CATALOG_BASELINE:
            actual = catalog_by_path.get(path)
            if actual != expected_section:
                mismatches.append(f"{path}: expected {expected_section!r}, got {actual!r}")
        assert not mismatches, "Section drift in catalog:\n  " + "\n  ".join(mismatches)

    def test_catalog_descriptions_preserved(self) -> None:
        """Descriptions survive — they ride into the LLM system prompt."""
        catalog_by_path = {f.path: f.description for f in BUYER_PERSONA_EDITABLE_FIELDS}
        mismatches: list[str] = []
        for path, _section, _label, expected_desc in BUYER_PERSONA_CATALOG_BASELINE:
            actual = catalog_by_path.get(path)
            if actual != expected_desc:
                mismatches.append(f"{path}: expected {expected_desc!r}, got {actual!r}")
        assert not mismatches, "Description drift in catalog:\n  " + "\n  ".join(mismatches)


class TestBuyerPersonaCatalogValidatorAgreement:
    """The 12 catalog paths all validate against the schema introspection.

    Confirms every catalog entry is currently driveable by
    ``propose_field_updates`` — Fase 07 must not break any of them.
    """

    def test_working_paths_validate(self) -> None:
        invalid = sorted(p for p in WORKING_PATHS_BASELINE if not validate_field_path("buyer_persona", p))
        assert not invalid, (
            f"Catalog paths rejected by validate_field_path: {invalid}. "
            f"Pre-Fase-07 the catalog and validator agreed — investigate."
        )
