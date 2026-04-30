# CONTRACT — PR-1-drop-buyer-persona-fields

> Owner: `nicolify-architect`. SSoT pre-implementación cross-stack. Backend + Frontend builders consumen este archivo en paralelo. **Refactor cleanup, no nueva capacidad.**

## 0. Context Summary

| Campo | Valor |
|---|---|
| PR | PR-1-drop-buyer-persona-fields |
| Sprint | S1-cleanup-buyer-persona |
| PI | PI-4-brand-evolutive-maintenance |
| Tipo | Refactor cross-stack — drop 2 fields buyer_persona |
| Módulos tocados | `brand` (model + entity + DTOs + repo + api + field-contract), `copilot` (persister + field_paths + extraction template) |
| Skills consultados | `brand-expert` (BuyerPersona aggregate vive bajo `brand/domain`, registra como `"buyer_persona"`); `copilot-expert` (extraction registry, prompt slot ordering, persister flow); `backend-expert` (migration idempotente, arch tests); `frontend-expert` (FSD schema mirror manual) |
| current-state afectados | `docs/pm-nico/current-state/brand.md` (capability lineage), `docs/pm-nico/current-state/copilot.md` (no actualiza — extraction sigue genérico) |
| Arch gates relevantes | `tests/architecture/test_buyer_persona_editable_fields_baseline.py` (NO drift — fields nunca estuvieron en baseline), DDD boundaries (no nuevos cross-module imports), backend-migrations (raw SQL idempotente) |

### Decisión arquitectónica clave (resuelta por architect)

| Pregunta abierta en PR.md | Resolución |
|---|---|
| **Backup data prod antes DROP o aceptar pérdida** | **ACEPTAR PÉRDIDA — sin script backup**. Justificación: (1) el field contract registra ambos fields como `can_propose=False`, lo que significa que copilot NUNCA propuso valor wholesale → datos sólo entran via form-runtime CRUD manual del user. (2) Form-runtime CRUD es opcional (no hay required-semantic). (3) Chris confirma en PR.md "Riesgos / Tenant prod con datos llenos" como decisión architect — interpretamos "data útil = 0 verified" porque ningún consumer downstream lee estos fields (sales_agent.objection_history es session-state distinto, offer.objections es campo distinto). (4) Migration es DROP COLUMN — irreversible vía downgrade trivial; un dump JSONB ad-hoc fuera del PR es lo correcto si Chris cambia de opinión post-merge. **Si Chris exige backup antes de merge, ver Open Question #1**. |
| **1 migration con 2 ALTER vs 2 migrations separadas** | **1 migration con 2 ALTER en un solo `op.execute(...)` block**. Justificación: ambos fields son la misma decisión funcional ("dropear las 2 secciones del form que el user no usa"), atomic together en una transacción evita estado intermedio inválido (model SA ya sin column pero DB todavía con column = ORM valida y rompe), y `IF EXISTS` garantiza idempotencia individual aunque sea un solo file. Más simple, mismo blast radius. |

## 1. Domain Entities (delta)

### `BuyerPersona` (`backend/src/modules/brand/domain/buyer_persona.py`)

```python
class BuyerPersona(BaseEntity):
    """Rich buyer persona entity built via the copilot's guided setup."""

    id: UUID
    tenant_id: UUID
    user_id: UUID
    name: str
    tagline: str | None = None
    scope: str = "GLOBAL"
    offer_id: UUID | None = None
    is_primary: bool = False

    # Profile (JSONB)
    demographics: dict = Field(default_factory=dict)
    psychographics: dict = Field(default_factory=dict)
    pain_points: list[dict] = Field(default_factory=list)
    desires: list[dict] = Field(default_factory=list)
    # ❌ DROP: objections: list[dict] = Field(default_factory=list)
    # ❌ DROP: preferred_channels: list[dict] = Field(default_factory=list)
    buyer_journey: dict = Field(default_factory=dict)
    purchase_triggers: list[str] = Field(default_factory=list)
    anti_patterns: list[str] = Field(default_factory=list)

    completeness_score: float = 0.0
    is_active: bool = True
    deleted_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
```

Docstring update: línea 18 `desires, objections, channel preferences, and the full buyer journey` → `desires, and the full buyer journey`.

## 2. SQLAlchemy 2.0 Models (delta)

### `BuyerPersonaModel` (`backend/src/modules/brand/infrastructure/models/buyer_persona_model.py`)

Drop columns L33-L34:
```python
# ❌ DROP: objections = Column(JSONB, nullable=False, default=list)
# ❌ DROP: preferred_channels = Column(JSONB, nullable=False, default=list)
```

**No nuevos índices, no nuevas columns.** Restantes columns + composite index `ix_buyer_personas_tenant_scope` intactos. Modelo todavía usa SQLA 1.x style `Column()` — **NO migrar a `mapped_column()` en este PR** (out of scope, S1 es cleanup atómico).

## 3. Pydantic v2 DTOs (delta)

### `backend/src/modules/brand/api/dto/buyer_personas.py`

`BuyerPersonaSectionUpdateDTO` (request):
```python
class BuyerPersonaSectionUpdateDTO(BaseModel):
    """PATCH parcial — only sent fields are updated."""

    name: str | None = None
    tagline: str | None = None
    demographics: dict[str, Any] | None = None
    psychographics: dict[str, Any] | None = None
    pain_points: list[dict[str, Any]] | None = None
    desires: list[dict[str, Any]] | None = None
    # ❌ DROP L28: objections: list[dict[str, Any]] | None = None
    # ❌ DROP L29: preferred_channels: list[dict[str, Any]] | None = None
    buyer_journey: dict[str, Any] | None = None
    purchase_triggers: list[str] | None = None
    anti_patterns: list[str] | None = None
```

`BuyerPersonaResponseDTO` (response, `from_attributes=True`):
```python
class BuyerPersonaResponseDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    tagline: str | None
    scope: str
    offer_id: UUID | None
    is_primary: bool
    demographics: dict[str, Any]
    psychographics: dict[str, Any]
    pain_points: list[dict[str, Any]]
    desires: list[dict[str, Any]]
    # ❌ DROP L50: objections: list[dict[str, Any]]
    # ❌ DROP L51: preferred_channels: list[dict[str, Any]]
    buyer_journey: dict[str, Any]
    purchase_triggers: list[str]
    anti_patterns: list[str]
    completeness_score: float
    created_at: datetime | None
    updated_at: datetime | None
```

`BuyerPersonaCreateDTO` — **sin cambios** (estos fields no se incluían en create shell).

## 4. API Routes (delta)

| Method | Path | Auth | response_model | Cambio |
|---|---|---|---|---|
| GET | `/api/v1/brand/buyer-personas` | Bearer + X-Tenant-ID | `list[BuyerPersonaResponseDTO]` | response shape pierde 2 fields |
| POST | `/api/v1/brand/buyer-personas` | Bearer + X-Tenant-ID | `BuyerPersonaResponseDTO` | response shape pierde 2 fields |
| GET | `/api/v1/brand/buyer-personas/{id}` | Bearer + X-Tenant-ID | `BuyerPersonaResponseDTO` | response shape pierde 2 fields |
| PATCH | `/api/v1/brand/buyer-personas/{id}` | Bearer + X-Tenant-ID | `BuyerPersonaResponseDTO` | request DTO ya no acepta los 2 fields (sería ignorado pre-cambio, ahora `extra="ignore"` por default Pydantic — sin 422) |
| DELETE | `/api/v1/brand/buyer-personas/{id}` | Bearer + X-Tenant-ID | 204 | sin cambios |

`response_model=` ya está en TODAS las rutas (verificado L48, L60, L81, L95). PII guardrail: ningún field dropeado era PII; los restantes (demographics.location, demographics.income) ya estaban allowed por feature.

### Completeness recomputation (`backend/src/modules/brand/api/buyer_personas.py:25-35`)

```python
_PROFILE_FIELDS = (
    "demographics",
    "psychographics",
    "pain_points",
    "desires",
    # ❌ DROP L30: "objections",
    # ❌ DROP L31: "preferred_channels",
    "buyer_journey",
    "purchase_triggers",
    "anti_patterns",
)
```

**Side-effect documentado:** `_calc_completeness()` cambia denominador de 9 a 7. Personas existentes recalculan completeness_score al primer PATCH (no migration data fix necesaria; eventual consistency aceptable para field cosmético). Score tip up para personas existentes (numerador igual o casi-igual, denominador menor). **Sin alarma user-side**.

## 5. TypeScript Types (delta)

### `frontend/src/lib/api/buyer-persona.ts`

```typescript
export interface BuyerPersona {
  id: string;
  name: string;
  tagline: string | null;
  scope: "GLOBAL" | "OFFER" | "CAMPAIGN";
  offer_id: string | null;
  is_primary: boolean;
  demographics: Record<string, unknown>;
  psychographics: Record<string, unknown>;
  pain_points: Record<string, unknown>[];
  desires: Record<string, unknown>[];
  // ❌ DROP L17: objections: Record<string, unknown>[];
  // ❌ DROP L18: preferred_channels: Record<string, unknown>[];
  buyer_journey: Record<string, unknown>;
  purchase_triggers: string[];
  anti_patterns: string[];
  completeness_score: number;
  created_at: string | null;
  updated_at: string | null;
}

export type BuyerPersonaSectionUpdateDTO = Partial<
  Pick<
    BuyerPersona,
    | "name"
    | "tagline"
    | "demographics"
    | "psychographics"
    | "pain_points"
    | "desires"
    // ❌ DROP L43: | "objections"
    // ❌ DROP L44: | "preferred_channels"
    | "buyer_journey"
    | "purchase_triggers"
    | "anti_patterns"
  >
>;
```

API client functions (`list/get/create/patch/delete`) — sin cambios de signatura.

## 6. Repository Interfaces (delta)

### `backend/src/modules/brand/infrastructure/repositories/buyer_persona_repository.py`

```python
def create(self, persona: BuyerPersona) -> BuyerPersona:
    db_model = BuyerPersonaModel(
        id=persona.id,
        tenant_id=persona.tenant_id,
        user_id=persona.user_id,
        name=persona.name,
        tagline=persona.tagline,
        scope=persona.scope,
        offer_id=persona.offer_id,
        is_primary=persona.is_primary,
        demographics=persona.demographics,
        psychographics=persona.psychographics,
        pain_points=persona.pain_points,
        desires=persona.desires,
        # ❌ DROP L47: objections=persona.objections,
        # ❌ DROP L48: preferred_channels=persona.preferred_channels,
        buyer_journey=persona.buyer_journey,
        purchase_triggers=persona.purchase_triggers,
        anti_patterns=persona.anti_patterns,
        completeness_score=persona.completeness_score,
        is_active=persona.is_active,
    )
    ...
```

`update()` no nombra columns explícitamente (usa `setattr(model, key, value)` con `hasattr` guard L125) — auto-resiliente. Tenant isolation preservado en TODAS las queries (`get_by_id`, `list_by_tenant`, `update`, `soft_delete`).

## 7. Application Services (delta)

No hay capa application/services dedicada para buyer_persona — la API route dispatcha directo al repo (patrón aceptado para CRUD). **Sin cambios.**

## 8. Agentic Surfaces (delta — `copilot-expert` consultado)

### 8.1 Field-contract registry (`backend/src/modules/brand/domain/buyer_persona_field_contract.py`)

`BUYER_PERSONA_SECTION_MAP` (L94-L119):
```python
BUYER_PERSONA_SECTION_MAP: dict[str, str] = {
    # identity, demographics, psychographics, journey ─── intactos
    "pain_points": "pain_points",
    "desires": "desires",
    # ❌ DROP L114: "objections": "objections",
    # ❌ DROP L115: "preferred_channels": "channels",
    "purchase_triggers": "triggers",
    "anti_patterns": "anti_patterns",
}
```

`BUYER_PERSONA_FIELD_OVERRIDES` (L133-L141):
```python
BUYER_PERSONA_FIELD_OVERRIDES: dict[str, Override] = {
    "pain_points": Override(can_propose=False),
    "desires": Override(can_propose=False),
    # ❌ DROP L137: "objections": Override(can_propose=False),
    # ❌ DROP L138: "preferred_channels": Override(can_propose=False),
    "purchase_triggers": Override(can_propose=False),
    "anti_patterns": Override(can_propose=False),
    # ... (resto identity/demographics/psychographics/buyer_journey labels intactos)
}
```

`BUYER_PERSONA_DICT_SUBKEYS` y `BUYER_PERSONA_IGNORE_PATHS` — **sin cambios**.

`derive_contracts_from_pydantic` re-deriva auto post-edit Pydantic + section map. Walker emit() ya filtra fields no presentes en model.

### 8.2 Copilot persister (`backend/src/modules/copilot/infrastructure/persisters/buyer_persona_persister.py`)

```python
_LIST_FIELDS = {
    "pain_points",
    "desires",
    # ❌ DROP L29: "objections",
    # ❌ DROP L30: "preferred_channels",
    "purchase_triggers",
    "anti_patterns",
}
```

`_DICT_FIELDS` y `_SCALAR_FIELDS` — **sin cambios**. `load_existing()` filtra por field presence en model (L97 `getattr(persona, field, None)`) — defensivo, no rompe en transición.

### 8.3 Field paths hint (`backend/src/modules/copilot/domain/field_paths_hint.py`)

```python
_LIST_PATHS: dict[str, set[str]] = {
    "buyer_persona": {
        "pain_points",
        "desires",
        # ❌ DROP L35: "objections",
        # ❌ DROP L36: "preferred_channels",
        "purchase_triggers",
        "anti_patterns",
    },
    "offer": {
        "marketing_pain_points",
        "marketing_desires",
        "deliverables",
        "pricing_options",
        "objections",         # ⚠️ NO TOCAR — distinct field offer module
        "target_avatar_match",
    },
}
```

**`offer.objections` queda intacto** — es campo distinto (verified Explore brief).

### 8.4 Extraction template (`backend/src/modules/copilot/infrastructure/prompts/templates/interview/buyer_persona_doc_extraction.j2`)

Drop líneas 26-27 (regla de extracción):
```jinja
4. Para campos `(list)`, usa el cue semántico para ruteo correcto:
   - `pain_points` → lista de objetos `{description, severity}` (severity 1-5). Cue: ...
   - `desires` → lista de objetos `{description, importance}` (importance 1-5). Cue: ...
   ❌ DROP L26: `objections` → lista de objetos {text, response}. Cue: ...
   ❌ DROP L27: `preferred_channels` → lista de objetos {channel, usage}. Cue: ...
   - `purchase_triggers` → lista de strings cortos. Cue: ...
   - `anti_patterns` → lista de strings cortos. Cue: ...
```

Drop líneas 51-52 del bloque de ejemplo JSON output:
```jinja
{
  "extracted_fields": {
    "name": "...",
    "demographics.age_range": "...",
    "pain_points": [{"description": "...", "severity": 4}],
    "desires": [{"description": "...", "importance": 5}],
    ❌ DROP L51: "objections": [{"text": "...", "response": "..."}],
    ❌ DROP L52: "preferred_channels": [{"channel": "...", "usage": "..."}],
    "purchase_triggers": ["..."],
    ...
  }
}
```

### 8.5 Cache prefix invariants (consultado `copilot-expert`)

**Verificación slot ordering preservado:** el extraction template `buyer_persona_doc_extraction.j2` NO es parte del system_prompt cache prefix (slots 1-6). Es prompt user-turn-specific renderizado con `prompt_loader.render(...)` para tool `extract_document_to_fields`. **Cache hit rate sales/copilot NO se ve afectado**. El template `field_paths_hint` que se inyecta dentro del extraction prompt re-derive automáticamente desde `editable_fields` catalog (que YA NO incluye los 2 fields porque `can_propose=False`) — coherencia auto post-cambio.

**Verificación trace events:** `copilot_trace_event` recorder no nombra estos paths específicamente (event-sourced JSONB). No drift de schema observability.

### 8.6 Extraction registry (`backend/src/modules/copilot/domain/extraction_domain_registry.py`)

Update comentario L57-L60 (cosmético, no cambia behavior):
```python
"buyer_persona": ExtractionDomainConfig(
    domain="buyer_persona",
    template_name="interview/buyer_persona_doc_extraction",
    persister_key="buyer_persona",
    # BuyerPersona stores pain_points/desires/purchase_triggers/anti_patterns
    # as arrays (objects or strings), so the LLM may return list[dict] or
    # list[str] values alongside scalars. The DocumentExtractionResponse
    # model is widened in document_processor to accept those shapes.
    response_value_kind="mixed",
),
```

`response_value_kind="mixed"` mantiene — todavía hay list[dict] (pain_points, desires) en buyer_persona.

## 9. Migration Notes

### Archivo: `backend/alembic/versions/{NEW_REV}_drop_buyer_persona_fields.py`

```python
"""drop_buyer_persona_fields

Drops `objections` + `preferred_channels` JSONB columns from
buyer_personas. Both fields were verified unused by downstream consumers
(sales_agent.objection_history is session-state distinct; offer.objections
is a different module's field). Form-runtime CRUD users may have populated
data; the cleanup intentionally accepts data loss (decision PI-4 S1 PR-1).

Revision ID: {NEW_REV}
Revises: f86f848caefa
Create Date: 2026-04-29 ...
"""

from collections.abc import Sequence

from alembic import op

revision: str = "{NEW_REV}"
down_revision: str | None = "f86f848caefa"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE buyer_personas DROP COLUMN IF EXISTS objections")
    op.execute("ALTER TABLE buyer_personas DROP COLUMN IF EXISTS preferred_channels")


def downgrade() -> None:
    op.execute(
        "ALTER TABLE buyer_personas "
        "ADD COLUMN IF NOT EXISTS objections JSONB NOT NULL DEFAULT '[]'"
    )
    op.execute(
        "ALTER TABLE buyer_personas "
        "ADD COLUMN IF NOT EXISTS preferred_channels JSONB NOT NULL DEFAULT '[]'"
    )
```

### Decisiones migration

- **Down revision = `f86f848caefa`** (verified `ls backend/alembic/versions/ | tail` — última migración aplicada en el proyecto).
- **`{NEW_REV}` se genera con `alembic revision -m "drop_buyer_persona_fields"`**. Builder asigna el hash real.
- **Idempotente** vía `DROP COLUMN IF EXISTS` (Postgres native). `op.execute()` raw SQL (regla `backend-migrations.md`).
- **Downgrade re-crea columns vacías** (`DEFAULT '[]'`). Datos perdidos en upgrade NO se recuperan en downgrade — esto es DROP COLUMN, no soft-delete. Documentado en docstring.
- **Sin enum changes** (no aplica).
- **Sin index drops** — los 2 fields no tenían índice dedicado (verified L33-L34 model y L48-L55 migration histórica).

### Test pre-prod (clone DB) — comando obligatorio antes de merge

```bash
docker exec -t visionarias_postgres psql -U postgres -c "CREATE DATABASE migration_test;"
docker exec visionarias_postgres bash -c 'pg_dump -U postgres -s visionarias_logs | psql -U postgres -d migration_test'
docker exec -t visionarias_brain_dev bash -c 'POSTGRES_DB=migration_test alembic stamp f86f848caefa && POSTGRES_DB=migration_test alembic upgrade head'
docker exec -t visionarias_brain_dev bash -c 'POSTGRES_DB=migration_test alembic upgrade head'  # 2nd run = idempotency check
docker exec -t visionarias_postgres psql -U postgres -c "DROP DATABASE migration_test;"
```

## 10. File Structure (delta)

### MODIFIED files

| Path | Layer | Cambio |
|---|---|---|
| `backend/src/modules/brand/domain/buyer_persona.py` | BE/domain | Drop fields L40-L41 + docstring L18 |
| `backend/src/modules/brand/infrastructure/models/buyer_persona_model.py` | BE/infra | Drop columns L33-L34 |
| `backend/src/modules/brand/api/dto/buyer_personas.py` | BE/api | Drop fields L28-L29 (Update DTO) + L50-L51 (Response DTO) |
| `backend/src/modules/brand/api/buyer_personas.py` | BE/api | Drop entries L30-L31 en `_PROFILE_FIELDS` |
| `backend/src/modules/brand/infrastructure/repositories/buyer_persona_repository.py` | BE/infra | Drop entries L47-L48 en `create()` |
| `backend/src/modules/brand/domain/buyer_persona_field_contract.py` | BE/domain | Drop entries L114-L115 (SECTION_MAP) + L137-L138 (FIELD_OVERRIDES) |
| `backend/src/modules/copilot/infrastructure/persisters/buyer_persona_persister.py` | BE/infra (copilot) | Drop entries L29-L30 en `_LIST_FIELDS` |
| `backend/src/modules/copilot/domain/field_paths_hint.py` | BE/domain (copilot) | Drop entries L35-L36 en `_LIST_PATHS["buyer_persona"]` |
| `backend/src/modules/copilot/infrastructure/prompts/templates/interview/buyer_persona_doc_extraction.j2` | BE/infra (copilot) | Drop líneas 26-27 (cues) + 51-52 (ejemplo JSON) |
| `backend/src/modules/copilot/domain/extraction_domain_registry.py` | BE/domain (copilot) | Update comentario L57-L60 (cosmético) |
| `backend/tests/modules/brand/test_buyer_persona_model.py` | BE/test | Drop entries L29-L30 del set `expected` |
| `backend/tests/modules/brand/test_buyer_persona_entity.py` | BE/test | Drop assertions L71-L72 (`persona.objections == []`, `persona.preferred_channels == []`) |
| `backend/tests/modules/brand/test_buyer_persona_repository.py` | BE/test | Drop kwargs `objections=` (L258-L263), `preferred_channels=` (L264-L269) en `_make_persona()` |
| `backend/tests/modules/copilot/test_buyer_persona_extraction_template.py` | BE/test (copilot) | Drop tests `test_objections_have_explicit_cue` (L66-L69) + `test_preferred_channels_have_explicit_cue` (L71-L74). Update docstring L6 |
| `backend/tests/modules/copilot/test_extract_validation.py` | BE/test (copilot) | Drop assertions L102-L103 (`validate_field_path("buyer_persona", "objections")`, `..."preferred_channels"`) |
| `backend/tests/modules/copilot/test_field_paths_hint.py` | BE/test (copilot) | Update L41 — remove `"objections"` y `"preferred_channels"` del tuple iterado (assertion sigue válida — siguen NO en hint) |
| `backend/tests/modules/copilot/test_editable_fields_integration.py` | BE/test (copilot) | Drop assertions L50, L53 (`"objections" not in paths`, `"preferred_channels" not in paths`) — paths siguen no estando, pero los tests específicos ya no aplican porque los fields no existen |
| `frontend/src/features/brand-studio/schemas/buyer-persona.schema.ts` | FE/feature | Drop entries L181-L221 (objeciones array) + L225-L249 (preferred_channels array) |
| `frontend/src/lib/api/buyer-persona.ts` | FE/lib | Drop fields L17-L18 (BuyerPersona interface) + L43-L44 (BuyerPersonaSectionUpdateDTO union) |
| `frontend/src/features/brand-studio/pages/PersonaDetailPage.tsx` | FE/feature | **NUEVO descubrimiento (no en PR.md surface)** — drop entries L22-L23 del array `EDITABLE_FIELDS` |
| `frontend/src/features/brand-studio/pages/__tests__/PersonaDetailPage.test.tsx` | FE/test | Drop entries L66-L67 del fixture `FULL_PERSONA` |
| `frontend/src/features/brand-studio/components/dashboard/__tests__/BuyerPersonasDashboard.test.tsx` | FE/test | Drop entries L90-L91 del mock |

### NEW files

| Path | Layer | Cambio |
|---|---|---|
| `backend/alembic/versions/{NEW_REV}_drop_buyer_persona_fields.py` | BE/migration | Nueva migration idempotente raw SQL (sección 9) |
| `backend/tests/modules/brand/test_buyer_persona_fields_dropped_regression.py` | BE/test | Regression test "response no incluye objections/preferred_channels" + "Pydantic Update DTO rechaza fields obsoletos via from-attributes" (sección 14) |
| `frontend/src/features/brand-studio/schemas/__tests__/buyer-persona-schema-cleanup.test.ts` | FE/test | Regression test "schema buyer-persona NO contiene fields objections/preferred_channels" (sección 14) |

### REFERENCE only (NO MODIFICAR)

- `backend/alembic/versions/f851363921c9_add_buyer_personas.py` — history immutable
- `backend/src/modules/sales_agent/**` — `objection_history` es session state distinto, NO TOCAR
- `backend/src/modules/offer/**` — `Offer.objections` es campo distinto, NO TOCAR
- `backend/src/modules/copilot/application/tools/offer_section_tools.py` — `suggest_missing_objections` y `structure_objections` son tools del módulo offer, NO TOCAR
- `backend/src/modules/copilot/infrastructure/qdrant/marketing_kb_store.py` — `domain="objections"` es categoría KB curada cross-tenant, NO TOCAR
- `backend/tests/architecture/test_copilot_registry.py` — referencia tools offer, NO TOCAR

## 11. Cross-Cutting Concerns

| Concern | Tratamiento |
|---|---|
| **Tenant isolation** | Todas las queries del repo siguen filtrando `tenant_id`. Sin cambios. |
| **Currency / monetary** | N/A — no hay fields monetarios afectados. `demographics.income` es string libre, sin currency code. |
| **Master data (UTC + tenant locale)** | N/A — no hay datetime fields afectados. `created_at`/`updated_at` intactos. |
| **Spanish neutro LatAm** | Sí aplica — el extraction template j2 está en español neutro. Drop preserva neutro (no introduce voseo). User-facing: form-runtime schema FE pierde labels "Objeciones" + "Canales preferidos" (ambos neutros). |
| **PII** | Ninguno de los 2 fields era PII por sí mismo (ambos son user-authored arrays libres). Sin cambios al PII allowlist. `response_model=` ya enforced. |
| **Native-first dev** | Builder corre `cd backend && .venv/bin/{ruff,pytest,alembic}` y `cd frontend && npx {tsc,eslint,vitest}`. NUNCA `docker exec ruff/pytest`. |
| **Idempotency on writes** | N/A — PR es DROP-only, no nuevos writes. Migration es idempotente vía `IF EXISTS`. |
| **Soft delete** | `deleted_at` column intacto en `buyer_personas`. `BuyerPersonaModel` y `BuyerPersona` mantienen `deleted_at`. |

## 12. Architecture Fitness Impact

### Gates que correrán contra este PR

| Gate | Resultado esperado | Justificación |
|---|---|---|
| `tests/architecture/test_buyer_persona_editable_fields_baseline.py` | **GREEN sin cambios** | Los 2 fields NUNCA estuvieron en el catalog baseline (12 entries — sólo identity/demographics/psychographics/journey). `can_propose=False` los mantenía fuera de la projection. |
| `tests/architecture/test_field_contract_completeness.py` (Pydantic ⊆ FieldContract) | **GREEN tras edit** | Pydantic shrink + section_map shrink en sync. Walker auto-rederive. |
| `tests/architecture/test_field_contract_platform.py` | **GREEN** | Sin nuevos paths fuera de Pydantic. |
| `tests/architecture/test_extraction_contract.py` (analytics, ortogonal) | **GREEN sin cambios** | No toca analytics. |
| `tests/architecture/test_no_new_copilot_module_imports.py` (ratchet 22) | **GREEN sin cambios** | Sin nuevos cross-module imports. |
| `tests/architecture/test_copilot_anchors.py` (cap 36/36) | **GREEN sin cambios** | Sin nuevos anchors. |
| `tests/architecture/test_copilot_registry.py` | **GREEN sin cambios** | `suggest_missing_objections` + `structure_objections` (offer module) intactos. |
| `tests/architecture/test_response_model_required.py` | **GREEN sin cambios** | Todas las rutas tienen `response_model=`. |
| `tests/architecture/test_currency_handling.py` | **N/A** — sin currency fields tocados. |
| FE arch tests (`frontend/src/__tests__/architecture/`) | **GREEN sin cambios** | No nuevos cross-feature imports, no nuevo schema centralization. |

### Allowlists impact

- **Ratchet shrink expected:** N/A — los 2 fields no estaban en ningún allowlist. Cleanup interno.
- **Sin allowlist growth.**

## 13. pm-nico/current-state Updates Required

### `docs/pm-nico/current-state/brand.md`

PM update post-merge en sección "Capacidades actuales" → línea Buyer Personas:
```markdown
- Buyer Personas (multi-persona) — sin objections/preferred_channels (cleanup PR-1 PI-4 S1, 2026-04-29)
```

Y append entry en "PIs históricos":
```markdown
| PI-4 S1 PR-1 | drop buyer_persona objections + preferred_channels (no consumer downstream) | 2026-04-29 |
```

### `docs/pm-nico/current-state/copilot.md`

**No actualiza.** Auto-fill de buyer_persona pierde 2 cues en extraction template, pero la capability "Doc extraction" sigue sólida — el template re-deriva automáticamente del FieldContract registry. No es regresión user-facing.

## 14. Test Surfaces (TDD-mandatory)

Builder DEBE escribir RED tests por capa antes de implementar GREEN.

### BE — Domain layer (RED first)

- `backend/tests/modules/brand/test_buyer_persona_entity.py` — UPDATE: drop assertions L71-L72. Tests existentes restantes deben seguir GREEN.
- `backend/tests/modules/brand/test_buyer_persona_fields_dropped_regression.py` — **NUEVO RED test**:
  ```python
  def test_buyer_persona_entity_has_no_objections_field() -> None:
      from src.modules.brand.domain.buyer_persona import BuyerPersona
      fields = BuyerPersona.model_fields
      assert "objections" not in fields
      assert "preferred_channels" not in fields
  ```

### BE — Infrastructure layer (RED first)

- `backend/tests/modules/brand/test_buyer_persona_model.py` — UPDATE: drop entries L29-L30 del set `expected`. Test sigue assert `expected.issubset(columns)` GREEN.
- `backend/tests/modules/brand/test_buyer_persona_fields_dropped_regression.py` (continued):
  ```python
  def test_buyer_persona_model_has_no_objections_column() -> None:
      from src.modules.brand.infrastructure.models.buyer_persona_model import BuyerPersonaModel
      columns = {c.name for c in BuyerPersonaModel.__table__.columns}
      assert "objections" not in columns
      assert "preferred_channels" not in columns
  ```
- `backend/tests/modules/brand/test_buyer_persona_repository.py` — UPDATE: drop kwargs L258-L269 del helper `_make_persona`. Test full-roundtrip sigue GREEN sin esos fields.

### BE — Migration test (RED first)

- `backend/tests/modules/brand/test_buyer_persona_fields_dropped_regression.py` (continued):
  ```python
  def test_migration_idempotent(clone_db_session) -> None:
      """Run upgrade twice — second pass is no-op."""
      # Run alembic upgrade head twice on clone, both succeed.
  ```
- **Manual integration step (Acceptance gate):** clone DB test command de sección 9.

### BE — Application/API layer

- `backend/tests/modules/brand/test_buyer_persona_fields_dropped_regression.py` (continued):
  ```python
  def test_response_dto_excludes_dropped_fields() -> None:
      from src.modules.brand.api.dto.buyer_personas import BuyerPersonaResponseDTO
      fields = BuyerPersonaResponseDTO.model_fields
      assert "objections" not in fields
      assert "preferred_channels" not in fields

  def test_update_dto_excludes_dropped_fields() -> None:
      from src.modules.brand.api.dto.buyer_personas import BuyerPersonaSectionUpdateDTO
      fields = BuyerPersonaSectionUpdateDTO.model_fields
      assert "objections" not in fields
      assert "preferred_channels" not in fields
  ```

### BE — Copilot extraction layer

- `backend/tests/modules/copilot/test_buyer_persona_extraction_template.py` — drop tests L66-L74 (`test_objections_have_explicit_cue`, `test_preferred_channels_have_explicit_cue`). Update docstring L6 quita refs a los 2 fields.
- `backend/tests/modules/copilot/test_extract_validation.py` — drop assertions L102-L103. **Side-effect:** `validate_field_path("buyer_persona", "objections")` ahora retorna `False` (correcto — path ya no en catalog ni en model). Tests "rejects garbage" L111-L116 cubren — agregar 2 assertions:
  ```python
  assert validate_field_path("buyer_persona", "objections") is False
  assert validate_field_path("buyer_persona", "preferred_channels") is False
  ```
- `backend/tests/modules/copilot/test_field_paths_hint.py` — UPDATE L41 tuple iterado quita `"objections"` + `"preferred_channels"` (los assertions siguen válidos).
- `backend/tests/modules/copilot/test_editable_fields_integration.py` — UPDATE: drop assertions L50, L53 (los 2 fields ya no existen en el modelo, no es necesario assert "not in paths" — son negativos vacuos post-drop).

### FE — Schema layer (RED first)

- `frontend/src/features/brand-studio/schemas/__tests__/buyer-persona-schema-cleanup.test.ts` — **NUEVO RED test**:
  ```typescript
  import { describe, it, expect } from "vitest";
  import { buyerPersonaSchema } from "../buyer-persona.schema";

  describe("buyerPersonaSchema cleanup PR-1", () => {
    it("does not contain objections field", () => {
      const ids = buyerPersonaSchema.fields.map(f => f.id);
      expect(ids).not.toContain("objections");
    });
    it("does not contain preferred_channels field", () => {
      const ids = buyerPersonaSchema.fields.map(f => f.id);
      expect(ids).not.toContain("preferred_channels");
    });
  });
  ```

### FE — Component / Page layer

- `frontend/src/features/brand-studio/pages/__tests__/PersonaDetailPage.test.tsx` — UPDATE fixture `FULL_PERSONA` (drop L66-L67). Tests existentes siguen GREEN porque no asertan estos fields específicamente.
- `frontend/src/features/brand-studio/components/dashboard/__tests__/BuyerPersonasDashboard.test.tsx` — UPDATE mock data (drop L90-L91). Idem.

### E2E

- **No requerido**. PR es cleanup schema sin nueva ruta. Smoke existente `/brand-studio/publico/persona/{id}` debe seguir GREEN (UI pierde 2 secciones del scroll vertical, pero ninguna interacción crítica cambia).

### Agentic eval

- **No requerido**. No hay golden eval afectado (los 2 fields nunca estuvieron en goldens copilot por `can_propose=False`).

## 15. Research Notes

**No aplica** — patrón cleanup conocido (DROP COLUMN idempotente + Pydantic shrink + section_map shrink). El field-contract platform ya provee derivación auto del catalog post-edit (Fase 06-09 cementadas en 2026-04, ver `docs/refactors/field-contract-platform/LEARNINGS.md`). Sin patterns novel.

## 16. Open Questions for PM — RESUELTAS (Chris 2026-04-29)

| # | Pregunta | Resolución Chris |
|---|---|---|
| **#1** | Backup data prod antes DROP COLUMN | **NO backup. Aceptar pérdida.** Justificación architect aceptada (`can_propose=False` + sin consumer downstream). Comando CSV ad-hoc disponible si emergencia post-merge, NO incluido en PR scope. |
| **#2** | `_calc_completeness` ratio change (denominador 9→7) | **Lazy recompute on next PATCH.** NO data-fix migration bulk. Side-effect aceptable (mejora UX, fields omitidos no penalizan). |
| **#3** | `validate_field_path` rejection del path obsoleto | **Aceptar comportamiento default.** Pydantic `extra="ignore"` ya filtra. NO explicit warning log en transition window (sobre-engineering). |
| **#4** | Sales_agent + offer + KB intactos | **Confirmado intacto.** NO aprovechar PR para cleanup adicional en otros módulos. Out-of-scope respetado. |

**Estado:** todas resueltas. Builder BE + FE pueden proceder en paralelo sin bloqueos PM.

---

<!-- @pm: CONTRACT.md ready. Próximo paso: ejecutar prompts/02-builder-start.md o ejecutar /pm "PR-1 architect done" para review. -->
