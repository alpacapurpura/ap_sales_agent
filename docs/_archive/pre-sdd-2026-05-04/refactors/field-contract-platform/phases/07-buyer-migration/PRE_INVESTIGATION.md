# Pre-investigación obligatoria — Fase 07

## Sección 1 — Buyer-persona Pydantic surface

### Q1.1 — Modelo completo `BuyerPersona`

`backend/src/modules/brand/domain/buyer_persona.py` — extiende `BaseEntity` (Pydantic `BaseModel` con `from_attributes=True`). 22 fields:

| Field | Type | Required | Categoría |
|---|---|---|---|
| `id` | `UUID` | ✅ | system |
| `tenant_id` | `UUID` | ✅ | system |
| `user_id` | `UUID` | ✅ | system |
| `name` | `str` | ✅ | scalar user-facing |
| `tagline` | `str \| None` | — | scalar user-facing |
| `scope` | `str` (default `"GLOBAL"`) | — | metadata interno |
| `offer_id` | `UUID \| None` | — | relación interna |
| `is_primary` | `bool` | — | metadata interno |
| `demographics` | `dict` | — | JSONB **dict** |
| `psychographics` | `dict` | — | JSONB **dict** |
| `pain_points` | `list[dict]` | — | JSONB **list[dict]** |
| `desires` | `list[dict]` | — | JSONB **list[dict]** |
| `objections` | `list[dict]` | — | JSONB **list[dict]** |
| `preferred_channels` | `list[dict]` | — | JSONB **list[dict]** |
| `buyer_journey` | `dict` | — | JSONB **dict** |
| `purchase_triggers` | `list[str]` | — | JSONB **list[str]** |
| `anti_patterns` | `list[str]` | — | JSONB **list[str]** |
| `completeness_score` | `float` | — | derivado |
| `is_active`, `deleted_at`, `created_at`, `updated_at` | — | — | lifecycle/audit |

### Q1.2 — Composables / nested Pydantic

**Ninguno**. BuyerPersona NO tiene sub-modelos Pydantic. Los campos "anidados" son JSONB con shape libre (`dict` y `list[dict]`). El walker actual de `derive_contracts_from_pydantic` no recurse sobre dicts.

## Sección 2 — Section catalog

### Q2.1 — Section catalog dedicado para buyer_persona

**No tiene** section_catalog separado (a diferencia de brand). Las secciones inline usadas por el catalog actual son: `identity`, `demographics`, `psychographics`, `journey`. Sin alineación con `brand/domain/section_catalog.py`. Para Fase 07: declarar secciones en `BUYER_PERSONA_SECTION_MAP` directo, sin crear archivo `section_catalog.py` nuevo.

Sections planeadas:

| Section | Cubre |
|---|---|
| `identity` | name, tagline |
| `demographics` | demographics.* |
| `psychographics` | psychographics.* |
| `journey` | buyer_journey.* |
| `pain_points` | list pain_points |
| `desires` | list desires |
| `objections` | list objections |
| `channels` | list preferred_channels |
| `triggers` | list purchase_triggers |
| `anti_patterns` | list anti_patterns |

## Sección 3 — Module registration name

### Q3.1 — Módulo BE separado vs subdir de brand

**Mantener** `brand/domain/buyer_persona_field_contract.py` (subdir de brand, sin crear módulo BE nuevo). Razones:

- BuyerPersona vive en `brand/domain/`. Mover requiere refactor cross-domain ortogonal al field-contract refactor.
- `register_module_contracts("buyer_persona", ...)` ya distingue el dominio sin necesitar módulo separado.
- Lazy registrar: `_LAZY_REGISTRARS["buyer_persona"] = "src.modules.brand.domain.buyer_persona_field_contract"`.
- Consistente con catálogo legacy `brand/domain/copilot_editable_fields_buyer_persona.py`.

Module key cross-platform: `"buyer_persona"` (consistente con port editable_fields y schema_introspection).

## Sección 4 — Drift audit

### Sources comparadas

| Source | Path count | Comportamiento |
|---|---|---|
| `BUYER_PERSONA_EDITABLE_FIELDS` (catalog) | **12** | Surface visible al copilot |
| `_build_buyer_persona_paths` (validator) | 24 (8 top + 16 dotted) | Validación path en `propose_field_updates` |
| FE `buyer-persona.schema.ts` | **16** (12 + 4 lists) | UX render del form-runtime |
| `BuyerPersonaPersister` accepted | abierto via prefix matching de dict parents | Persistencia |

### Drifts encontrados

1. **`demographics.income` vs `demographics.income_range`**: catalog usa `income`, validator declara `income_range` en `dot_notation`. FE schema usa `income`. Persister acepta ambos (prefix matching dict parent). **Resolución**: canónico = `demographics.income` (FE-driven). Dropear `income_range` del scope contract.
2. **`psychographics.aspirations` (catalog + FE)** no aparece en validator dotted set (validator tiene `beliefs`/`personality_traits`/`media_consumption` que el catalog no expone). Resolución: canónico = sub-keys del FE schema. Validator legacy se replazará en Fase 08.
3. **List fields (`pain_points`, `desires`, `objections`, `preferred_channels`)** existen en FE + Pydantic pero NO en catalog (decisión UX existente: edición item-by-item via form-runtime, no propose_field_updates). Resolución: contract emit con `can_propose=False`.
4. **`purchase_triggers`, `anti_patterns`** (list[str]) viven en Pydantic + validator's `top_level` set, pero NO en catalog ni FE schema. Resolución: emit con `can_propose=False` (no UX surface hoy).

## Sección 5 — Decisión walker (Patrón A vs B)

### Patrón A — hand-author dict sub-keys

Cada módulo con dicts JSONB hand-authora un dict de sub-keys + descripción manual de cada contract. Walker no se toca.

**Contras**: cada módulo nuevo con JSONB duplica boilerplate. Pierde el invariant "section_map declara → walker emite".

### Patrón B — extender walker con `dict_subkeys` arg

`derive_contracts_from_pydantic` recibe `dict_subkeys: dict[str, tuple[str, ...]] | None = None`. Cuando un campo top-level está en `dict_subkeys`, walker emite un FieldContract por sub-key (path `"{field}.{subkey}"`, type TEXT default, is_required_structural=False). El campo parent se trata como composable handle (no emite contract bare).

**Pros**: extensión mínima a shared (~15 LOC), reutilizable para cualquier módulo con JSONB sub-keys. Section_map sigue siendo SSoT de paths → secciones. Override puede subir tipo (NUMBER/ENUM) si necesario.

**Recomendación pre-investigación (Fase 06 LEARNINGS)**: B. **Confirmado**.

## Sección 6 — Coordinación

- `project_brand_studio_refactor` (Sprint 6.E): offer-studio FE editor — **cero overlap** con buyer-persona BE.
- Brand Fase 06 cerrada (`ed8a3a4f`). No reabrir.
- Buyer-persona FE schema `buyer-persona.schema.ts` no se toca (INVARIANT 9).

## Output

- [x] Lista Pydantic completa: 22 fields documentados.
- [x] Section catalog confirmado: inline en `BUYER_PERSONA_SECTION_MAP`, 10 sections.
- [x] Module name: `"buyer_persona"`, archivo en `brand/domain/buyer_persona_field_contract.py`.
- [x] Walker decisión: **Patrón B** (`dict_subkeys` arg en shared walker).
- [x] Drift audit: 4 drifts catalogados + estrategia byte-identical via `can_propose=False`.
- [x] FE schema canónico: 16 paths user-facing.
- [x] Catalog post-Fase-07 expected: 12 entries (byte-identical al legacy).
