# Pre-investigación obligatoria — Fase 08

> Inventario sin hacks: cada call site verificado con grep + Read.
> ADR-017: bloqueante antes del primer Write/Edit en código.

## Estado de partida

- Branch: `development`
- Last green commit: `1f210a5d` (close Fase 07)
- 3 módulos migrados al FieldContract platform: offer + brand + buyer_persona.
- 490 arch tests pass · 4286+ BE tests pass.
- Working tree limpio (3 archivos ajenos listados en STATE.md).

---

## §1 — Call sites de `editable_fields` port

### 1.1 — `get_catalog(domain)`

| Archivo | Línea | Uso | Shape consumido |
|---|---|---|---|
| `shared/links/ports/editable_fields.py` | 71 | definición | — |
| `shared/links/ports/editable_fields.py` | 101 | `get_paths_for(domain)` interno | `f.path` |
| `copilot/domain/field_paths_hint.py` | 85 | `build_field_paths_hint(domain)` para extraction prompt | `path`, `label`, `section`, `description` (group_by_section + render markdown) |
| `copilot/domain/schema_introspection.py` | 409 | `is_editable_path` | `f.path` |
| `copilot/domain/schema_introspection.py` | 428 | `format_editable_field_catalog_markdown` | `path`, `label`, `section`, `description` |
| `copilot/application/guided/block_generator.py` | 84 | guided interview block builder | catalog completo |
| `copilot/application/orchestrator/graph.py` | 311 | `_render_studio_snapshot` | `path` (filled vs empty) |
| `tests/architecture/test_editable_fields_ssot.py` | 36, 39, 42, 54, 63, 84 | aserts catalog ≥ 1 | shape FieldSpec entero |
| `tests/modules/copilot/test_editable_fields_integration.py` | 16-58, 191 | unit tests por dominio | `path`, `description`, asdict |
| `tests/modules/copilot/test_studio_snapshot_layer.py` | 143 | mock `graph.get_catalog` | mock |

**Conclusión**: shape esperado es `tuple[FieldSpec(path, label, section, description=None), ...]`. La projection FieldContract → FieldSpec ya implementada idéntica en los 3 catalog files de módulos migrados — extraerla al port produce el mismo output byte-identical.

### 1.2 — `get_paths_for(domain)`

| Archivo | Línea | Uso |
|---|---|---|
| `copilot/application/tools/mutations.py` | 18, 31 | `_guess_domain` para `propose_field_updates` |
| `tests/architecture/test_field_contract_platform_module_template.py` | 59-109 | platform fitness gates |
| `tests/architecture/test_editable_fields_ssot.py` | 71-72 | per-domain path validation |
| `tests/modules/copilot/test_editable_fields_integration.py` | 175-180 | uniqueness + non-empty |

**Crítico — `propose_field_updates` flow**:
1. LLM tool invoca `propose_field_updates(updates=[{field_id, new_value, ...}])`.
2. Para cada update: `_guess_domain(field_id)` itera `get_registered_domains()` y chequea `field_id in get_paths_for(domain)`.
3. Match → validated. No match → rejected con structured error.

Post-Fase 08: el set de paths sigue idéntico (FieldSpec.path se preserva), `propose_field_updates` se mantiene sin tocar.

### 1.3 — `get_registered_domains()`

| Archivo | Línea | Uso |
|---|---|---|
| `copilot/domain/schema_introspection.py` | 23, 447 | `format_all_editable_catalogs_markdown` |
| `copilot/application/tools/mutations.py` | 18, 30, 76 | `_guess_domain` + error message |
| `tests/architecture/test_editable_fields_ssot.py` | 45, 53, 62, 71, 83 | enum de dominios para tests |
| `tests/modules/copilot/test_editable_fields_integration.py` | 60-63 | aserts |

Post-Fase 08: deriva de `get_all_modules()` del field_contract registry, comportamiento idéntico para los 3 dominios migrados.

### 1.4 — `register_catalog(domain, fields)`

| Archivo | Línea | Uso |
|---|---|---|
| `shared/links/ports/editable_fields.py` | 61 | definición |
| `brand/domain/copilot_editable_fields.py` | 89 | bootstrap brand |
| `brand/domain/copilot_editable_fields_buyer_persona.py` | 87 | bootstrap buyer_persona |
| `offer/domain/copilot_editable_fields.py` | 88 | bootstrap offer |

Post-Fase 08: API queda para tests-stub. Los 3 callers de bootstrap se eliminan junto con sus archivos (catalogs ahora derivan auto).

---

## §2 — Call sites de `schema_introspection`

### 2.1 — `validate_field_path(domain, path)`

| Archivo | Línea | Uso |
|---|---|---|
| `copilot/application/tools/guided/extract.py` | 24, 107 | `extract_structured` tool — silent per-turn extractor |
| `tests/architecture/test_brand_editable_fields_baseline.py` | 23, 270, 283 | working/broken paths baseline |
| `tests/architecture/test_buyer_persona_editable_fields_baseline.py` | 23, 177 | working paths baseline |
| `tests/modules/copilot/test_extract_validation.py` | 5, 13-108 | unit tests críticos |

**Comportamiento que se debe preservar byte-identical** (assertions clave del test_extract_validation):
- `validate_field_path("brand", "identity.brand_name")` → True (path en contract)
- `validate_field_path("brand", "identity")` → True (**bare section** — necesita tratamiento especial post-derivation)
- `validate_field_path("brand", "story")` → True (bare section)
- `validate_field_path("brand", "positioning")` → True (bare section)
- `validate_field_path("brand", "narrative")` → True (bare section)
- `validate_field_path("brand", "visuals")` → True (bare section)
- `validate_field_path("brand", "nonexistent_section.fake_field")` → False
- `validate_field_path("offer", "public_name")` → True
- `validate_field_path("offer", "headline_promise")` → True
- `validate_field_path("offer", "id")` → False (ignored path)
- `validate_field_path("buyer_persona", "demographics.age_range")` → True (exact)
- `validate_field_path("buyer_persona", "demographics.marital_status")` → True (**prefix match** — dict_parent)
- `validate_field_path("buyer_persona", "psychographics.hobbies")` → True (prefix match)
- `validate_field_path("buyer_persona", "buyer_journey.post_purchase")` → True (prefix match)
- `validate_field_path("buyer_persona", "name")` → True
- `validate_field_path("buyer_persona", "pain_points")` → True (top_level list)
- `validate_field_path("buyer_persona", "purchase_triggers")` → True
- `validate_field_path("unknown_domain", "any.field")` → False

**Conclusión derivación** post-Fase 08:
- `_build_offer_paths` → `{c.path for c in get_module_contracts("offer")}`. Drop import desde `offer_fields.py`.
- `_build_brand_paths` → `{c.path for c in contracts} | {c.section for c in contracts}` — la unión preserva validación de bare section names que `get_model_sections(BrandSettings)` emite hoy.
- `_build_buyer_persona_paths` → `{c.path for c in get_module_contracts("buyer_persona")}`. Drop hand-authored set.
- `_DOMAIN_DICT_PARENTS["buyer_persona"]` → derivado de `set(BUYER_PERSONA_DICT_SUBKEYS.keys())`.

### 2.2 — `get_model_sections(model_class)`

Pydantic introspection helper, **operates on a Pydantic model, NOT on a domain string**. Uso:

| Archivo | Línea | Uso |
|---|---|---|
| `admin/modules/tenant_health.py` | 20, 37, 233, 254 | admin panel completion view |
| `copilot/application/tools/module_tools.py` | 19, 170 | LLM module data tool |
| `copilot/application/tools/awareness.py` | 22, 45 | nudge awareness |
| `copilot/application/orchestrator/graph.py` | 54, 69 | brand snapshot completion |
| `copilot/application/procedures/base.py` | 16, 90 | procedure step context |
| `copilot/api/nudge.py` | 21, 44 | nudge API |
| `copilot/domain/schema_introspection.py` | 253 (interno `_build_brand_paths`) | — |

**Decisión scope Fase 08**: `get_model_sections` permanece como Pydantic introspector. NO se intenta derivarlo de `FieldContract` registry — los consumers (admin, awareness, nudge, procedures) requieren shape estructural Pydantic-driven (sub_fields, field_descriptions con descripciones de Pydantic Field). Migrar esto al contract registry es **out of scope** (probable Fase 09+ cuando el contract incluya `description` rich) — `get_model_sections` no tiene drift con FieldContract porque opera 1:1 sobre Pydantic, lo mismo que el walker.

### 2.3 — `is_editable_path(domain, path)`

| Archivo | Línea | Uso |
|---|---|---|
| `schema_introspection.py` | 400 | definición — consume `get_catalog(domain)` |

Único call site interno para format markdown. Post-Fase 08 sigue idéntico (consume el catalog que ahora deriva).

### 2.4 — `format_editable_field_catalog_markdown` / `format_all_editable_catalogs_markdown`

| Archivo | Línea | Uso |
|---|---|---|
| `schema_introspection.py` | 420, 441 | definición |
| `copilot/application/orchestrator/graph.py` | 490, 493 | system prompt builder |
| `tests/modules/copilot/test_editable_fields_integration.py` | 151-168 | smoke |

Sin cambio. Consume `get_catalog` post-Fase 08.

---

## §3 — Flujo `propose_field_updates`

```
LLM emite tool call
    │
    ▼
propose_field_updates(updates=[{field_id, new_value, reason}])
    │
    ▼
_guess_domain(field_id) →
    for domain in get_registered_domains():       # editable_fields port
        if field_id in get_paths_for(domain):     # editable_fields port → FieldSpec.path set
            return domain
    return None
    │
    ▼
domain found → validated dict
domain None → rejected dict con error structured
    │
    ▼
ui_action="proposal" emitido al FE
    │
    ▼
User aprueba en ProposalCard
    │
    ▼
FE PATCH endpoint del módulo (offer/brand/buyer_persona)
    │
    ▼
Service deserializa → entity → repo persist
```

**Validación de field_path en el persister** (offer-specific):
- `copilot/infrastructure/persisters/offer_persister.py:100` chequea `field_path in PERSISTABLE_FIELDS`.
- `PERSISTABLE_FIELDS` deriva de `OFFER_FIELD_CONTRACTS` (Fase 04). Mantenido. **No tocar en Fase 08**.

**Validación en `extract_structured` tool** (separado de propose_field_updates):
- `extract.py:107` usa `validate_field_path(domain, field_path)` (schema_introspection).
- Aceptación más permisiva (model paths + dict_parent prefix) que `is_editable_path` (curated catalog).

Post-Fase 08: ambos caminos idénticos en comportamiento — solo cambia el origen de la data (FieldContract registry vs hand-authored sets).

---

## §4 — Tests acceptance copilot existentes

### 4.1 — Tests críticos que deben pasar idéntico

| Test | Path | Cobertura |
|---|---|---|
| `test_editable_fields_integration.py` | `backend/tests/modules/copilot/` | get_catalog + propose_field_updates contracts |
| `test_extract_validation.py` | `backend/tests/modules/copilot/` | validate_field_path comportamiento exacto |
| `test_field_paths_hint.py` (si existe) | — | document extraction prompt hint |
| `test_brand_editable_fields_baseline.py` | `backend/tests/architecture/` | 38 working + 40 broken paths brand |
| `test_buyer_persona_editable_fields_baseline.py` | `backend/tests/architecture/` | working paths buyer baseline |
| `test_editable_fields_ssot.py` | `backend/tests/architecture/` | non-empty + uniqueness per dominio |
| `test_studio_snapshot_layer.py` | `backend/tests/modules/copilot/` | studio snapshot rendering |
| `test_field_contract_platform_coverage.py` | `backend/tests/architecture/` | Pydantic ⊆ FieldContract per módulo migrado |
| `test_field_contract_platform_module_template.py` | `backend/tests/architecture/` | generic fitness gates |

### 4.2 — Tests downstream que tocan editable_fields/validate_field_path

```bash
cd backend && .venv/bin/pytest tests/modules/copilot/ tests/architecture/ -q --tb=no
```

Baseline: 490 arch tests pass + tests/modules/copilot/ verde.

### 4.3 — Test acceptance copilot end-to-end

Tests de chat full-stack viven bajo `tests/modules/copilot/` (orchestrator, tools, persister tests). Ningún E2E de chat-stream golden snapshot hoy — el copilot acceptance es por unit test de cada componente (mutations, schema_introspection, persister).

---

## §5 — `copilot/domain/offer_fields.py` post-Fase 04

### 5.1 — Estado actual

```python
# copilot/domain/offer_fields.py — 38 líneas, projection-only

PERSISTABLE_FIELDS: set[str] = {
    c.path for c in OFFER_FIELD_CONTRACTS
    if c.can_propose and c.status == FieldStatus.ACTIVE
}
```

### 5.2 — Consumers

| Archivo | Línea | Uso |
|---|---|---|
| `copilot/infrastructure/persisters/offer_persister.py` | 9, 34, 100, 136 | validation + iteration en persist |
| `copilot/domain/schema_introspection.py` | 268 | `_build_offer_paths` indirección |
| `tests/architecture/test_field_contract_platform_coverage.py` | 31, 232, 244 | arch tests anti-drift |

### 5.3 — Decisión

**Mantener `offer_fields.py` como alias documentado**:
- 4 consumers, incluido offer_persister (critical path).
- Migrar consumers a `get_module_contracts` directo introduce cambios en código de persistencia con riesgo > beneficio (38 líneas más vs PR contained).
- En Fase 08, `schema_introspection._build_offer_paths` migra a `get_module_contracts("offer")` directo, eliminando UNA de las indirecciones (la otra — `offer_persister` — sigue leyendo `PERSISTABLE_FIELDS` como alias del contract registry, mathematically equivalent).
- Documentar en LEARNINGS Fase 08 + future phase puede dropearlo cuando offer_persister tenga golden snapshot tests más amplios.

---

## §6 — Estado caches schema_introspection

```python
# Module-level state actual
_DOMAIN_FIELD_CACHE: dict[str, set[str]] = {}    # cached por dominio
_DOMAIN_DICT_PARENTS: dict[str, set[str]] = {    # parents para prefix match
    "buyer_persona": {"demographics", "psychographics", "buyer_journey"},
}
_DOMAIN_BUILDERS: dict[str, Callable[[], set[str]]] = {
    "brand": _build_brand_paths,
    "offer": _build_offer_paths,
    "buyer_persona": _build_buyer_persona_paths,
}
```

**Consumer privado de `_DOMAIN_DICT_PARENTS`**: `field_paths_hint.py:24` lo importa directo (private!). Post-Fase 08: derivar de `BUYER_PERSONA_DICT_SUBKEYS.keys()` mantiene la API privada para field_paths_hint sin breaking change.

`_DOMAIN_FIELD_CACHE`: optimization — cache de paths set por dominio. Sigue siendo válido post-derivation (FieldContract registry es immutable post-bootstrap).

---

## §7 — Coordinación cross-cutting

### 7.1 — Boundaries

`shared/links/ports/editable_fields.py` puede importar `shared/domain/field_contract.py`. Ambos en `shared/`. No introduce nuevo cross-module coupling.

`copilot/domain/schema_introspection.py` ya importa `editable_fields` port. Agregar import de `field_contract` registry (`get_module_contracts`) está dentro del shared boundary.

### 7.2 — Lazy registration

Hoy: 2 lazy registrars paralelos.
- `field_contract._LAZY_REGISTRARS` importa `{module}/domain/field_contract.py` cuando se llama `get_module_contracts(module)`.
- `editable_fields._KNOWN_DOMAINS` importa `{module}/domain/copilot_editable_fields*.py` cuando se llama `get_catalog(domain)`.

Post-Fase 08: solo queda el primero. El segundo se elimina porque get_catalog deriva de get_module_contracts (que ya hace lazy load).

### 7.3 — Consumer downstream del shape interno del cache

Verificado vía grep: ningún consumer accede `_DOMAIN_FIELD_CACHE` o `_DOMAIN_BUILDERS` directamente (todos via `validate_field_path`). Único consumer del private `_DOMAIN_DICT_PARENTS` es `field_paths_hint.py:24` (intra-copilot, OK).

---

## §8 — Output (DoD pre-investigación)

- [x] Inventario completo call sites `get_catalog`/`get_paths_for`/`get_registered_domains`/`register_catalog`.
- [x] Inventario completo call sites `validate_field_path`/`is_editable_path`/`get_model_sections`/`format_*_markdown`.
- [x] Flow `propose_field_updates` documentado end-to-end.
- [x] Tests acceptance copilot identificados (10 archivos críticos).
- [x] Decisión sobre `offer_fields.py`: **mantener** como alias documentado.
- [x] `_DOMAIN_DICT_PARENTS` derivable de `BUYER_PERSONA_DICT_SUBKEYS.keys()` sin breaking change para field_paths_hint.
- [x] Boundaries cross-module verificados (sin nuevos coupling).

**Pre-investigación completa. Listo para escribir SPEC.md y ACCEPTANCE.md.**
