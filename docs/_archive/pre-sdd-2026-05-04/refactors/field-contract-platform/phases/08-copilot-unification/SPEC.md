# Fase 08 — Copilot unification · SPEC

## Objetivo

Eliminar duplicación interna del copilot. `editable_fields` port +
`schema_introspection._build_*_paths` consumen `FieldContract`
cross-module en lugar de boilerplate paralelo.

Métrica concreta: 3 archivos `copilot_editable_fields*.py` (boilerplate
projection idéntica) eliminados, port deriva via `get_module_contracts`.
Cero drift Pydantic ↔ catalog ↔ validator por construcción.

## Scope dentro

### Cambio 1 — `shared/links/ports/editable_fields.py` deriva

- Nuevo helper interno `_derive_from_contracts(domain)` que proyecta
  `get_module_contracts(domain)` → `tuple[FieldSpec, ...]` con filtros
  `can_propose=True` + `status=ACTIVE` y dedupe por `path`.
- `get_catalog(domain)`:
  1. Si hay registro explícito en `_CATALOGS` (test stub o seed) → return.
  2. Si no, deriva via `_derive_from_contracts(domain)` y cachea.
- `get_registered_domains()` deriva de `get_all_modules()` (FieldContract
  registry). Domains con catalog vacío excluidos.
- `register_catalog(domain, fields)` API mantenida (test stubs + casos
  de override custom). Documenta que la default es derivación.
- Drop `_KNOWN_DOMAINS` + `_lazy_register` interno (la lazy-load corre
  en `field_contract._LAZY_REGISTRARS`, transitivamente).

### Cambio 2 — Drop 3 catalog projection files

Boilerplate idéntico. Reemplazado por la derivación del port.

- `backend/src/modules/brand/domain/copilot_editable_fields.py` → drop.
- `backend/src/modules/brand/domain/copilot_editable_fields_buyer_persona.py` → drop.
- `backend/src/modules/offer/domain/copilot_editable_fields.py` → drop.

Anti-regression test (sub-step 08.D): ningún módulo migrado puede
re-introducir un `copilot_editable_fields*.py` con `register_catalog`.

### Cambio 3 — `schema_introspection._build_*_paths` deriva

- `_build_offer_paths()` →
  `{c.path for c in get_module_contracts("offer")}`. Drop import desde
  `offer_fields.PERSISTABLE_FIELDS` (mantiene equivalencia matemática).
- `_build_brand_paths()` →
  `{c.path for c in contracts} | {c.section for c in contracts}`.
  Preserva validación de bare section names ("identity", "story",
  "positioning", "narrative", "visuals"…) que tests assert.
- `_build_buyer_persona_paths()` →
  `{c.path for c in get_module_contracts("buyer_persona")}`. Drop
  hand-authored `top_level` + `dot_notation` sets (24 paths a mano).
- `_DOMAIN_DICT_PARENTS["buyer_persona"]` →
  `set(BUYER_PERSONA_DICT_SUBKEYS.keys())` (= mismo trío hoy: 
  `demographics`/`psychographics`/`buyer_journey`).

`_DOMAIN_FIELD_CACHE` cache mantenido (immutability del registry post-
bootstrap = cache válido).

`field_paths_hint.py:24` sigue importando `_DOMAIN_DICT_PARENTS` —
mantener la API privada (no breaking change).

### Cambio 4 — Anti-regression arch tests

3 tests nuevos en `backend/tests/architecture/`:

1. `test_editable_fields_derivation.py` — `get_catalog(domain)` para
   los 3 dominios migrados es **idéntico** a la projection manual de
   `get_module_contracts(domain)` con filtros (can_propose+ACTIVE).
   Detecta drift entre port deriving y projection esperada.
2. `test_no_catalog_projection_files.py` — ningún archivo bajo
   `backend/src/modules/{offer,brand,buyer_persona}/domain/` matchea
   pattern `copilot_editable_fields*.py`. Anti-regression del drop.
3. `test_schema_introspection_derives_from_registry.py` — los 3
   `_build_*_paths` no contienen literales de paths hand-authored
   (AST scan: no `set` literals con > N strings, fuerza derivation).

### Cambio 5 — `offer_fields.py` mantenido (decisión PRE_INVESTIGATION §5)

Sin cambio de código. Documentar en doc-string que `_build_offer_paths`
ya no lo consume (deriva de get_module_contracts directo). Mantenerlo
como alias para offer_persister + arch tests que lo enforzan.

## Scope fuera

- Multi-channel projection (Fase 09).
- Reescritura prompt copilot (UX intacta).
- FE schemas (INVARIANT 9).
- `get_model_sections` migration (out of scope per PRE_INVESTIGATION §2.2).
- Drop de `offer_fields.py` (out of scope per PRE_INVESTIGATION §5).
- Diferidos Fase 05 (data-driven loop full, completion alignment,
  landing aggregate migration).

## Riesgo

**Medio-alto**. Copilot está en producción. Tests acceptance exhaustivos
requeridos. Mitigaciones:

1. PRE_INVESTIGATION §1+§2+§3 documenta cada call site + comportamiento.
2. Cada sub-step revertible atómico.
3. Baseline arch tests (490 pass) capturado pre-fase. Post-fase ≥ 490 + nuevos.
4. Tests acceptance copilot existentes (test_editable_fields_integration,
   test_extract_validation, test_editable_fields_ssot, test_studio_snapshot_layer)
   pasan sin cambio.
5. Comportamiento `validate_field_path` y `propose_field_updates`
   preservado byte-identical (PRE_INVESTIGATION §2.1 + §3 listan
   assertions específicas).
6. UX byte-identical: system prompt enumeration y document extraction
   hint usan `get_catalog` que deriva idéntico a projection actual de
   los 3 catalog files.

## Sub-steps

| # | Subject | Commit |
|---|---|---|
| 08.A | docs: PRE_INVESTIGATION + SPEC + ACCEPTANCE Fase 08 | docs/refactor only |
| 08.B | refactor: `editable_fields` port deriva de `get_module_contracts` + drop 3 catalog projection files | port + drop 3 files |
| 08.C | refactor: `schema_introspection._build_*_paths` derivan del FieldContract registry | schema_introspection.py |
| 08.D | test(arch): anti-regression — derivation + drop catalog files + no hand-authored paths | 3 tests nuevos |
| 08.F | chore(close): LEARNINGS + STATE/STATUS bump + HANDOFF Fase 09 | docs/refactor close |

## DoD per sub-step

Detallado en [ACCEPTANCE.md](ACCEPTANCE.md).

## Decisiones documentadas (no nuevas ADRs — implementación de ADR-011..017)

- **Mantener `register_catalog` public API**: tests pueden stubbear.
  Default es derivación pero override sigue posible. Compatibility win.
- **`_DOMAIN_DICT_PARENTS` derivado, NO eliminado**: api privada usada
  por `field_paths_hint.py`. Cambiar shape rompería ese consumer.
- **Brand bare sections preservados via `| {c.section for c in contracts}`**:
  validate_field_path("brand", "identity") debe seguir True. Tests
  enforcing en `test_extract_validation.py`.
- **Offer paths puros (no bare sections)**: offer aggregate es flat,
  no tiene "section names" como paths válidos. Tests confirman.
- **Buyer paths puros (no bare dict_parents)**: dict_parents NO son
  paths válidos por sí mismos (ver schema_introspection.py:286-291).
  Sub-keys + prefix-match accept rule.
