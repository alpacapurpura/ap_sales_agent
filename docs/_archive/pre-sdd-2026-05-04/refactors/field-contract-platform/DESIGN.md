# DESIGN — Field Contract Platform

> Documento de diseño cross-module. Sirve como anchor arquitectónico
> para todas las fases (04-09) y para sesiones futuras de Claude.
> **Nunca borrar ni reducir.** Si una decisión se invalida, marcar
> `superseded by ADR-NNN` con fecha — no editar in-place.

## 1 — Problema

Hoy en el monolito hay **5+ fuentes paralelas** que describen "qué
fields existen y a qué sección pertenecen":

| # | Archivo | Patrón | Ámbito |
|---|---|---|---|
| 1 | `shared/links/ports/editable_fields.py` (`FieldSpec`) registrado en `{module}/domain/copilot_editable_fields.py` | Manual | brand, buyer_persona, offer |
| 2 | `copilot/domain/schema_introspection.py` | Runtime Pydantic | cross-module, copilot read-side |
| 3 | `copilot/domain/offer_fields.py::PERSISTABLE_FIELDS` | Manual `set[str]` | offer write |
| 4 | `offer/domain/field_contract.py::FIELD_CONTRACT_REGISTRY` | Manual tuple | offer estructural |
| 5 | `offer/domain/extraction_section_map.py::OFFER_FIELDS_BY_FE_SECTION` | Manual dict | offer extraction worker |
| 6 | `{module}/domain/section_catalog.py` | Manual `SECTION_CATALOG` | UX metadata por section |

Cada uno se mantiene a mano. Drift confirmado entre #1 y #4 al abrir
Fase 04 (offer `OFFER_EDITABLE_FIELDS` no incluye los pricing LATAM
nuevos ni `total_perceived_value_anchor` ni authority fields que sí
viven en `FIELD_CONTRACT_REGISTRY`).

Continuar agregando registries por-módulo escala mal:
- 17 módulos × 4-5 registries paralelos = imposible mantener.
- Copilot conversacional necesita un contrato único para preguntar
  naturalmente — no puede reconciliar 5 fuentes en runtime.

## 2 — Solución

### 2.1 Capas claras

```
L0  Pydantic models                     Estructural · qué se persiste
     (offer.Offer, brand.BrandSettings, buyer_persona.BuyerPersona, …)
     │
     │ introspección + override metadata
     ▼
L1  shared.domain.FieldContract         Semántico · cross-module SSoT
     - path, owner_module, type
     - section, group, priority
     - filters (archetype, value_level, business_type, preset)
     - is_required_semantic
     - lifecycle (status, deprecated_in, replaced_by, introduced_in)
     - copilot meta (human_question_es, expects, gate,
                     redo_if_changes, can_propose)
     - notes (downstream context)
     │
     │ proyección por consumer
     ▼
L2  Consumers (todos derivados, ninguno SSoT paralelo)
     - FE schemas form-runtime              UX web
     - Copilot prompt enumeration            UX conversacional
     - Copilot propose_field_updates port    UX write
     - Sales-agent identity prompt           Render data-driven
     - Landing content builders              Render data-driven
     - Extraction wave outputs               ETL prompt + schema
     - Completion service                    % completado
     - Section catalog labels                UX metadata
```

**Principio**: Pydantic responde "¿qué se persiste?". FieldContract
responde "¿cómo lo trato semánticamente?". FE schema responde "¿cómo
se ve?". Cada consumer es proyección — nunca duplica.

### 2.2 Anatomía del FieldContract

Dataclass `frozen=True, slots=True` para tratarlo como compile-time
constant. Atributos agrupados por propósito:

```python
@dataclass(frozen=True, slots=True)
class FieldContract:
    # ── Identity ────────────────────────────────────────────────────
    path: str                    # "headline_promise" o "specific_details.duration"
    owner_module: str            # "offer" | "brand" | "buyer_persona" | …

    # ── Estructura (mostly derived from Pydantic) ───────────────────
    type: FieldType              # enum TEXT/NUMBER/BOOL/ENUM/LIST/OBJECT/DATE/URL
    is_required_structural: bool # Pydantic-required (no default, no Optional)
    enum_values: tuple[str, ...] | None
    list_item_type: str | None   # "text" | "object" | "enum" | …

    # ── Placement semántico ─────────────────────────────────────────
    section: str                 # FE section slug
    group: str | None            # subsection within section
    priority: int                # display/asking order

    # ── Filtros (cuando aplica) ─────────────────────────────────────
    archetype_filter: tuple[str, ...] | None       # offer-specific
    value_level_filter: tuple[str, ...] | None     # offer-specific
    business_type_filter: tuple[str, ...] | None   # cross-module
    preset_filter: tuple[str, ...] | None          # offer-specific

    # ── Requiredness semántico ──────────────────────────────────────
    is_required_semantic: bool   # required para considerar sección "completa"

    # ── Lifecycle ───────────────────────────────────────────────────
    status: FieldStatus          # ACTIVE | DEPRECATED | REMOVED
    deprecated_in: str | None    # version string ("2026-04-24-fase-08")
    replaced_by: str | None      # path replacement
    introduced_in: str | None    # version string

    # ── Copilot conversacional ──────────────────────────────────────
    can_propose: bool            # ¿el copilot puede escribir este field?
    human_question_es: str | None  # pregunta natural en español neutro
    expects: str | None          # type/format hint para LLM
    gate: str | None             # path precondición ("archetype debe estar set")
    redo_if_changes: tuple[str, ...] | None  # paths cuyo cambio invalida

    # ── Notes para consumers (sales-agent, landing, etc) ────────────
    notes: str | None
```

### 2.3 Cómo se construye

Cada módulo declara **un mapping** + **un dict de overrides**:

```python
# offer/domain/field_contract.py (post-refactor)

OFFER_SECTION_MAP: dict[str, str] = {
    # path → section
    "public_name": "identity",
    "headline_promise": "identity",
    "value_level": "strategy",
    "specific_details.weekly_time_commitment_hours": "program_details",
    "platform_details.api_available": "platform_details",
    # ... full mapping covering every Offer field user-facing
}

OFFER_FIELD_OVERRIDES: dict[str, FieldContractOverride] = {
    "headline_promise": Override(
        is_required_semantic=True,
        priority=10,
        human_question_es="¿Cuál es la promesa principal de esta oferta?",
        expects="una frase corta (8-15 palabras)",
        notes="Se renderiza en hero de landing y copy de sales-agent.",
    ),
    "value_level": Override(
        is_required_semantic=True,
        priority=5,
        human_question_es="¿Qué nivel de valor tiene esta oferta? (lead magnet, trial, core, premium…)",
        expects="uno de los valores del enum OfferValueLevel",
        gate="archetype",  # archetype debe estar set primero
    ),
    # ... overrides
}

# Derivación automática
OFFER_FIELD_CONTRACTS = derive_contracts_from_pydantic(
    model=Offer,
    owner_module="offer",
    section_map=OFFER_SECTION_MAP,
    overrides=OFFER_FIELD_OVERRIDES,
    ignore_paths=frozenset({"id", "tenant_id", "deleted_at", "created_at",
                            "updated_at", "metadata_info", "archived_at",
                            "shows_as_lead_magnet"}),
)

register_module_contracts("offer", OFFER_FIELD_CONTRACTS)
```

**Derivación walker**:
- Walk `Offer.model_fields` recursivamente.
- Para nested Pydantic models (PlatformDetails) → walk con prefix
  (`platform_details.X`).
- Para polymorphic union (`specific_details: Product | Service | …`)
  → walk cada variante con prefix `specific_details.X` y registrar
  archetype_filter automático según `ARCHETYPE_TO_DETAILS_MAPPING`.
- Tipo Pydantic → `FieldType` enum (`str` → TEXT, `int|float` → NUMBER,
  `bool` → BOOL, `Enum subclass` → ENUM con `enum_values`,
  `list[X]` → LIST con `list_item_type`).
- `Optional[X]` desempacado vía `unwrap_optional` (reuso código de
  `copilot/domain/schema_introspection.py`).
- Override merge: cualquier campo del override no-None pisa el derivado.
- Section: lookup en `section_map`. Si falta → arch test falla.

### 2.4 Module registry shared

```python
# shared/domain/field_contract.py

_MODULE_CONTRACTS: dict[str, tuple[FieldContract, ...]] = {}

def register_module_contracts(module: str, contracts: tuple[FieldContract, ...]) -> None:
    """Idempotent. Multiple imports of same module replace cleanly."""
    _MODULE_CONTRACTS[module] = contracts

def get_module_contracts(module: str) -> tuple[FieldContract, ...]:
    """Triggers lazy import if module not yet registered."""

def get_all_modules() -> tuple[str, ...]: ...

def find_contract(module: str, path: str) -> FieldContract | None: ...

def fields_by_section(module: str, section: str) -> tuple[FieldContract, ...]: ...

def fields_by_path_prefix(module: str, prefix: str) -> tuple[FieldContract, ...]:
    """For walking specific_details.* etc."""
```

### 2.5 Proyecciones por consumer

#### Copilot editable (write surface)

```python
# offer/domain/copilot_editable_fields.py (post-refactor)

OFFER_EDITABLE_FIELDS = tuple(
    FieldSpec(
        path=c.path,
        label=_label_from_override_or_section(c),  # override.label_es or section_catalog
        section=c.section,
        description=c.human_question_es or c.notes,
    )
    for c in get_module_contracts("offer")
    if c.can_propose and c.status == FieldStatus.ACTIVE
)
register_catalog("offer", OFFER_EDITABLE_FIELDS)
```

#### Persistable validation (write validator)

```python
# copilot/domain/offer_fields.py (post-refactor)

PERSISTABLE_FIELDS = frozenset(
    c.path
    for c in get_module_contracts("offer")
    if c.can_propose and c.status == FieldStatus.ACTIVE
)
```

#### Extraction worker grouping

```python
# offer/domain/extraction_section_map.py (post-refactor)

def fields_to_fe_sections(*, archetype, filled_paths) -> dict[str, list[str]]:
    contracts = get_module_contracts("offer")
    by_path = {c.path: c for c in contracts}
    result: dict[str, list[str]] = {}
    for path in filled_paths:
        # match exact (works for top-level + nested)
        contract = by_path.get(path)
        if contract is None:
            # fallback: prefix match for specific_details.*
            top = path.split(".")[0]
            contract = by_path.get(top)
        if contract is None:
            continue
        # archetype filter check
        if contract.archetype_filter and archetype not in contract.archetype_filter:
            continue
        result.setdefault(contract.section, []).append(path)
    return result
```

OFFER_FIELDS_BY_FE_SECTION dict: **borrado**.

#### Sales-agent prompt (futuro Fase 05)

```python
# sales_agent/application/knowledge_builder.py (post-fase-05)

def render_offer_block(offer: Offer) -> str:
    contracts = get_module_contracts("offer")
    blocks = []
    for c in sorted(contracts, key=lambda x: (x.section, x.priority)):
        if c.status != FieldStatus.ACTIVE:
            continue
        value = _resolve_path(offer, c.path)
        if value in (None, "", []):
            continue
        blocks.append(f"{c.section} · {c.notes or c.path}: {value}")
    return "\n".join(blocks)
```

#### Copilot conversacional (futuro Fase 09)

```python
# copilot/application/orchestrator/conversational_questioning.py

def next_question(module: str, current_state: dict) -> str | None:
    """Pick highest-priority field with no value + gates satisfied."""
    contracts = get_module_contracts(module)
    candidates = [
        c for c in contracts
        if c.status == FieldStatus.ACTIVE
        and c.can_propose
        and c.is_required_semantic
        and _path_value(current_state, c.path) in (None, "", [])
        and _gate_satisfied(c.gate, current_state)
    ]
    candidates.sort(key=lambda c: (c.priority, c.section))
    if not candidates:
        return None
    next_field = candidates[0]
    return next_field.human_question_es
```

### 2.6 Tests cross-cutting (gates de drift)

```python
# tests/architecture/test_field_contract_platform.py

def test_pydantic_model_fields_subset_of_field_contract_per_migrated_module():
    """Every Pydantic field user-facing tiene FieldContract entry."""
    for module in MIGRATED_MODULES:  # ["offer"] hoy, crece per fase
        pydantic_paths = _collect_pydantic_paths(_get_root_model(module))
        contract_paths = {c.path for c in get_module_contracts(module)}
        missing = pydantic_paths - contract_paths - IGNORED_PATHS[module]
        assert not missing, (
            f"Pydantic fields without FieldContract in {module}: {missing}"
        )

def test_editable_fields_subset_of_field_contract():
    """Catalog editable_fields del copilot ⊆ FieldContract paths."""

def test_persistable_fields_subset_of_field_contract():
    """offer_fields.PERSISTABLE_FIELDS ⊆ FieldContract paths."""

def test_fe_schema_paths_subset_of_field_contract():
    """offer-field-paths.json ⊆ FieldContract paths (offer)."""

def test_section_map_covers_all_fields():
    """Every Pydantic field user-facing está en module's SECTION_MAP."""

def test_no_orphan_section():
    """Every section en FieldContract aparece en section_catalog del módulo."""
```

### 2.7 Lifecycle de fields

Workflow para deprecar un field:

1. Marcar override con `status=FieldStatus.DEPRECATED, deprecated_in="...", replaced_by="..."`.
2. Consumers que leen → siguen recibiendo el field hasta que su `status == REMOVED`.
3. FE schemas se actualizan en sprint siguiente para no renderizar deprecados.
4. Sales-agent + landing + completion ya filtran por `status == ACTIVE`.
5. Una vez no hay rendering activo, ratchet a `REMOVED` + drop del Pydantic + migration.

Ventajas:
- Cero breaking changes. Cliente FE viejo sigue funcionando.
- LLM extraction prompt puede seguir capturando deprecated, va a la sombra.
- Drop coordinado en migration window.

### 2.8 Multi-channel projection (Fase 09)

El mismo `FieldContract` proyecta a:

- **Form-runtime web**: schema FE consume via codegen `OfferFieldPath`,
  el form usa `human_question_es` como fallback de label si schema no
  declara label custom (futuro).
- **Whatsapp/telegram (copilot conversacional)**: el orchestrator
  selecciona next field por priority + gate satisfied + missing value,
  emite `human_question_es` como mensaje al usuario, parsea respuesta
  con `expects` como hint al LLM.
- **Email/voz**: misma lógica.

Sin esto, el copilot conversacional necesita prompts hardcoded por
módulo. Con esto, agregar un field nuevo = aparece automático en todos
los canales.

## 3 — Migración incremental

| Fase | Módulo | Riesgo | Bloquea |
|---|---|---|---|
| 04 | offer (pilot) | Medio | Fase 05+ |
| 05 | sales-agent + landing + completion data-driven | Medio | nada |
| 06 | brand | Bajo | nada (patrón validado) |
| 07 | buyer-persona | Bajo | nada |
| 08 | copilot read+write unificación | Medio | bloqueado por brand+buyer |
| 09 | multi-channel projection | Alto | bloqueado por copilot unificación |

**Cada fase mantiene módulos no-migrados funcionando idéntico.** Brand
y buyer-persona en Fase 04 siguen con sus `FieldSpec` manuales — no
los toco. Cuando sea su turno (Fase 06/07), su `copilot_editable_fields.py`
pasa a derivación con migración byte-equivalent.

## 4 — Anti-frankenstein

Reglas:
- **Un solo `FieldContract`** vive en `shared/domain/`. Nunca per-módulo.
- **Cero duplicación**: si un consumer declara su propio "qué fields
  hay" → arch test falla.
- **Override en lugar de duplicar**: si un módulo necesita metadata
  extra para un field, va al override, no a otro registry.
- **Lifecycle versionado**: deprecaciones documentadas, no silenciadas.
- **Tests cross-cutting**: cada drift detectable se enforce con arch
  test que falla CI.

## 5 — Decisiones de diseño rechazadas

### 5.1 FieldContract per-módulo (no shared)

Rechazado: replica el problema. Cada módulo termina con su propio
contract divergente. Frankenstein peor.

### 5.2 Generar FieldContract desde JSON Schema

Rechazado: codegen + sync overhead. JSON Schema no soporta nuestros
filtros semánticos (archetype, business_type) sin extension.

### 5.3 Derivar todo de Pydantic + decoradores `@field_contract`

Rechazado: contamina el dominio Pydantic con metadata cross-module.
Override pattern separa cleanly.

### 5.4 Mover `editable_fields` port adentro de `FieldContract`

Rechazado: editable_fields tiene shape específica para copilot prompt.
Mantener proyección + port intacto preserva flexibilidad. Cuando Fase
08 unifique copilot, ahí se evalúa colapsar.

## 6 — Lo que este diseño NO resuelve (out of scope)

- Validación runtime de constraints (longitudes, regex, ranges) →
  vive en Pydantic + FE schemas (Zod).
- Internacionalización beyond español neutro LATAM → producto, no
  arquitectura.
- Form-runtime UI patterns (cards vs split arrays) → FE-only.
- Tenant-specific overrides de fields → casos extremos, evaluar
  cuando aparezca demanda real.

## 7 — Glosario

| Término | Significado |
|---|---|
| FieldContract | Dataclass shared con metadata semántica per field |
| Pydantic field | Atributo de un modelo Pydantic en `domain/` |
| FE schema | Archivo `.schema.ts` en `frontend/src/features/{module}/schemas/` |
| Section | Slug agrupador FE (`identity`, `pricing`, etc.) |
| Owner module | Módulo BE que persiste el field (offer, brand, …) |
| Override | Metadata semántica que Pydantic no puede expresar |
| Section map | Diccionario `path → section` por módulo |
| Lifecycle | Estado del field (ACTIVE/DEPRECATED/REMOVED) + transiciones |
| Copilot meta | `human_question_es`, `expects`, `gate`, `redo_if_changes`, `can_propose` |
| Multi-channel | Web + whatsapp + telegram + email + voz |

## 8 — Referencias

- Workspace previo: `docs/refactors/field-contract-ssot/`
- Reglas: `.claude/rules/copilot-resilience.md`, `.claude/rules/backend-ddd.md`
- Memorias: `~/.claude/projects/.../memory/feedback_form_runtime_autosave.md`
- Producto: `docs/domains/copilot/editable-fields.md` (si existe)
