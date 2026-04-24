# CONTRACT — Offer Narrative Fields Alignment

**Status:** READY TO IMPLEMENT (BE + FE parallel)
**Owner domain:** `offer` (backend), `offer-studio` (frontend)
**Date:** 2026-04-24
**Reviewers:** backend-expert, frontend-expert
**Arch rule refs:** `backend-ddd.md`, `backend-migrations.md`, `tenant-isolation.md`, `offer-catalogs.md`, `spanish-text.md`, `form-runtime-array.md`, `frontend-fsd.md`, tessl `pii-sanitisation`, `parallel-safety.md`.

---

## 1. Resumen

Este contrato arregla el bug donde el extractor URL del copilot graba data correctamente en `products.*`, el worker calcula `section_completed` y emite badges correctas, pero las secciones OFFER_LEVEL de la UI (`identity`, `promise`, `strategy`, `psychology`, `closing`) muestran placeholders porque los `path` en los schemas FE apuntan a **campos que no existen** en el aggregate `Offer` ni en `ProductModel` (ejs: `before_state`, `after_state`, `measurable_outcomes`, `cultural_trust_barriers`, `refund_process_description`, `urgency_drivers`, `public_name`, `objections_raw`, etc.).

Ruta elegida (decisión producto D1): **expansiva** — crear las columnas DB faltantes y realinear paths FE a columnas canónicas. 13 columnas nuevas en `products`, 13 fields nuevos en `Offer` + DTOs + repo, prompts LLM actualizados, renderer nuevo `textarea` con `storeAs: "newline_array"`, tool copilot `structure_objections` para flujo paste-AI.

**Fuera de alcance (NO tocar):**
- Polimorfismo `specific_details.*` (program/service/event/product/subscription).
- Catálogos SSoT (`archetype`, `preset`, `section`, `value_level`, `format`, `variant_structure`, `ladder_hints`, `business_types`).
- Wizard preset-first (`PresetPickerStep`, `ConditionalQuestionsStep`, `CreateOfferWizard`).
- Secciones NO OFFER_LEVEL (`platform_details`, `location`, `gallery`, `testimonials`, `portfolio`, `faq`, `resources`, `knowledge`, `instructors`, `value_stack`, `pricing`).
- Brand studio extraction.
- `offer_completion_service` ratios existentes.

---

## 2. Columnas nuevas — migration spec

**Archivo:** `backend/alembic/versions/<timestamp>_offer_narrative_fields.py`
**Tabla:** `products`
**Regla:** `backend-migrations.md` — idempotente, raw SQL, sin FK, sin `op.add_column()`, sin `sa.Enum(..., create_type=True)`.

### 2.1 Inventario (13 columnas)

| # | column_name | pg_type | nullable | default | jsonb_shape | FE_section |
|---|---|---|---|---|---|---|
| 1 | `before_state` | `text` | YES | NULL | — | promise |
| 2 | `after_state` | `text` | YES | NULL | — | promise |
| 3 | `why_now` | `text` | YES | NULL | — | promise |
| 4 | `measurable_outcomes` | `jsonb` | NO | `'[]'::jsonb` | `string[]` | promise |
| 5 | `cultural_trust_barriers` | `jsonb` | NO | `'[]'::jsonb` | `string[]` | psychology |
| 6 | `emotional_triggers` | `jsonb` | NO | `'[]'::jsonb` | `string[]` | psychology |
| 7 | `status_drivers` | `jsonb` | NO | `'[]'::jsonb` | `string[]` | psychology |
| 8 | `regret_scenarios` | `jsonb` | NO | `'[]'::jsonb` | `string[]` | psychology |
| 9 | `refund_process_description` | `text` | YES | NULL | — | closing |
| 10 | `urgency_drivers` | `jsonb` | NO | `'[]'::jsonb` | `string[]` | closing |
| 11 | `scarcity_reason_honest` | `text` | YES | NULL | — | closing |
| 12 | `bonus_if_act_now` | `text` | YES | NULL | — | closing |
| 13 | `final_push_copy` | `text` | YES | NULL | — | closing |

### 2.2 SQL idempotente (copy-paste literal)

```python
"""offer: +13 narrative columns for OFFER_LEVEL sections

Revision ID: <auto>
Revises: <prev>
Create Date: 2026-04-24
"""
from alembic import op


revision = "<auto>"
down_revision = "<prev>"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- promise ------------------------------------------------------
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS before_state TEXT")
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS after_state TEXT")
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS why_now TEXT")
    op.execute(
        "ALTER TABLE products ADD COLUMN IF NOT EXISTS measurable_outcomes "
        "JSONB NOT NULL DEFAULT '[]'::jsonb"
    )

    # --- psychology ---------------------------------------------------
    op.execute(
        "ALTER TABLE products ADD COLUMN IF NOT EXISTS cultural_trust_barriers "
        "JSONB NOT NULL DEFAULT '[]'::jsonb"
    )
    op.execute(
        "ALTER TABLE products ADD COLUMN IF NOT EXISTS emotional_triggers "
        "JSONB NOT NULL DEFAULT '[]'::jsonb"
    )
    op.execute(
        "ALTER TABLE products ADD COLUMN IF NOT EXISTS status_drivers "
        "JSONB NOT NULL DEFAULT '[]'::jsonb"
    )
    op.execute(
        "ALTER TABLE products ADD COLUMN IF NOT EXISTS regret_scenarios "
        "JSONB NOT NULL DEFAULT '[]'::jsonb"
    )

    # --- closing ------------------------------------------------------
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS refund_process_description TEXT")
    op.execute(
        "ALTER TABLE products ADD COLUMN IF NOT EXISTS urgency_drivers "
        "JSONB NOT NULL DEFAULT '[]'::jsonb"
    )
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS scarcity_reason_honest TEXT")
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS bonus_if_act_now TEXT")
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS final_push_copy TEXT")


def downgrade() -> None:
    # Explicit NO-OP. Narrative columns are purely additive; dropping them
    # would destroy tenant data. Use a forward-only migration if a rollback
    # is really needed.
    pass
```

### 2.3 Regression test antes de prod

Obligatorio (`.claude/rules/backend-migrations.md`):

```bash
docker exec -t visionarias_postgres psql -U postgres -c "CREATE DATABASE migration_test;"
docker exec visionarias_postgres bash -c 'pg_dump -U postgres -s visionarias_logs | psql -U postgres -d migration_test'
docker exec -t visionarias_brain_dev bash -c 'POSTGRES_DB=migration_test alembic stamp <PREV_REV>'
docker exec -t visionarias_brain_dev bash -c 'POSTGRES_DB=migration_test alembic upgrade head'
docker exec -t visionarias_postgres psql -U postgres -c "DROP DATABASE migration_test;"
```

---

## 3. SQLAlchemy model — `ProductModel`

**Archivo:** `backend/src/modules/offer/infrastructure/models/product_model.py`

Agregar (manteniendo estilo 1.x `Column(...)` actual del archivo — no mezclar con `mapped_column`, ese refactor es out-of-scope):

```python
# --- Narrative: promise ----------------------------------------------
before_state = Column(Text, nullable=True)
after_state = Column(Text, nullable=True)
why_now = Column(Text, nullable=True)
measurable_outcomes = Column(JSONB, nullable=False, default=list, server_default="[]")

# --- Narrative: psychology -------------------------------------------
cultural_trust_barriers = Column(JSONB, nullable=False, default=list, server_default="[]")
emotional_triggers = Column(JSONB, nullable=False, default=list, server_default="[]")
status_drivers = Column(JSONB, nullable=False, default=list, server_default="[]")
regret_scenarios = Column(JSONB, nullable=False, default=list, server_default="[]")

# --- Narrative: closing ----------------------------------------------
refund_process_description = Column(Text, nullable=True)
urgency_drivers = Column(JSONB, nullable=False, default=list, server_default="[]")
scarcity_reason_honest = Column(Text, nullable=True)
bonus_if_act_now = Column(Text, nullable=True)
final_push_copy = Column(Text, nullable=True)
```

Nota: `Text` ya importado en la parte superior del archivo. No introducir imports nuevos.

---

## 4. Domain entity — `Offer`

**Archivo:** `backend/src/modules/offer/domain/offer.py`

### 4.1 Fields en `class Offer(BaseEntity)`

Insertar tras `objections: list[ObjectionItem] = []` (línea 150) y antes de `metadata_info`:

```python
# --- Promise narrative (post-identity) ---
before_state: str | None = None
after_state: str | None = None
why_now: str | None = None
measurable_outcomes: list[str] = []

# --- Psychology narrative (post-objections) ---
cultural_trust_barriers: list[str] = []
emotional_triggers: list[str] = []
status_drivers: list[str] = []
regret_scenarios: list[str] = []

# --- Closing narrative ---
refund_process_description: str | None = None
urgency_drivers: list[str] = []
scarcity_reason_honest: str | None = None
bonus_if_act_now: str | None = None
final_push_copy: str | None = None
```

### 4.2 `OfferPromiseUpdate` (+4 fields)

```python
class OfferPromiseUpdate(BaseEntity):
    headline_promise: str | None = None
    primary_outcome: str | None = None
    time_to_value: str | None = None
    # NEW:
    before_state: str | None = None
    after_state: str | None = None
    why_now: str | None = None
    measurable_outcomes: list[str] | None = None
```

### 4.3 `OfferPsychologyUpdate` (+4 fields)

```python
class OfferPsychologyUpdate(BaseEntity):
    target_avatar_match: list[AvatarPersona] | None = None
    anti_avatar_keywords: list[str] | None = None
    marketing_pain_points: list[str] | None = None
    marketing_desires: list[str] | None = None
    objections: list[ObjectionItem] | None = None
    # NEW:
    cultural_trust_barriers: list[str] | None = None
    emotional_triggers: list[str] | None = None
    status_drivers: list[str] | None = None
    regret_scenarios: list[str] | None = None
```

### 4.4 `OfferClosingUpdate` (+5 fields)

```python
class OfferClosingUpdate(BaseEntity):
    guarantee_type: GuaranteeType | None = None
    guarantee_terms: str | None = None
    checkout_page_url: str | None = None
    calendar_type_id: str | None = None
    onboarding_action: OnboardingMechanism | None = None
    onboarding_url: str | None = None
    downsell_offer_id: UUID | None = None
    upsell_offer_id: UUID | None = None
    # NEW:
    refund_process_description: str | None = None
    urgency_drivers: list[str] | None = None
    scarcity_reason_honest: str | None = None
    bonus_if_act_now: str | None = None
    final_push_copy: str | None = None
    support_duration_days: int | None = None  # moved from OfferDetailsUpdate visibility (still persists as-is)
```

**Nota importante:** `support_duration_days` ya existe en DB/domain y vive en `OfferDetailsUpdate`. Agregarlo en `OfferClosingUpdate` **como puerto adicional** (no moverlo) para que el wave `closing` del LLM pueda rellenarlo — el repo sigue mapeando el mismo `model.support_duration_days`. Si viene en ambas Updates a la vez, el service aplica el último patch ganador (orden actual: details wave corre en wave 3, closing en wave 2 — closing se sobrescribirá con details si details trae valor).

---

## 5. DTOs — `ProductResponse` / `ProductUpdate`

**Archivo:** `backend/src/modules/offer/api/dto/products.py`

### 5.1 `ProductResponse` — agregar (tras `marketing_desires`, línea 42):

```python
# Narrative: promise
before_state: str | None = None
after_state: str | None = None
why_now: str | None = None
measurable_outcomes: list[str] | None = []

# Narrative: psychology
cultural_trust_barriers: list[str] | None = []
emotional_triggers: list[str] | None = []
status_drivers: list[str] | None = []
regret_scenarios: list[str] | None = []

# Narrative: closing
refund_process_description: str | None = None
urgency_drivers: list[str] | None = []
scarcity_reason_honest: str | None = None
bonus_if_act_now: str | None = None
final_push_copy: str | None = None

# Objections structured (serializada como list[dict] via model_dump)
objections: list[dict[str, Any]] | None = []
```

### 5.2 `ProductUpdate` — agregar (todas optional):

```python
# Promise
before_state: str | None = None
after_state: str | None = None
why_now: str | None = None
measurable_outcomes: list[str] | None = None

# Psychology
cultural_trust_barriers: list[str] | None = None
emotional_triggers: list[str] | None = None
status_drivers: list[str] | None = None
regret_scenarios: list[str] | None = None
objections: list[dict[str, Any]] | None = None   # structured objection items

# Closing
refund_process_description: str | None = None
urgency_drivers: list[str] | None = None
scarcity_reason_honest: str | None = None
bonus_if_act_now: str | None = None
final_push_copy: str | None = None
```

### 5.3 PII guard (tessl `pii-sanitisation`)

Ningún field nuevo es PII. `ProductResponse` ya cumple `response_model=` en todos los endpoints que lo devuelven (`api/products.py` verificar). No hace falta masking.

---

## 6. Repository mapping

**Archivo:** `backend/src/modules/offer/infrastructure/repositories/offer_repository.py`

### 6.1 `_to_domain()` — agregar al dict (tras línea 76 `"metadata_info": ...`):

```python
# --- Narrative: promise ---
"before_state": model.before_state,
"after_state": model.after_state,
"why_now": model.why_now,
"measurable_outcomes": model.measurable_outcomes or [],

# --- Narrative: psychology ---
"cultural_trust_barriers": model.cultural_trust_barriers or [],
"emotional_triggers": model.emotional_triggers or [],
"status_drivers": model.status_drivers or [],
"regret_scenarios": model.regret_scenarios or [],

# --- Narrative: closing ---
"refund_process_description": model.refund_process_description,
"urgency_drivers": model.urgency_drivers or [],
"scarcity_reason_honest": model.scarcity_reason_honest,
"bonus_if_act_now": model.bonus_if_act_now,
"final_push_copy": model.final_push_copy,
```

### 6.2 `_to_model()` — agregar al constructor `ProductModel(...)` (tras línea 156 `objections=...`):

```python
before_state=offer.before_state,
after_state=offer.after_state,
why_now=offer.why_now,
measurable_outcomes=list(offer.measurable_outcomes or []),

cultural_trust_barriers=list(offer.cultural_trust_barriers or []),
emotional_triggers=list(offer.emotional_triggers or []),
status_drivers=list(offer.status_drivers or []),
regret_scenarios=list(offer.regret_scenarios or []),

refund_process_description=offer.refund_process_description,
urgency_drivers=list(offer.urgency_drivers or []),
scarcity_reason_honest=offer.scarcity_reason_honest,
bonus_if_act_now=offer.bonus_if_act_now,
final_push_copy=offer.final_push_copy,
```

### 6.3 Safety rules

- **None / ausencia** → `_to_model` pasa `None` para columnas `Text`; para columnas `JSONB NOT NULL DEFAULT '[]'` pasa `[]` (NO `None` — rompería el `NOT NULL`).
- Pydantic defaults ya garantizan `[]` en `Offer.*_outcomes/triggers/drivers/scenarios/urgency_drivers`, el `list(offer.x or [])` es doble red.
- Tenant isolation: sin cambios, el repo ya filtra por `tenant_id` en toda query (líneas 174, 191, 201, 221, 237, 253, 275).

---

## 7. Extraction section map (SSoT)

**Archivo:** `backend/src/modules/offer/domain/extraction_section_map.py`

### 7.1 Update `OFFER_FIELDS_BY_FE_SECTION`:

```python
OFFER_FIELDS_BY_FE_SECTION: dict[str, tuple[str, ...]] = {
    "identity": (
        "public_name",
        "internal_sku",
        "headline_promise",
        "primary_outcome",
        "time_to_value",
    ),
    "promise": (
        "requires_application",
        "min_financial_capacity",
        "prerequisites",
        # NEW narrative:
        "before_state",
        "after_state",
        "why_now",
        "measurable_outcomes",
    ),
    "strategy": (
        "value_level",
        "delivery_model",
        "target_avatar_match",
        "anti_avatar_keywords",
    ),
    "psychology": (
        "marketing_pain_points",
        "marketing_desires",
        "objections",
        # NEW narrative:
        "cultural_trust_barriers",
        "emotional_triggers",
        "status_drivers",
        "regret_scenarios",
    ),
    "value_stack": ("deliverables", "includes_offers"),
    "pricing": ("pricing_options", "price_pay_in_full", "currency"),
    "instructors": ("instructors",),
    "closing": (
        "guarantee_type",
        "guarantee_terms",
        "checkout_page_url",
        "calendar_type_id",
        "onboarding_action",
        "onboarding_url",
        "downsell_offer_id",
        "upsell_offer_id",
        "vsl_link",
        # NEW narrative:
        "refund_process_description",
        "urgency_drivers",
        "scarcity_reason_honest",
        "bonus_if_act_now",
        "final_push_copy",
        "support_duration_days",
    ),
}
```

### 7.2 Decisión de asignación única (doble conteo)

`marketing_pain_points` y `marketing_desires` **viven únicamente en `psychology`** (no se duplican en `strategy`) para evitar double-counting en badges de progreso. El schema FE `strategy.schema.ts` **sigue mostrándolos** (consumo de lectura), pero el mapa de grouping del worker los atribuye a `psychology` al emitir `section_completed`.

Justificación: el FE ya hace `strategy → path: "marketing_pain_points_raw"` (proxy textarea sobre el array), pero el extractor popula el array. El badge "sección strategy llena 4/4" se sostiene porque `target_avatar_match`, `anti_avatar_keywords`, `value_level`, `delivery_model` suman 4 ya. Psicología suma sus 7 propios (pain + desires + objections + 4 narrativos nuevos).

`support_duration_days` queda asignado a `closing` (aunque domain lo exponga también desde details). Decisión: el usuario lo ve en `closing` section — es la primera sección que lo pregunta.

### 7.3 Arch test (§12) enforza: cada path listado existe como attr en `Offer` domain.

---

## 8. LLM extraction pydantic schemas

**Layer:** application (NO domain — las pydantic schemas del LLM son concerns de aplicación, NO de dominio). Arch test `test_domain_layer_has_no_framework_imports` sigue verde porque los pydantic `BaseModel` ya viven en `src/modules/offer/domain/offer.py` — lo cual el repo permite dado que `BaseEntity` es Pydantic (ver `.claude/rules/backend-ddd.md` — "pure Python + Pydantic only en domain"). **Los schemas de wave YA existen como `OfferPromiseUpdate`/etc en domain** — lo que agregamos son sus fields nuevos (§4).

Adicionalmente, los prompts Jinja (`backend/src/modules/offer/infrastructure/prompts/templates/`) deben describir los nuevos fields en castellano Latam neutro.

### 8.1 Field descriptions para el LLM (castellano Latam neutro)

En `OfferPromiseUpdate`, reemplazar con `Field(description=...)`:

```python
from pydantic import Field

class OfferPromiseUpdate(BaseEntity):
    headline_promise: str | None = Field(
        None,
        description="Frase titular de una línea con el resultado prometido. Concreta, memorable, en primera persona del beneficio.",
    )
    primary_outcome: str | None = Field(
        None,
        description="Resultado principal descriptivo que obtiene el cliente al completar la oferta. Más extenso que la frase titular.",
    )
    time_to_value: str | None = Field(
        None,
        description="Cuánto tarda el cliente en sentir el primer resultado útil. Ejemplos: '30 días', '1 trimestre', 'primera semana'.",
    )
    before_state: str | None = Field(
        None,
        description="Cómo vive el cliente ANTES de la oferta. Dolor concreto y situación cotidiana específica.",
    )
    after_state: str | None = Field(
        None,
        description="Cómo vive el cliente DESPUÉS de completar la oferta. Evidencia concreta, no abstracta.",
    )
    why_now: str | None = Field(
        None,
        description="Razón por la que postergar tiene costo concreto. Conecta con el costo real de inacción. Evita escasez falsa.",
    )
    measurable_outcomes: list[str] | None = Field(
        None,
        description="Lista de resultados medibles concretos, uno por ítem. Idealmente con números. Diferencia la promesa de 'vas a sentirte mejor'.",
    )
```

En `OfferPsychologyUpdate`:

```python
class OfferPsychologyUpdate(BaseEntity):
    target_avatar_match: list[AvatarPersona] | None = Field(
        None,
        description="Segmentos/arquetipos adicionales a los que también les sirve la oferta (no solo el avatar principal).",
    )
    anti_avatar_keywords: list[str] | None = Field(
        None,
        description="Palabras o frases que descalifican a un lead. El sales-agent las usa para descartar prospectos mal calificados.",
    )
    marketing_pain_points: list[str] | None = Field(
        None,
        description="Dolores específicos y medibles del avatar, uno por ítem. Evita genéricos. El agente los cita textualmente.",
    )
    marketing_desires: list[str] | None = Field(
        None,
        description="Deseos concretos del avatar (qué quiere LOGRAR), uno por ítem. Con números cuando aplique.",
    )
    objections: list[ObjectionItem] | None = Field(
        None,
        description=(
            "Objeciones anticipadas estructuradas. Cada ítem tiene: type (price/time/trust/partner/custom), "
            "trigger_phrases (frases reales del prospecto), strategy (nombre del argumento, ej. 'ROI Reframing'), "
            "rebuttal (guion de respuesta textual)."
        ),
    )
    cultural_trust_barriers: list[str] | None = Field(
        None,
        description=(
            "Barreras culturales Latam que no son objeciones clásicas: desconfianza a pagos online, preferencia WhatsApp, "
            "tarjetas internacionales rebotadas, exigencia de factura B2B, negociación esperada. Uno por ítem."
        ),
    )
    emotional_triggers: list[str] | None = Field(
        None,
        description="Miedos, deseos y aspiraciones que mueven la decisión de compra. Lenguaje emocional (no racional). Uno por ítem.",
    )
    status_drivers: list[str] | None = Field(
        None,
        description="Qué cambia en la percepción social del cliente cuando compra y tiene éxito. Uno por ítem.",
    )
    regret_scenarios: list[str] | None = Field(
        None,
        description="Situaciones futuras concretas donde el lead se va a arrepentir de no haber comprado hoy. Uno por ítem.",
    )
```

En `OfferClosingUpdate`:

```python
class OfferClosingUpdate(BaseEntity):
    guarantee_type: GuaranteeType | None = Field(None, description="Tipo de garantía ofrecida. Enum estándar.")
    guarantee_terms: str | None = Field(
        None,
        description="Términos exactos de la garantía, copia textual para landing + checkout + email. Tono confiado, sin letra chica.",
    )
    checkout_page_url: str | None = None
    calendar_type_id: str | None = None
    onboarding_action: OnboardingMechanism | None = None
    onboarding_url: str | None = None
    downsell_offer_id: UUID | None = None
    upsell_offer_id: UUID | None = None
    refund_process_description: str | None = Field(
        None,
        description=(
            "Cómo se devuelve el dinero, desglosado por método de pago (tarjeta, Mercado Pago, transferencia). "
            "Combate la desconfianza Latam. Más importante que el monto de la garantía."
        ),
    )
    urgency_drivers: list[str] | None = Field(
        None,
        description="Razones HONESTAS para comprar ahora. Uno por ítem. Urgencia falsa pierde confianza.",
    )
    scarcity_reason_honest: str | None = Field(
        None,
        description="Razón honesta de los cupos limitados — logística real, tiempo del experto, calidad de atención.",
    )
    bonus_if_act_now: str | None = Field(
        None,
        description="Bonus condicional a actuar en una ventana de acción definida (48h, 7 días). Distinto del fast-action del value-stack.",
    )
    final_push_copy: str | None = Field(
        None,
        description="Frase de cierre emocional para cuando el lead está a un paso de decidir. Directa, empática, con recordatorio de garantía.",
    )
    support_duration_days: int | None = Field(
        None,
        description="Cuántos días el cliente tiene acceso al soporte post-compra (chat, email, comunidad).",
    )
```

### 8.2 Prompts Jinja (infrastructure)

Archivos a actualizar:

- `backend/src/modules/offer/infrastructure/prompts/templates/offer_extract_promise.j2` — agregar instrucciones sobre `before_state`, `after_state`, `why_now`, `measurable_outcomes`.
- `backend/src/modules/offer/infrastructure/prompts/templates/offer_extract_psychology.j2` — agregar instrucciones para objections estructuradas + 4 narrativos.
- `backend/src/modules/offer/infrastructure/prompts/templates/offer_extract_closing.j2` — agregar los 5 narrativos.

**Regla spanish-text.md:** Latam neutro, tuteo (`tú`/`tienes`), sin voseo (`vos`/`tenés`). Tildes/eñes correctas. Los prompts son entrada al modelo, NO usuario-final, pero el output del modelo SÍ es usuario-final → instruir al modelo a emitir en tuteo Latam neutro.

### 8.3 Waves sin cambio

- `value_stack` — sin cambio.
- `details` (polimórfico por archetype) — sin cambio, fuera de alcance.
- `strategy` — sin cambio (pain_points/desires ya los migraba al array structured).

---

## 9. FE schema paths — mapping canónico

**Regla:** todos los `path` apuntan a campos que existen en `ProductResponse` (camelCase NO aplica — Pydantic/FE usan el mismo snake_case para estos paths porque el form-runtime los aplica directo al aggregate via PATCH).

### 9.1 `identity.schema.ts`

| id | old_path | new_path | field_type |
|---|---|---|---|
| `public_name` | `public_name` | `name` | text |
| `headline_promise` | `headline_promise` | `headline_promise` | textarea |
| `primary_outcome` | `primary_outcome` | `primary_outcome` | textarea |
| `time_to_value` | `time_to_value` | `time_to_value` | text |

**Razón:** la columna DB es `products.name` — NO crear `public_name`. El backend ya expone `ProductResponse.name` y acepta `ProductUpdate.name`. El FE del form-runtime debe usar `path: "name"`. El label sigue mostrándose como "Nombre público" al usuario.

### 9.2 `promise.schema.ts`

| id | old_path | new_path | field_type | DB |
|---|---|---|---|---|
| `before_state` | `before_state` | `before_state` | textarea | `text` |
| `after_state` | `after_state` | `after_state` | textarea | `text` |
| `why_now` | `why_now` | `why_now` | textarea | `text` |
| `measurable_outcomes` | `measurable_outcomes` | `measurable_outcomes` | textarea + `storeAs: "newline_array"` | `jsonb string[]` |

### 9.3 `strategy.schema.ts`

| id | old_path | new_path | field_type | DB |
|---|---|---|---|---|
| `avatar_id` | `avatar_id` | `avatar_id` | text | `uuid` |
| `target_avatar_match` | `target_avatar_match_raw` | `target_avatar_match` | textarea + `storeAs: "newline_array"` | `jsonb string[]` |
| `marketing_pain_points` | `marketing_pain_points_raw` | `marketing_pain_points` | textarea + `storeAs: "newline_array"` | `jsonb string[]` |
| `marketing_desires` | `marketing_desires_raw` | `marketing_desires` | textarea + `storeAs: "newline_array"` | `jsonb string[]` |
| `anti_avatar_keywords` | `anti_avatar_keywords_raw` | `anti_avatar_keywords` | textarea + `storeAs: "newline_array"` | `jsonb string[]` |

**Decisión `target_avatar_match`:** el DB actual persiste `list[AvatarPersona]` (enum). El FE actual lo expone como textarea libre. Discrepancia. **Decisión:** mantener el enum en domain/DB (los valores válidos son un enum cerrado `AvatarPersona`), pero el textarea acepta una línea por valor. El renderer `storeAs: "newline_array"` split por `\n` → validación domain descarta strings que no matchean enum (ya pasa por `normalize_*` en repo). Documentar en hint FE: "Uno por línea. Valores válidos: <lista de enum>" — o migrar a array de strings libres en una iteración futura (fuera de alcance).

### 9.4 `psychology.schema.ts`

| id | old_path | new_path | field_type | DB |
|---|---|---|---|---|
| `objections` | `objections_raw` | `objections` | array cards (structured) | `jsonb structured[]` |
| `cultural_trust_barriers` | `cultural_trust_barriers` | `cultural_trust_barriers` | textarea + newline_array | `jsonb string[]` |
| `emotional_triggers` | `emotional_triggers` | `emotional_triggers` | textarea + newline_array | `jsonb string[]` |
| `status_drivers` | `status_drivers` | `status_drivers` | textarea + newline_array | `jsonb string[]` |
| `regret_scenarios` | `regret_scenarios` | `regret_scenarios` | textarea + newline_array | `jsonb string[]` |

### 9.5 `closing.schema.ts`

| id | old_path | new_path | field_type | DB |
|---|---|---|---|---|
| `guarantee_type` | `guarantee_type` | `guarantee_type` | enum | `string` |
| `guarantee_terms` | `guarantee_terms` | `guarantee_terms` | textarea | `text` |
| `refund_process_description` | `refund_process_description` | `refund_process_description` | textarea | `text` |
| `urgency_drivers` | `urgency_drivers` | `urgency_drivers` | textarea + newline_array | `jsonb string[]` |
| `scarcity_reason_honest` | `scarcity_reason_honest` | `scarcity_reason_honest` | textarea | `text` |
| `bonus_if_act_now` | `bonus_if_act_now` | `bonus_if_act_now` | textarea | `text` |
| `support_duration_days` | `support_duration_days` | `support_duration_days` | number | `integer` |
| `final_push_copy` | `final_push_copy` | `final_push_copy` | textarea | `text` |

### 9.6 `objections` itemSchema (array cards)

Regla `form-runtime-array.md` — 3 sub-fields visibles → cards (strategy auto-sugerido por type). Spec:

```ts
{
  id: "objections",
  label: "Objeciones típicas del lead",
  type: "array",
  path: "objections",
  renderAs: "cards",
  itemSchema: {
    itemNoun: "objeción",
    fields: [
      {
        id: "type",
        label: "Tipo",
        type: "enum",
        path: "type",
        required: true,
        options: [
          { value: "price", label: "Precio" },
          { value: "time", label: "Tiempo" },
          { value: "trust", label: "Confianza" },
          { value: "partner", label: "Socio/pareja (tengo que consultarlo)" },
          { value: "custom", label: "Otra" },
        ],
      },
      {
        id: "rebuttal",
        label: "Respuesta del agente",
        type: "textarea",
        path: "rebuttal",
        rows: 3,
        required: true,
        placeholder: "Ej. Entiendo la preocupación del precio. Si en 30 días…",
      },
      {
        id: "trigger_phrases",
        label: "Frases disparadoras del lead (una por línea)",
        type: "textarea",
        path: "trigger_phrases",
        rows: 2,
        placeholder: "• Está muy caro\n• No tengo presupuesto",
      },
      // strategy: auto-suggested por type en un useEffect del componente
      // (NO field editable en v1 — el copiloto lo asigna). Hidden en cards.
    ],
  },
}
```

**`strategy` auto-sugerido por `type`:** mapeo determinístico client-side o via `structure_objections` tool (§10):

| type | strategy default |
|---|---|
| price | "ROI Reframing" |
| time | "Time Reallocation" |
| trust | "Risk Reversal + Guarantee" |
| partner | "Decision Facilitator" |
| custom | (vacío — editable) |

El form-runtime no expone `strategy` en el `itemSchema` (cards mode, 3 sub-fields visibles) → el campo se completa server-side al serializar. El copilot tool `structure_objections` (§10) puede producir una mejor `strategy` basada en el rebuttal.

### 9.7 Helper "paste-AI" para objections

Botón en el dashboard `psychology`: "Pegá texto y estructurar con IA → structure_objections". Invoca tool del copilot (§10). El resultado llega como card `proposal` con los `objections[]` estructurados — el usuario los aplica via flujo normal de cards.

---

## 10. Form-runtime renderer nuevo — `textarea` con `storeAs: "newline_array"`

### 10.1 Extensión del contrato del schema

**Archivo:** `frontend/src/lib/form-runtime/schema/types.ts`

Agregar al `FieldSchema`:

```ts
export interface FieldSchema {
  // ...campos existentes...

  /**
   * Para fields `type: "textarea"` que persisten a un `string[]` en BE.
   * El renderer hace split/join por `\n` entre UI (string) y state (string[]).
   *
   * UI render:   value.join("\n")
   * UI onChange: e.target.value.split("\n").map(s => s.trim()).filter(Boolean)
   *
   * Sólo válido con type === "textarea". Ignorado en otros tipos.
   */
  storeAs?: "newline_array";
}
```

### 10.2 Renderer

**Archivo a modificar:** `frontend/src/components/form-runtime/inputs/TextareaInput.tsx`

(El renderer actual vive en `components/form-runtime/inputs/` NO en `lib/form-runtime/renderers/`. Mantener ubicación existente — `form-runtime-array.md` spec. Ubicación del nuevo código: mismo `TextareaInput.tsx` con branch `storeAs === "newline_array"`).

```tsx
"use client";

import { InlineEditableTextarea } from "@/components/ui/inline-editable";
import type { BaseInputProps } from "./types";

function joinLines(value: unknown): string {
  if (Array.isArray(value)) {
    return value.filter((v): v is string => typeof v === "string").join("\n");
  }
  return (value as string | null | undefined) ?? "";
}

function splitLines(raw: string): string[] {
  return raw
    .split("\n")
    .map((line) => line.replace(/^[\s•·\-\*]+/, "").trim())
    .filter((line) => line.length > 0);
}

export function TextareaInput({
  field,
  value,
  onChange,
  disabled,
  autoFocus,
  onBlur,
}: BaseInputProps<string | string[] | null>) {
  const isArrayMode = field.storeAs === "newline_array";

  const stringValue = isArrayMode ? joinLines(value) : ((value as string | null) ?? "");

  const handleChange = (next: string) => {
    if (isArrayMode) {
      (onChange as (v: string[]) => void)(splitLines(next));
    } else {
      (onChange as (v: string) => void)(next);
    }
  };

  return (
    <InlineEditableTextarea
      id={field.id}
      value={stringValue}
      onChange={handleChange}
      onBlur={onBlur}
      placeholder={field.placeholder}
      minRows={field.rows ?? 2}
      disabled={disabled}
      autoFocus={autoFocus}
      aria-required={field.required}
    />
  );
}
```

### 10.3 Contrato exacto

| Dirección | Transformación |
|---|---|
| BE → UI | `string[] | null | undefined` → `.filter(Boolean).join("\n")` → `""` si vacío |
| UI → BE | `string` → split `\n` → `replace(/^[\s•·\-\*]+/, "").trim()` (limpia bullets `• - *`) → filter empty → `string[]` |
| `null` inicial | Render `""` (placeholder visible) |
| Blur con `""` | Persiste `[]` (array vacío, NO null) |
| Blur con `"abc"` | Persiste `["abc"]` |

### 10.4 Autosave on-change

Regla `form-runtime-array.md`: autosave on-change **preservado**. El renderer llama `onChange` por keystroke, el `useAutoSave` hook del runtime debouncea a 800ms → PATCH. Sin botón "Guardar".

### 10.5 Tests renderer

`frontend/src/components/form-runtime/inputs/__tests__/inputs.test.tsx` — agregar suite `describe("TextareaInput storeAs newline_array")`:

1. `value: ["a", "b"]` → renders `"a\nb"`.
2. `value: null` → renders `""`.
3. User types `"a\nb\nc"` → `onChange([\"a\", \"b\", \"c\"])`.
4. Bullet cleanup: `"• foo\n- bar"` → `["foo", "bar"]`.
5. Empty line filter: `"foo\n\nbar\n"` → `["foo", "bar"]`.

---

## 11. Nuevo tool copilot — `structure_objections`

**Archivo:** `backend/src/modules/copilot/application/tools/offer_section_tools.py`

### 11.1 Contract

| Aspecto | Valor |
|---|---|
| name | `structure_objections` |
| section_slug | `psychology` |
| args | `{raw_text: str}` (tenant_id y offer_id vienen del context, NO args — ver tools existentes §80) |
| returns | JSON string con `{status, section, draft_fields: {objections: [...]}, confidence, suggestions, sources}` |
| confidence | 0.8 cuando LLM devuelve al menos 1 objection estructurado |
| sources | `["copilot:llm:structure_objections"]` |
| side effects | Ninguna escritura. Emite card `proposal` via `_ok_response` (patrón existente). |

### 11.2 Runtime

1. `tenant_id = get_tenant_id()` — guard `_no_data_response` si None.
2. Si `raw_text.strip()` vacío → `_no_data_response("psychology", "Necesito el texto con las objeciones pegadas.")`.
3. LLM call con `AIActionService` (patrón existente otras tools offer-studio si aplica, o directo `invoke_structured_output` con pydantic model `_StructureObjectionsOutput`).
4. `_StructureObjectionsOutput` schema (local al archivo, no exponer):

```python
from pydantic import BaseModel, Field

class _ObjectionItemOut(BaseModel):
    type: str = Field(description="price | time | trust | partner | custom")
    rebuttal: str = Field(description="Guión de respuesta del agente, tuteo Latam neutro.")
    strategy: str = Field(description="Nombre corto de la estrategia, ej. 'ROI Reframing'.")
    trigger_phrases: list[str] = Field(default_factory=list)

class _StructureObjectionsOutput(BaseModel):
    objections: list[_ObjectionItemOut] = Field(default_factory=list)
```

5. Mapear cada `_ObjectionItemOut` → dict compatible con `ObjectionItem` domain.
6. `return _ok_response("psychology", {"objections": [...]}, suggestions, 0.8, ["copilot:llm:structure_objections"])`.

### 11.3 Decoration + registro

```python
@tool
def structure_objections(raw_text: str) -> str:
    """Estructurar objeciones pegadas en texto libre a formato tipado.

    Sección: psychology.
    El usuario pega texto (p.ej. un email con dudas de prospectos, notas de
    ventas, un resumen de call) y devolvemos objections[] estructuradas
    con type/rebuttal/strategy/trigger_phrases listas para aplicar en el
    aggregate Offer.

    Args:
        raw_text: Texto libre con las objeciones del prospecto. Obligatorio.

    Returns:
        JSON string con draft_fields.objections lista para aplicar.
    """
    # ...implementación...
```

Agregar a `OFFER_SECTION_TOOLS` (líneas 1311–1329):

```python
OFFER_SECTION_TOOLS = [
    adapt_from_brand_identity,
    # ...
    suggest_missing_objections,
    structure_objections,  # NEW
    # ...
]
```

Registro automático: `structure_objections` queda disponible en ROUTE_TOOL_MAP `"offer-studio"` → `"offer_section"` → ya listado (línea 122 registry.py). **Sin cambios en registry.**

### 11.4 Arch/Tenant/PII

- Tenant isolation: `get_tenant_id()` context var (patrón existente).
- PII: `raw_text` input puede contener PII del prospecto. Log con `_sanitize_payload` truncado (regla copilot-resilience.md MAX_PAYLOAD_CHARS=4000). NO almacenar raw_text en trace JSONB más allá del cap.
- No endpoint nuevo (es tool, no route). Tessl `pii-sanitisation` no aplica (no hay FastAPI endpoint).

### 11.5 Observability (copilot-resilience.md)

El tool se beneficia automáticamente del recorder existente: `tool_call` row en `copilot_trace_event` con `data.args` (truncado) + `data.output_preview` (objections count + types).

---

## 12. Sales-agent consumers

### 12.1 `knowledge_builder.py`

**Archivo:** `backend/src/modules/sales_agent/application/services/knowledge_builder.py`

Ya incluye `offers_data = [o.model_dump(mode="json") for o in active_offers]` (línea 77) — los fields nuevos del `Offer` aggregate **se serializan automáticamente** al dict. Sin cambios de código en este archivo.

### 12.2 `agent_identity.j2`

**Archivo:** `backend/src/modules/sales_agent/infrastructure/prompts/templates/agent_identity.j2`

**Política:** additive only (nunca romper los `{% if offer.X %}` existentes). Después del bloque `objections` (línea 107) y antes de `checkout_page_url` (línea 110), agregar:

```jinja
{%- if offer.before_state %}
- **Situación previa típica:** {{ offer.before_state }}
{%- endif %}
{%- if offer.after_state %}
- **Situación objetivo:** {{ offer.after_state }}
{%- endif %}
{%- if offer.why_now %}
- **Por qué ahora:** {{ offer.why_now }}
{%- endif %}
{%- if offer.measurable_outcomes %}
- **Resultados medibles:**
{%- for mo in offer.measurable_outcomes %}
  - {{ mo }}
{%- endfor %}
{%- endif %}
{%- if offer.cultural_trust_barriers %}
- **Barreras culturales Latam a anticipar:**
{%- for cb in offer.cultural_trust_barriers %}
  - {{ cb }}
{%- endfor %}
{%- endif %}
{%- if offer.emotional_triggers %}
- **Disparadores emocionales:** {{ offer.emotional_triggers | join("; ") }}
{%- endif %}
{%- if offer.status_drivers %}
- **Motores de estatus:** {{ offer.status_drivers | join("; ") }}
{%- endif %}
{%- if offer.regret_scenarios %}
- **Escenarios de arrepentimiento (usar en cierre emocional):**
{%- for rs in offer.regret_scenarios %}
  - {{ rs }}
{%- endfor %}
{%- endif %}
{%- if offer.urgency_drivers %}
- **Urgencia honesta:**
{%- for ud in offer.urgency_drivers %}
  - {{ ud }}
{%- endfor %}
{%- endif %}
{%- if offer.scarcity_reason_honest %}
- **Motivo de escasez real:** {{ offer.scarcity_reason_honest }}
{%- endif %}
{%- if offer.refund_process_description %}
- **Proceso de devolución:** {{ offer.refund_process_description }}
{%- endif %}
{%- if offer.bonus_if_act_now %}
- **Bonus por decidir ahora:** {{ offer.bonus_if_act_now }}
{%- endif %}
{%- if offer.final_push_copy %}
- **Cierre sugerido:** {{ offer.final_push_copy }}
{%- endif %}
```

**NO renombrar ni remover** `offer.headline_promise`, `offer.primary_outcome`, `offer.marketing_pain_points`, `offer.marketing_desires`, `offer.objections`, `offer.guarantee_type`, `offer.checkout_page_url`, `offer.calendar_type_id`. Esos bloques se mantienen intactos (líneas 83–113 actuales).

### 12.3 Regla spanish-text.md

Todo el texto user-facing del agent (que acaba yendo al lead) debe ser Latam neutro. Los prompts Jinja no son user-facing directo, pero alimentan el system prompt — instruir al agent en tuteo Latam neutro está en templates upstream (agent_identity.j2 ya usa tuteo neutro).

### 12.4 Sin cambios en `SemanticRouter`

El router (línea 109) sólo consume `pain_points`/`desires`/`objections` para routing semántico — todos ya existen.

---

## 13. Tests de contrato

### 13.1 Backend — arch fitness tests

**Archivo nuevo:** `backend/tests/architecture/test_extraction_section_map_paths.py`

```python
"""Arch test: every path in OFFER_FIELDS_BY_FE_SECTION must exist as a
Pydantic field on the Offer domain aggregate."""
import pytest
from src.modules.offer.domain.extraction_section_map import OFFER_FIELDS_BY_FE_SECTION
from src.modules.offer.domain.offer import Offer


def test_every_mapped_field_exists_on_offer_aggregate() -> None:
    offer_fields = set(Offer.model_fields.keys())
    for slug, field_names in OFFER_FIELDS_BY_FE_SECTION.items():
        for name in field_names:
            assert name in offer_fields, (
                f"OFFER_FIELDS_BY_FE_SECTION[{slug!r}] references "
                f"'{name}' which is not a field of Offer. Either add it to "
                f"the domain aggregate or remove it from the map."
            )
```

**Archivo nuevo:** `backend/tests/architecture/test_offer_narrative_columns_present.py`

```python
"""Arch test: every narrative field on Offer domain maps to a ProductModel column."""
from src.modules.offer.domain.offer import Offer
from src.modules.offer.infrastructure.models.product_model import ProductModel

NARRATIVE_FIELDS = frozenset({
    "before_state", "after_state", "why_now", "measurable_outcomes",
    "cultural_trust_barriers", "emotional_triggers", "status_drivers", "regret_scenarios",
    "refund_process_description", "urgency_drivers", "scarcity_reason_honest",
    "bonus_if_act_now", "final_push_copy",
})


def test_narrative_fields_exist_on_offer_domain() -> None:
    offer_fields = set(Offer.model_fields.keys())
    missing = NARRATIVE_FIELDS - offer_fields
    assert not missing, f"Narrative fields missing on Offer domain: {missing}"


def test_narrative_columns_exist_on_product_model() -> None:
    columns = {c.name for c in ProductModel.__table__.columns}
    missing = NARRATIVE_FIELDS - columns
    assert not missing, f"Narrative columns missing on ProductModel: {missing}"
```

### 13.2 Backend — repository round-trip test

**Archivo nuevo:** `backend/tests/modules/offer/test_offer_repository_narrative.py`

```python
"""Integration: round-trip _to_model + _to_domain preserves narrative fields."""
# Usa la fixture existente `db_session` + `tenant_id`. Crear Offer con
# narrative fields populated, persistir, leer, assert equal.
```

### 13.3 Backend — extraction wave output test

**Archivo nuevo:** `backend/tests/modules/offer/test_offer_extraction_narrative.py`

Fixtures JSON en `backend/tests/modules/offer/fixtures/` con contenido simulado de landing page, assert cada wave Updates incluye los nuevos fields cuando el texto de entrada los contiene.

### 13.4 Frontend — path contract test

**Archivo nuevo:** `frontend/src/features/offer-studio/schemas/__tests__/path-contract.test.ts`

```ts
import { describe, it, expect } from "vitest";
import { offerIdentitySchema } from "../identity.schema";
import { offerPromiseSchema } from "../promise.schema";
import { offerStrategySchema } from "../strategy.schema";
import { offerPsychologySchema } from "../psychology.schema";
import { offerClosingSchema } from "../closing.schema";

// Generated by `backend && .venv/bin/python scripts/dump_offer_fields.py`
// and committed under `frontend/src/features/offer-studio/schemas/__tests__/`.
const ALLOWED_OFFER_PATHS: ReadonlySet<string> = new Set([
  "name", "internal_sku", "headline_promise", "primary_outcome", "time_to_value",
  "before_state", "after_state", "why_now", "measurable_outcomes",
  "value_level", "delivery_model", "target_avatar_match", "anti_avatar_keywords",
  "avatar_id",
  "marketing_pain_points", "marketing_desires", "objections",
  "cultural_trust_barriers", "emotional_triggers", "status_drivers", "regret_scenarios",
  "guarantee_type", "guarantee_terms", "checkout_page_url", "calendar_type_id",
  "onboarding_action", "onboarding_url", "downsell_offer_id", "upsell_offer_id",
  "vsl_link", "refund_process_description", "urgency_drivers",
  "scarcity_reason_honest", "bonus_if_act_now", "final_push_copy",
  "support_duration_days",
]);

describe("Offer schema paths must exist on the Offer aggregate", () => {
  const schemas = [
    offerIdentitySchema,
    offerPromiseSchema,
    offerStrategySchema,
    offerPsychologySchema,
    offerClosingSchema,
  ];
  for (const schema of schemas) {
    for (const field of schema.fields) {
      it(`${schema.key}.${field.id} → path "${field.path}"`, () => {
        expect(ALLOWED_OFFER_PATHS).toContain(field.path);
      });
    }
  }
});
```

Un script Python opcional (`backend/scripts/dump_offer_fields.py`) puede regenerar `ALLOWED_OFFER_PATHS` para evitar drift futuro.

### 13.5 Frontend — renderer test

`frontend/src/components/form-runtime/inputs/__tests__/inputs.test.tsx` — agregar suite `TextareaInput storeAs newline_array` (§10.5).

### 13.6 E2E smoke

No requerido para este change (cobertura por unit tests). Si se agrega: `frontend/e2e/specs/smoke/offer-narrative-sections.spec.ts` — cargar offer con narrative fields populated, verificar que los valores render en las 5 secciones OFFER_LEVEL. Fuera de alcance del contrato inicial.

---

## 14. Impactos que NO deben romperse

Lista exhaustiva (acceptance criteria):

| Feature | Estado esperado | Dónde verificar |
|---|---|---|
| Wizard preset-first | Sin cambio | `frontend/src/features/offer-studio/components/create/*` |
| `PresetPickerStep` / `ConditionalQuestionsStep` | Sin cambio | mismo path |
| `CreateOfferWizard` | Sin cambio | mismo |
| Brand studio extraction | Sin cambio | `backend/src/modules/brand/` intacto |
| Landing page generator | Consume algunos fields del offer — verificar que `landing_generation_service.py` no rompe por fields nuevos (son additive, pero si hace iteración sobre keys del dict, agregarlos no debe romper) | `backend/src/modules/offer/application/services/landing_generation_service.py` |
| Copilot extraction de brand | Sin cambio | `offer_section_tools.py` — sólo agregamos `structure_objections` |
| `offer_completion_service` | Ratios existentes NO cambian. Si se quiere contabilizar los narrativos, hacerlo en PR separado. | `backend/src/modules/offer/application/services/offer_completion_service.py` |
| Arch test `test_domain_purity` | Verde. Pydantic `Field(description=...)` no viola (ya usa Pydantic) | `backend/tests/architecture/test_domain_purity.py` |
| Arch test `test_ddd_boundaries` | Verde. No agregamos cross-module imports. | `backend/tests/architecture/test_conventions.py` |
| Arch test `test_api_contracts` | Verde. `ProductResponse` ya es `response_model=` en todos los endpoints. | `backend/tests/architecture/test_api_contracts.py` |
| Arch test `test_no_hard_deletes` | Verde. Sin cambios en lifecycle. | same |
| Arch test `test_no_sqlalchemy_1x_query_syntax` | Verde. Repo usa `select(...)` y no agregamos `session.query()`. | same |
| Arch test `test_master_data` | Verde. Sin hardcoded currency nuevo. | same |
| Tenant isolation | Verde. Todo query `WHERE tenant_id = ?` ya. | repo |
| `form-runtime-array.md` | Objections en cards mode (3 sub-fields visibles). Default automático del `ArrayInput` aplica. | `frontend/src/components/form-runtime/inputs/ArrayInput.tsx` |
| FE arch tests (10 fitness) | Verdes. No agregamos default exports, no rompemos naming, no cross-feature imports. | `frontend/src/__tests__/architecture/` |
| Autosave on-change | Preservado. Renderer nuevo usa mismo `onChange` → debounced save. | `frontend/src/lib/form-runtime/hooks/use-auto-save.ts` |
| Badge "sección N llena M campos" | Funciona correctamente post-fix. Bug original resuelto. | `OFFER_FIELDS_BY_FE_SECTION` (§7) |
| Offer copilot extractor via URL | Persiste narrativos correctamente → UI los muestra. | `OfferExtractionService` (§8) |
| Currency handling (`currency-handling.md`) | Sin cambio. Nada nuevo monetario. | N/A |
| Spanish neutro Latam (`spanish-text.md`) | Aplicar a descriptions pydantic + prompts Jinja. Tuteo, sin voseo. | §8.1 |

---

## 15. Commits pattern

**Branch:** `development` (regla `parallel-safety.md`).
**Stage por nombre** (nunca `git add -A`).
**Conventional Commits.**

Plan de 7 commits (consolidación sugerida 6↔7 posible si el tool `structure_objections` cae en el mismo PR que FE objections cards):

| # | Scope | Mensaje | Archivos |
|---|---|---|---|
| 1 | migration | `feat(offer): +13 narrative columns via idempotent migration` | `backend/alembic/versions/<ts>_offer_narrative_fields.py` |
| 2 | backend core | `feat(offer): expose narrative fields in model + domain + DTO + repo` | `product_model.py`, `offer.py`, `dto/products.py`, `offer_repository.py`, `extraction_section_map.py` |
| 3 | extraction | `feat(offer): populate narrative fields in extraction waves + prompts` | `offer_extraction_service.py` (sólo prompt keys si cambian), `infrastructure/prompts/templates/*.j2` |
| 4 | frontend schemas | `feat(offer-studio/fe): align schema paths to canonical DB columns` | `identity.schema.ts`, `promise.schema.ts`, `strategy.schema.ts`, `psychology.schema.ts`, `closing.schema.ts` |
| 5 | frontend renderer | `feat(form-runtime): textarea storeAs newline_array renderer` | `lib/form-runtime/schema/types.ts`, `components/form-runtime/inputs/TextareaInput.tsx` |
| 6 | frontend + copilot (consolidado) | `feat(offer-studio,copilot): objections structured cards + structure_objections paste-AI tool` | `psychology.schema.ts` (objections itemSchema), `offer_section_tools.py` (+tool + OFFER_SECTION_TOOLS list), FE button wiring (`features/offer-studio/components/dashboard/...`) |
| 7 | sales_agent | `feat(sales_agent): consume narrative fields in agent_identity prompt` | `agent_identity.j2` |
| 8 | tests | `test(offer): arch + path-contract + renderer coverage for narrative` | `backend/tests/architecture/test_extraction_section_map_paths.py`, `test_offer_narrative_columns_present.py`, `backend/tests/modules/offer/test_offer_repository_narrative.py`, `frontend/src/features/offer-studio/schemas/__tests__/path-contract.test.ts`, `frontend/src/components/form-runtime/inputs/__tests__/inputs.test.tsx` |

**Verificación previo a cada push:**

```bash
# Backend
cd backend && .venv/bin/ruff check src/ tests/ --no-cache
cd backend && .venv/bin/pytest tests/architecture/ -x -q --tb=short
cd backend && .venv/bin/pytest tests/modules/offer/ -v

# Frontend
cd frontend && npx tsc --noEmit
cd frontend && npx eslint src/
cd frontend && npx vitest run src/features/offer-studio/ src/components/form-runtime/
cd frontend && npx vitest run src/__tests__/architecture/
```

Migration test previo a `push origin main`: §2.3 (clone de DB prod → upgrade → drop).

---

## 16. Out-of-band reminders

- **Regla `etl-extraction-contract.md` NO aplica** — este cambio no toca `backend/src/modules/analytics/`.
- **Regla `copilot-resilience.md`:** `structure_objections` usa schema-introspection via pydantic (`ObjectionItem`) — no hardcodea field names.
- **Regla `offer-catalogs.md`:** no tocamos ningún catálogo SSoT. `public_name` label sigue siendo el mismo string user-facing.
- **Arch test meta-guard (futuro):** cuando exista el "cada `*_catalog.py` tiene su `test_*_completeness.py`", este contrato no introduce nuevo catalog.
- **Observability (`copilot-resilience.md`):** el tool nuevo genera rows en `copilot_trace_event` automáticamente vía recorder existente. Sin cambios al recorder.

---

**FIN DEL CONTRATO.**
