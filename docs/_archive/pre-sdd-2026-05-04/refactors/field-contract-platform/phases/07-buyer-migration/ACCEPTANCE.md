# Fase 07 — Buyer-persona migration · ACCEPTANCE

## Goal recap

`BUYER_PERSONA_EDITABLE_FIELDS` proyectado de un nuevo `BUYER_PERSONA_FIELD_CONTRACTS` derivado de `BuyerPersona` Pydantic + dict_subkeys. UX byte-identical (12 entries propuestos) + cobertura `Pydantic ⊆ FieldContract`. Walker shared extiende con `dict_subkeys` arg (Patrón B).

## Sub-steps + DoD

### 07.A · golden snapshot + ACCEPTANCE

- Capturar baseline `BUYER_PERSONA_EDITABLE_FIELDS_BASELINE` (12 entries, paths + labels) en `tests/architecture/test_buyer_persona_editable_fields_baseline.py`.
- Capturar `WORKING_PATHS_BASELINE` ⊆ `validate_field_path("buyer_persona", path)`.
- Escribir este `ACCEPTANCE.md`.
- DoD: 1 commit `test(arch): buyer-persona catalog baseline + ACCEPTANCE`. Test pasa GREEN sobre el código actual (catalog legacy intacto).

### 07.B · walker `dict_subkeys` arg en shared

- Extender `derive_contracts_from_pydantic` con `dict_subkeys: dict[str, tuple[str, ...]] | None = None`.
- Cuando `fname in dict_subkeys`: walker emite contract por sub-key con path `"{fname}.{subkey}"`, type TEXT default, is_required_structural=False, lookup section en `section_map`. Parent se trata como composable handle (no emite bare).
- Tests platform unit: 4-5 casos cubriendo dict_subkeys con/sin override + interacción con composable_fields.
- DoD: 1 commit `feat(shared): walker dict_subkeys arg para JSONB sub-keys`. Tests GREEN. 471+ arch tests, no regresión offer/brand.

### 07.C · buyer-persona FieldContract module

- Crear `backend/src/modules/brand/domain/buyer_persona_field_contract.py`:
  - `BUYER_PERSONA_DICT_SUBKEYS: dict[str, tuple[str, ...]]` para demographics/psychographics/buyer_journey.
  - `BUYER_PERSONA_IGNORE_PATHS: frozenset[str]` (id, tenant_id, user_id, scope, offer_id, is_primary, is_active, deleted_at, created_at, updated_at, completeness_score).
  - `BUYER_PERSONA_SECTION_MAP: dict[str, str]` 18 entries: 2 identity + 4 demographics + 3 psychographics + 3 journey + 6 lists.
  - `BUYER_PERSONA_FIELD_OVERRIDES: dict[str, Override]`: 12 con `label_es` + `notes` (byte-identical descriptions); 6 con `can_propose=False` para list fields no-surface.
  - `BUYER_PERSONA_FIELD_CONTRACTS = derive_contracts_from_pydantic(...)`.
  - `register_module_contracts("buyer_persona", BUYER_PERSONA_FIELD_CONTRACTS)`.
- Bump `_LAZY_REGISTRARS["buyer_persona"] = "src.modules.brand.domain.buyer_persona_field_contract"`.
- DoD: 1 commit `refactor(buyer-persona): FieldContract registry derivado de BuyerPersona`. Module importable. `get_module_contracts("buyer_persona")` retorna ≥18 contracts.

### 07.D · BUYER_PERSONA_EDITABLE_FIELDS proyectado

- Reescribir `brand/domain/copilot_editable_fields_buyer_persona.py`:
  - Drop tuples `_IDENTITY/_DEMOGRAPHICS/_PSYCHOGRAPHICS/_JOURNEY` (manual).
  - `_build_editable_fields()` proyecta de `BUYER_PERSONA_FIELD_CONTRACTS` (filtra `can_propose=True` + `status=ACTIVE`).
  - `_to_field_spec(c)` mapea `label = c.label_es or _humanize(c.path)`, `description = c.human_question_es or c.notes`.
  - `register_catalog("buyer_persona", BUYER_PERSONA_EDITABLE_FIELDS)`.
- DoD: 1 commit `refactor(buyer-persona): proyectar BUYER_PERSONA_EDITABLE_FIELDS desde el registry`. Catalog 12 paths (byte-identical). Labels preservados. `test_buyer_persona_editable_fields_baseline.py` GREEN.

### 07.E · MIGRATED_MODULES bump + Pydantic ⊆ contract

- En `tests/architecture/test_field_contract_platform_coverage.py`:
  - `MIGRATED_MODULES = ("offer", "brand", "buyer_persona")`.
  - Helper `_all_buyer_persona_pydantic_paths()` que produce paths esperados (top-level minus IGNORE minus dict_subkey parents + dict_subkey sub-keys).
  - Test `test_buyer_persona_model_fields_subset_of_field_contract`.
  - Test `test_buyer_persona_section_map_covers_every_pydantic_path` (mirror brand).
- En `tests/architecture/test_field_contract_platform_module_template.py`:
  - `_buyer_persona_spec()` con `composable_handles = frozenset({"demographics", "psychographics", "buyer_journey"})`.
  - Append a `_build_module_registry()` y `_MIGRATED_SPECS`.
- DoD: 1 commit `test(arch): MIGRATED_MODULES bump buyer_persona + buyer pydantic coverage`. Generic guards corren para 3 módulos. 471 → ≥480 arch tests.

### 07.F · anti-regression buyer-persona ratchet

- Crear `tests/architecture/test_buyer_persona_catalog_projection.py` (mirror `test_brand_catalog_projection.py`):
  - `test_catalog_equals_proposable_subset_of_registry`.
  - `test_catalog_section_matches_contract_section`.
  - `test_buyer_persona_catalog_file_has_no_inline_field_spec_tuples` (ratchet — solo 1 `FieldSpec(` call permitido en `_to_field_spec`).
  - `test_buyer_persona_catalog_file_imports_field_contracts`.
- DoD: 1 commit `test(arch): buyer-persona catalog anti-regression — projection mandatoria`. Tests GREEN.

### 07.G · close phase + handoff Fase 08

- Ejecutar `protocol/POST_FLIGHT.md`.
- `STATE.md`: bump `last_green_commit`, `active_phase=08-copilot-unification`, `sub_step=0/?`.
- `phases/07-buyer-migration/STATUS.md`: `status: done`, `closed_at`, hashes per sub-step.
- `phases/08-copilot-unification/STATUS.md`: `status: ready-to-start`, `baseline_green_commit`.
- `LEARNINGS.md`: append §Fase 07 (pre-fase vs realidad, métricas, descubrimientos walker dict_subkeys, deuda técnica).
- `HANDOFF.md`: prompt completo para Fase 08.
- DoD: 1 commit `chore(refactor-field-contract-platform): close Fase 07 + handoff Fase 08`. STATE coherente. Generar prompt para próxima sesión.

## Reglas atómicas

- Cada commit revertible. Branch `development`. Stage por nombre. Ajenos intactos.
- Spanish neutro LATAM en cualquier `human_question_es` / `notes` user-facing.
- TDD: tests primero (07.A baseline, 07.B walker tests). Implementación después.
- UX byte-identical: 12 catalog entries pre-fase = 12 catalog entries post-fase, mismos labels.
- No reabrir Fase 04/05/06.

## Out of scope

- Migración del validator legacy `_build_buyer_persona_paths` (Fase 08 copilot unification).
- Drop de `BuyerPersona` model en módulo BE separado.
- Cambios en FE schema `buyer-persona.schema.ts`.
- Sub-keys de list[dict] (`pain_points.emotional_impact`, `desires.urgency`) — no son JSONB-dict-parent, requieren walker extension diferente. Diferido.
