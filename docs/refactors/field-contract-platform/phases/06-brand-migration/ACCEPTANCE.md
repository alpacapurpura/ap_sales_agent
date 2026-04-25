# Fase 06 — ACCEPTANCE (DoD per sub-step)

> Cada sub-step = 1 commit atómico revertible. Conventional Commits scope
> `refactor-field-contract-platform`. Stage por nombre. No tocar archivos
> ajenos.

## 06.A — docs alignment + golden brand snapshot

**Subject**: capturar baseline brand snapshot pre-refactor + docs.

**Touch**:
- `docs/refactors/field-contract-platform/phases/06-brand-migration/PRE_INVESTIGATION.md` (resultado pre-investigación).
- `docs/refactors/field-contract-platform/phases/06-brand-migration/ACCEPTANCE.md` (este file).
- `docs/refactors/field-contract-platform/phases/06-brand-migration/STATUS.md` (open).
- `backend/tests/architecture/test_brand_editable_fields_baseline.py` (golden
  snapshot — set de paths que catalog actual emite, congelado pre-refactor).

**DoD**:
- [ ] Docs commit aislado.
- [ ] Golden snapshot test corre + pasa contra catalog actual (78 entries).

**Expected diff post-refactor**: el snapshot baseline expone paths
shorthand broken (drift A/B). Tras 06.D la catalog cambiará. Snapshot
se actualiza en 06.D con assert que los nuevos paths son superset de
los working hoy + drop sólo de broken paths.

## 06.B — generic platform tests pre-brand

**Subject**: extender platform tests genéricos para que `brand` se enchufe
con 1 entry.

**Touch**:
- `backend/tests/architecture/test_field_contract_platform_module_template.py`:
  agregar `_brand_spec()` builder, registrarlo en `_build_module_registry()`
  cuando `MIGRATED_MODULES` lo incluya.

**No-op hasta 06.E** (porque MIGRATED_MODULES sigue `("offer",)`). Test
existe pero parametrize sólo corre para `offer`.

**DoD**:
- [ ] Spec function listo + import lazy de BrandSettings.
- [ ] Tests verde sin cambios visible runtime (offer-only run).

## 06.C — brand FieldContract module

**Subject**: implementar `brand/domain/field_contract.py` con
`BRAND_SECTION_MAP` + `BRAND_FIELD_OVERRIDES` + `derive_contracts_from_pydantic`
+ `register_module_contracts("brand", ...)`.

**Touch**:
- `backend/src/modules/brand/domain/field_contract.py` (new).

**Contenido**:
- `BRAND_IGNORE_PATHS` (BaseEntity audit + legacy deprecates).
- `BRAND_COMPOSABLE_FIELDS = (9 composables)`.
- `BRAND_SECTION_MAP: dict[str, str]` cubriendo los 113 paths derivables.
- `BRAND_FIELD_OVERRIDES: dict[str, FieldContractOverride]` con
  `human_question_es`, `label_es`, `priority`, `can_propose=False` para
  visuals derivative tokens.
- `BRAND_FIELD_CONTRACTS = derive_contracts_from_pydantic(...)`.
- `register_module_contracts("brand", BRAND_FIELD_CONTRACTS)`.
- `_LAZY_REGISTRARS["brand"] = "src.modules.brand.domain.field_contract"`
  (en `shared/domain/field_contract.py` o module-level side-effect).

**DoD**:
- [ ] Importar `brand/domain/field_contract` registra contracts en platform.
- [ ] `get_module_contracts("brand")` no-empty.
- [ ] Cada path tiene section asignada (no None).
- [ ] Existing tests siguen verde.

## 06.D — BRAND_EDITABLE_FIELDS proyectado

**Subject**: `copilot_editable_fields.py` brand re-write proyecta del
registry. Drop entradas hand-written.

**Touch**:
- `backend/src/modules/brand/domain/copilot_editable_fields.py`.

**Contenido**:
- Drop tuples `_IDENTITY/_STORY/...`.
- `BRAND_EDITABLE_FIELDS = tuple(FieldSpec(c.path, c.label_es or _label_from_section(c), c.section, c.notes or c.human_question_es) for c in get_module_contracts("brand") if c.can_propose and c.status == FieldStatus.ACTIVE)`.
- `register_catalog("brand", BRAND_EDITABLE_FIELDS)` mantenido.
- Update golden baseline test 06.A — assertions:
  - Working paths viejos ⊆ paths nuevos.
  - Broken shorthand paths NO aparecen en nuevos.
  - Catalog post-refactor expande para cubrir Pydantic real.

**DoD**:
- [ ] Catalog emite paths derivados.
- [ ] Sin manual hardcoded entries.
- [ ] Tests baseline + arch siguen verde.

## 06.E — MIGRATED_MODULES bumped

**Subject**: agregar `"brand"` a `MIGRATED_MODULES`. Las 5 fitness gates
genéricas (04.I) corren para brand automáticamente.

**Touch**:
- `backend/tests/architecture/test_field_contract_platform_coverage.py`:
  `MIGRATED_MODULES = ("offer", "brand")`.
- `backend/tests/architecture/test_field_contract_platform_module_template.py`:
  registrar `_brand_spec()` en `_build_module_registry()`.

**DoD**:
- [ ] `test_module_has_non_empty_registry` pasa para brand.
- [ ] `test_module_contracts_have_owner_module_set` pasa.
- [ ] `test_module_contracts_have_section` pasa.
- [ ] `test_module_contract_paths_unique` pasa.
- [ ] `test_module_editable_paths_subset_of_registry` pasa para brand.
- [ ] `test_module_pydantic_subset_of_registry` pasa.
- [ ] Test específico `test_brand_pydantic_subset_of_field_contract` agregado.

## 06.F — tech debt en scope

**Subject**: cualquier deuda atajada por la migración. A definir según
hallazgos durante 06.C-E.

**Hallazgos esperados**:
- Anti-regression: arch test prohíbe re-introducir manual `_IDENTITY/_STORY/...`
  tuples en brand catalog file (similar a OFFER_FIELDS_BY_FE_SECTION ratchet).
- Documentar en LEARNINGS los 3 tipos de drift cerrado.

**DoD**:
- [ ] Arch test anti-regression brand catalog (0 hand-written FieldSpec en module).
- [ ] LEARNINGS Fase 06 inicial (drift catalog, walker brand, decisión
  composable).

## 06.G — close fase

**Subject**: cierre + handoff Fase 07.

**Touch**:
- `docs/refactors/field-contract-platform/STATE.md`: `active_phase=07`,
  bump `last_green_commit`.
- `docs/refactors/field-contract-platform/phases/06-brand-migration/STATUS.md`:
  status=done.
- `docs/refactors/field-contract-platform/phases/07-buyer-persona-migration/STATUS.md`:
  ready-to-start (crear si no existe).
- `docs/refactors/field-contract-platform/LEARNINGS.md`: append Fase 06.
- `docs/refactors/field-contract-platform/HANDOFF.md`: prompt Fase 07.

**DoD**:
- [ ] POST_FLIGHT.md ejecutado verde.
- [ ] Tests verde end-to-end (BE arch + BE full + FE arch + ruff).
- [ ] STATE/STATUS/LEARNINGS/HANDOFF actualizados.
- [ ] Prompt Fase 07 entregado al user.
