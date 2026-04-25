# Fase 08 — Copilot unification · ACCEPTANCE

> Sub-step atómicos con DoD explícito. Cada uno = 1 commit revertible.

## 08.A — docs commit

**Subject sugerido**: `docs(refactor-field-contract-platform): Fase 08 PRE_INVESTIGATION + SPEC + ACCEPTANCE`

**Files**:
- `docs/refactors/field-contract-platform/phases/08-copilot-unification/PRE_INVESTIGATION.md`
- `docs/refactors/field-contract-platform/phases/08-copilot-unification/SPEC.md`
- `docs/refactors/field-contract-platform/phases/08-copilot-unification/ACCEPTANCE.md`
- `docs/refactors/field-contract-platform/phases/08-copilot-unification/STATUS.md` (sub_step bump)
- `docs/refactors/field-contract-platform/STATE.md` (last_updated + sub_step)

**DoD**:
- [ ] PRE_INVESTIGATION completo (8 secciones, todas sin TBD).
- [ ] SPEC con 5 cambios + scope fuera + riesgo + sub-steps.
- [ ] ACCEPTANCE este archivo con DoD per sub-step.
- [ ] STATUS Fase 08 `status: in_progress`, `opened_at: 2026-04-24`.
- [ ] STATE.md `sub_step: A/F`, `last_updated: 2026-04-24`.
- [ ] Baseline tests note: 490 arch tests pass (pre-Fase 08).

---

## 08.B — `editable_fields` port deriva + drop 3 catalog files

**Subject sugerido**: `refactor(copilot): editable_fields port deriva de FieldContract platform`

**Files modificados**:
- `backend/src/shared/links/ports/editable_fields.py` (rewrite con derivation default)

**Files dropped**:
- `backend/src/modules/brand/domain/copilot_editable_fields.py`
- `backend/src/modules/brand/domain/copilot_editable_fields_buyer_persona.py`
- `backend/src/modules/offer/domain/copilot_editable_fields.py`

**Cambios al port**:
1. Nuevo helper `_humanize(name)` (movido del catalog file, idéntico).
2. Nuevo helper `_derive_from_contracts(domain) -> tuple[FieldSpec, ...]`.
3. `get_catalog(domain)` deriva por default si no hay registro explícito.
4. `get_registered_domains()` consume `get_all_modules()` del field_contract.
5. Drop `_KNOWN_DOMAINS` + `_lazy_register` interno.
6. `register_catalog` mantiene API (test stubs).

**DoD**:
- [ ] `cd backend && .venv/bin/pytest tests/architecture/ -q --tb=no` ≥ 490 pass.
- [ ] `cd backend && .venv/bin/pytest tests/modules/copilot/test_editable_fields_integration.py tests/modules/copilot/test_extract_validation.py tests/modules/copilot/test_studio_snapshot_layer.py -v` GREEN sin cambios.
- [ ] `len(get_catalog("offer"))` byte-identical pre/post (espera: igual count que `OFFER_EDITABLE_FIELDS` pre-fase).
- [ ] `len(get_catalog("brand"))` byte-identical pre/post.
- [ ] `len(get_catalog("buyer_persona"))` byte-identical pre/post.
- [ ] `get_registered_domains()` retorna `("brand", "buyer_persona", "offer")` (sorted).
- [ ] `propose_field_updates` smoke: invocación con field_id válido + inválido funciona idéntico.
- [ ] Lint + format clean: `cd backend && .venv/bin/ruff check src/shared/links src/modules/copilot src/modules/brand src/modules/offer` y `ruff format --check`.

---

## 08.C — `schema_introspection._build_*_paths` derivan

**Subject sugerido**: `refactor(copilot): schema_introspection._build_*_paths derivan de FieldContract registry`

**Files modificados**:
- `backend/src/modules/copilot/domain/schema_introspection.py`

**Cambios**:
1. `_build_offer_paths()` → `{c.path for c in get_module_contracts("offer")}` (drop import desde `offer_fields`).
2. `_build_brand_paths()` → `{c.path for c in contracts} | {c.section for c in contracts}` (drop `get_model_sections(BrandSettings)`).
3. `_build_buyer_persona_paths()` → `{c.path for c in get_module_contracts("buyer_persona")}` (drop hand-authored set).
4. `_DOMAIN_DICT_PARENTS["buyer_persona"]` → `set(BUYER_PERSONA_DICT_SUBKEYS.keys())` (derived constant).

**DoD**:
- [ ] `cd backend && .venv/bin/pytest tests/modules/copilot/test_extract_validation.py -v` GREEN — todas las assertions del test (boundary `validate_field_path` cases) pasan idénticas.
- [ ] `cd backend && .venv/bin/pytest tests/architecture/test_brand_editable_fields_baseline.py tests/architecture/test_buyer_persona_editable_fields_baseline.py -v` GREEN.
- [ ] `validate_field_path("brand", "identity")` → True (bare section preservada).
- [ ] `validate_field_path("buyer_persona", "demographics.marital_status")` → True (prefix match preservado).
- [ ] `validate_field_path("buyer_persona", "purchase_triggers")` → True (top-level path).
- [ ] `field_paths_hint.build_field_paths_hint("buyer_persona")` produce same output (smoke check via `python -c`).
- [ ] Lint + format clean.

---

## 08.D — anti-regression arch tests

**Subject sugerido**: `test(arch): editable_fields derivation + no catalog projection files + no hand-authored paths`

**Files nuevos**:
- `backend/tests/architecture/test_editable_fields_derivation.py`
- `backend/tests/architecture/test_no_catalog_projection_files.py`
- `backend/tests/architecture/test_schema_introspection_derives_from_registry.py`

**Tests específicos**:

### `test_editable_fields_derivation.py`

```python
def test_get_catalog_matches_field_contract_projection():
    """Para cada módulo migrado, get_catalog deriva idéntico a la
    projection manual de get_module_contracts con filtros + dedupe."""
    for module in ("offer", "brand", "buyer_persona"):
        derived = _project_manually(get_module_contracts(module))
        from_port = get_catalog(module)
        assert derived == from_port

def test_get_catalog_filters_by_can_propose_and_active():
    """can_propose=False o status!=ACTIVE excluidos de get_catalog."""
    for c in get_module_contracts("buyer_persona"):
        if not c.can_propose or c.status != FieldStatus.ACTIVE:
            assert c.path not in get_paths_for("buyer_persona")
```

### `test_no_catalog_projection_files.py`

```python
def test_no_module_has_copilot_editable_fields_file():
    """Anti-regression del drop. Ningún módulo migrado puede re-introducir
    archivo `copilot_editable_fields*.py` con register_catalog."""
    forbidden = list(Path("backend/src/modules").rglob("copilot_editable_fields*.py"))
    assert forbidden == [], (
        f"Found re-introduced catalog projection files: {forbidden}. "
        "Catalogs derive from FieldContract registry via shared port (Fase 08)."
    )
```

### `test_schema_introspection_derives_from_registry.py`

```python
def test_build_offer_paths_imports_get_module_contracts():
    """AST: _build_offer_paths consume get_module_contracts."""

def test_build_brand_paths_imports_get_module_contracts():
    """AST: _build_brand_paths consume get_module_contracts (no más
    get_model_sections con literal BrandSettings)."""

def test_build_buyer_persona_paths_imports_get_module_contracts():
    """AST: _build_buyer_persona_paths consume get_module_contracts.
    No hand-authored set literals con > 5 strings."""

def test_domain_dict_parents_buyer_persona_derived_from_subkeys():
    """_DOMAIN_DICT_PARENTS['buyer_persona'] == BUYER_PERSONA_DICT_SUBKEYS.keys()."""
```

**DoD**:
- [ ] 3 archivos test creados, todos pass.
- [ ] `cd backend && .venv/bin/pytest tests/architecture/ -q --tb=no` ≥ 490 + nuevos = 493+.
- [ ] Anti-regression real: introducir un literal hand-authored en
  `_build_*_paths` debe romper test_schema_introspection_derives_from_registry.
- [ ] Anti-regression real: re-crear `copilot_editable_fields.py` en
  cualquier módulo migrado debe romper test_no_catalog_projection_files.

---

## 08.F — close phase

**Subject sugerido**: `chore(refactor-field-contract-platform): close Fase 08 + handoff Fase 09`

**Files modificados**:
- `docs/refactors/field-contract-platform/STATE.md`
  - `active_phase: 09-multi-channel-projection`
  - `last_updated: 2026-04-24`
  - `last_green_commit: <commit-hash-de-08.D>`
  - Historial Fase 08 entry.
- `docs/refactors/field-contract-platform/phases/08-copilot-unification/STATUS.md`
  - `status: done`, `closed_at: 2026-04-24`.
- `docs/refactors/field-contract-platform/LEARNINGS.md`
  - Append `## Fase 08` section: descubrimientos + métricas + para Fase 09.
- `docs/refactors/field-contract-platform/HANDOFF.md`
  - Update con prompt arrancar Fase 09.
- `docs/refactors/field-contract-platform/phases/09-multi-channel-projection/STATUS.md`
  - Crear si no existe, `status: ready-to-start`.

**DoD**:
- [ ] LEARNINGS.md Fase 08 con: pre-fase expectations vs realidad,
  resultados cuantitativos (count contracts, tests arch antes/después,
  archivos dropped), descubrimientos concretos, deuda técnica
  encontrada (en scope resuelta + tangencial), Para Fase 09.
- [ ] STATE.md `active_phase: 09`.
- [ ] STATUS Fase 08 `done`.
- [ ] STATUS Fase 09 `ready-to-start`.
- [ ] HANDOFF.md con prompt Fase 09 listo para pegar.
- [ ] POST_FLIGHT.md ejecutado: tests counts post-fase reportados.

---

## Reglas inquebrantables (invocadas en cada sub-step)

- INVARIANT 1 — Cero registries paralelos nuevos.
- INVARIANT 3 — Un concepto por commit.
- INVARIANT 4 — UX byte-identical.
- INVARIANT 5 — Arch tests ≥ baseline cada commit.
- INVARIANT 13 — Stage por nombre. No tocar ajenos.
- INVARIANT 14 — Spanish neutro LATAM (commit messages, docs).
- INVARIANT 15 — TDD: tests anti-regression escritos antes (08.D).
