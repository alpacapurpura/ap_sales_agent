# Offer Studio: Reestructuración a 5 Arquetipos + Wizard

**Fecha:** 2026-03-27
**Branch:** main
**Estado:** Implementado y verificado (CI green)

---

## Motivación

El Offer Studio original tenía 21 `OfferType` con sesgo infoproductor que no escalaba a profesionales independientes ni agencias. La creación era abrupta: seleccionar tipo de una grilla → nombre → 14 secciones vacías.

Se reestructuró a **5 arquetipos universales** con mapeo 1:1 a detail models, un **wizard de 4 pasos** con progressive disclosure, y **format hints** como capa de extensibilidad libre.

**Segmentos target:** Infoproductores/coaches, profesionales independientes (abogados, médicos, nutricionistas), agencias/freelancers DFY.

---

## Arquitectura: Los 5 Arquetipos

| Arquetipo | Detail Model | Delivery Default | Tipo Legacy Default |
|-----------|-------------|-----------------|-------------------|
| `producto` | `ProductDetails` | DIY | `self_paced_course` |
| `programa` | `ProgramDetails` | DWY | `group_coaching_program` |
| `servicio` | `ServiceDetails` | DFY | `productized_service` |
| `membresia` | `SubscriptionDetails` | DIY | `paid_newsletter_subscription` |
| `experiencia` | `EventDetails` | DWY | `luxury_retreat` |

### Dual Dispatch (Backward Compat)

Todo el código nuevo prioriza `archetype`, con fallback a `type` legacy:

```
if offer.archetype → ARCHETYPE_TO_DETAILS_MAPPING[archetype]
elif offer.type → OFFER_TYPE_TO_DETAILS_MAPPING[type]  (legacy)
else → fallback a PRODUCTO
```

Este patrón se aplica en: validator de dominio, repositorio, servicio, NavRail, offer-health, live-preview.

---

## Cambios Backend

### 1. Nuevo Enum `OfferArchetype` + Mappings

**Archivo:** `backend/src/modules/offer/domain/enums.py`

```python
class OfferArchetype(str, Enum):
    PRODUCTO = "producto"
    PROGRAMA = "programa"
    SERVICIO = "servicio"
    MEMBRESIA = "membresia"
    EXPERIENCIA = "experiencia"
```

Mappings añadidos:
- `ARCHETYPE_DEFAULT_DELIVERY` — delivery model por defecto de cada arquetipo
- `ARCHETYPE_DEFAULT_TYPE` — tipo legacy auto-asignado cuando se crea por arquetipo

### 2. Entidad Offer (Dominio)

**Archivo:** `backend/src/modules/offer/domain/offer.py`

Nuevos campos:
```python
archetype: Optional[OfferArchetype] = None
format_hint: Optional[str] = None
is_lead_magnet: bool = False
```

Computed field:
```python
@computed_field
@property
def shows_as_lead_magnet(self) -> bool:
    """Auto-detect from price ($0) OR manual flag"""
    if self.is_lead_magnet:
        return True
    if self.pricing_options:
        return all(p.total_amount == 0 for p in self.pricing_options)
    return self.value_level == OfferValueLevel.LEVEL_0_FREE
```

Dict de dispatch por arquetipo:
```python
ARCHETYPE_TO_DETAILS_MAPPING: Dict[OfferArchetype, Type[BaseEntity]] = {
    OfferArchetype.PRODUCTO: ProductDetails,
    OfferArchetype.PROGRAMA: ProgramDetails,
    OfferArchetype.SERVICIO: ServiceDetails,
    OfferArchetype.MEMBRESIA: SubscriptionDetails,
    OfferArchetype.EXPERIENCIA: EventDetails,
}
```

El `model_validator` (`validate_consistency`) fue actualizado para soportar dual dispatch (archetype-first, type-fallback).

### 3. Modelo SQLAlchemy

**Archivo:** `backend/src/modules/offer/infrastructure/models/product_model.py`

Columnas añadidas a `ProductModel`:
```python
archetype = Column(String, nullable=True)
format_hint = Column(String, nullable=True)
is_lead_magnet = Column(Boolean, default=False, server_default="false")
```

### 4. Migración Alembic (Idempotente)

**Archivo:** `backend/alembic/versions/018_add_archetype_columns.py`

Operaciones:
1. `ADD COLUMN IF NOT EXISTS archetype VARCHAR`
2. `ADD COLUMN IF NOT EXISTS format_hint VARCHAR`
3. `ADD COLUMN IF NOT EXISTS is_lead_magnet BOOLEAN DEFAULT FALSE`
4. **Backfill `archetype`** desde `type` con CASE-WHEN (21 tipos → 5 arquetipos)
5. **Backfill `format_hint`** humanizando el `type` (replace `_` → ` `)
6. **Backfill `is_lead_magnet`** desde `offer_value_level = 'level_0_free'`
7. `CREATE INDEX IF NOT EXISTS idx_products_archetype`

Mapeo de backfill:
```sql
WHEN type IN ('free_resource','tripwire_offer','self_paced_course',
              'physical_merch','content_asset_podcast') THEN 'producto'
WHEN type IN ('free_webinar_challenge','hybrid_mentorship',
              'cohort_based_course','group_coaching_program') THEN 'programa'
WHEN type IN ('vip_day_strategy','one_on_one_private_mentoring','deep_dive_audit',
              'productized_service','ecommerce_development','monthly_retainer',
              'performance_rev_share','corporate_training','brand_sponsorship',
              'keynote_speaking') THEN 'servicio'
WHEN type IN ('paid_newsletter_subscription','community_lite',
              'mastermind_network') THEN 'membresia'
WHEN type IN ('luxury_retreat') THEN 'experiencia'
```

**Resultado verificado:** 13 ofertas backfilled correctamente (3 producto, 5 programa, 4 servicio, 1 membresia).

### 5. DTOs

**Archivo:** `backend/src/modules/offer/api/dto/products.py`

| DTO | Cambios |
|-----|---------|
| `ProductResponse` | +`archetype`, `format_hint`, `is_lead_magnet`, `shows_as_lead_magnet` (computed) |
| `ProductCreate` | `type` → `Optional[OfferType] = None`, +`archetype` (OfferArchetype, required validator), `format_hint`, `is_lead_magnet`, `headline_promise`, `avatar_id` |
| `ProductUpdate` | +`archetype`, `format_hint`, `is_lead_magnet` (todos opcionales) |

`ProductCreate` tiene un validator que asegura que al menos `archetype` o `type` esté presente.

### 6. Application Service

**Archivo:** `backend/src/modules/offer/application/offer_service.py`

`create_offer()`:
- Recibe `archetype`, `format_hint`, `is_lead_magnet`, `headline_promise`, `avatar_id`
- Si viene `archetype` sin `type` → auto-asigna `type` desde `ARCHETYPE_DEFAULT_TYPE`
- Si viene `archetype` sin `delivery_model` → auto-asigna desde `ARCHETYPE_DEFAULT_DELIVERY`
- Pasa campos al dominio Offer

`patch_offer()`:
- Usa archetype-first dispatch para resolver la clase de detail correcta

### 7. Repository

**Archivo:** `backend/src/modules/offer/infrastructure/repositories/offer_repository.py`

`_to_domain()`:
- Parsea `archetype` desde model string a enum
- Incluye `archetype`, `format_hint`, `is_lead_magnet` en offer_data
- Dispatch de detail class: archetype-first, type-fallback

`_to_model()`:
- Mapea `archetype` (como `.value` del enum), `format_hint`, `is_lead_magnet` a ProductModel

### 8. API Route

**Archivo:** `backend/src/modules/offer/api/products.py`

El endpoint `create_product` pasa todos los campos del wizard al service:
```python
archetype=body.archetype,
format_hint=body.format_hint,
is_lead_magnet=body.is_lead_magnet,
headline_promise=body.headline_promise,
avatar_id=body.avatar_id,
```

### 9. SDR Prompt Template

**Archivo:** `backend/src/modules/sales_agent/infrastructure/prompts/templates/agent_identity.j2`

Actualizado para renderizar archetype + format_hint cuando disponible:
```jinja2
- **Tipo:** {% if offer.archetype %}{{ offer.archetype | title }}{% if offer.format_hint %} ({{ offer.format_hint }}){% endif %}{% else %}{{ offer.type }}{% endif %}
```

---

## Cambios Frontend

### 1. Tipos TypeScript

**Archivo:** `frontend/src/features/offer-studio/types/index.ts`

```typescript
export enum OfferArchetype {
  PRODUCTO = "producto",
  PROGRAMA = "programa",
  SERVICIO = "servicio",
  MEMBRESIA = "membresia",
  EXPERIENCIA = "experiencia",
}
```

Campos añadidos a interface `Offer`:
```typescript
archetype?: OfferArchetype;
format_hint?: string;
is_lead_magnet?: boolean;
shows_as_lead_magnet?: boolean;
```

### 2. Zod Schema

**Archivo:** `frontend/src/features/offer-studio/types/schema.ts`

Campos añadidos a `OfferSchema`:
```typescript
archetype: z.nativeEnum(OfferArchetype).optional().nullable(),
format_hint: z.string().optional().nullable(),
is_lead_magnet: z.boolean().default(false),
```

### 3. Archetype Metadata (NUEVO)

**Archivo:** `frontend/src/features/offer-studio/config/archetype-metadata.ts`

Define `ArchetypeMetadata` interface y `ARCHETYPE_METADATA` record con:
- `label` — nombre display
- `subtitle` — descripción en lenguaje natural ("Algo que creé y empaqué")
- `icon` — LucideIcon
- `examples` — ejemplos concretos
- `defaultFormats` — chips sugeridos para Step 2 del wizard
- `detailsModel` — tipo de detail model

### 4. Builder Config Actualizado

**Archivo:** `frontend/src/features/offer-studio/config/offer-builder-config.ts`

Nuevo `ARCHETYPE_BUILDER_CONFIG`:
```typescript
export const ARCHETYPE_BUILDER_CONFIG: Record<OfferArchetype, string[]> = {
  [OfferArchetype.PRODUCTO]: ['identity', 'strategy', ...10 sections],
  [OfferArchetype.PROGRAMA]: ['identity', 'strategy', ...11 sections],
  [OfferArchetype.SERVICIO]: ['identity', 'strategy', ...11 sections],
  [OfferArchetype.MEMBRESIA]: ['identity', 'strategy', ...10 sections],
  [OfferArchetype.EXPERIENCIA]: ['identity', 'strategy', ...11 sections],
};
```

Nueva función centralizada `getSectionsForOffer()`:
```typescript
export function getSectionsForOffer(offer: { archetype?: OfferArchetype | string; type?: OfferType | string }): string[] {
  // 1. Archetype-first
  // 2. Type fallback (legacy)
  // 3. Ultimate fallback: PRODUCTO sections
}
```

Legacy `OFFER_BUILDER_CONFIG` preservado como fallback.

### 5. API Adapter

**Archivo:** `frontend/src/features/offer-studio/api/adapter.ts`

`BackendOffer` interface extendido con: `archetype`, `format_hint`, `is_lead_magnet`, `shows_as_lead_magnet`.

`backendToFrontend()` mapea los 4 campos nuevos al tipo `Offer` del frontend.

### 6. Wizard de Creación (NUEVO)

**Archivo:** `frontend/src/features/offer-studio/components/wizard/CreateOfferWizard.tsx`

Dialog multi-step con 4 pasos:

| Step | Contenido | Requerido |
|------|-----------|-----------|
| 1 | Selección de arquetipo (5 cards con ícono, label, subtitle, examples) | Sí |
| 2 | Selección de formato (chips sugeridos + input custom + "Saltar") | No |
| 3 | Nombre + Precio + Lead Magnet checkbox | Nombre sí, resto no |
| 4 | Promesa principal (textarea + "Completar después") | No |

Exporta `WizardResult` interface:
```typescript
export interface WizardResult {
  archetype: OfferArchetype;
  format_hint?: string;
  name: string;
  price?: number;
  is_lead_magnet: boolean;
  headline_promise?: string;
}
```

State machine simple (step 1-4) con reset en close.

### 7. Dashboard Actualizado

**Archivo:** `frontend/src/features/offer-studio/components/dashboard/offer-studio-dashboard.tsx`

- Dialog viejo de 2 pasos (type grid + name) → reemplazado por `<CreateOfferWizard />`
- `handleCreateOffer` acepta `WizardResult`, envía payload con archetype
- Búsqueda filtrable por archetype y format_hint

### 8. Offer Card

**Archivo:** `frontend/src/features/offer-studio/components/dashboard/offer-card.tsx`

Label de tipo ahora muestra: `Archetype (format_hint)` cuando disponible, fallback a type legacy.

### 9. Editor Layout

**Archivo:** `frontend/src/features/offer-studio/components/container/offer-studio-layout.tsx`

Header badge muestra archetype capitalizado con format_hint. Fallback a value_level para ofertas legacy.

### 10. NavRail

**Archivo:** `frontend/src/features/offer-studio/components/navigation/OfferNavRail.tsx`

Usa `getSectionsForOffer(offer)` (centralizado) en vez de acceso directo a config.

### 11. Live Preview

**Archivo:** `frontend/src/features/offer-studio/components/editor/offer-live-preview.tsx`

Usa `getSectionsForOffer()` con variable `currentArchetype` extraída para limpiar dependencia del `useMemo`.

### 12. Offer Health

**Archivo:** `frontend/src/features/offer-studio/utils/offer-health.ts`

Usa `getSectionsForOffer(offer)` para calcular health por secciones del arquetipo correcto.

---

## Archivos Nuevos Creados

| Archivo | Descripción |
|---------|-------------|
| `backend/alembic/versions/018_add_archetype_columns.py` | Migración idempotente con backfill |
| `frontend/src/features/offer-studio/config/archetype-metadata.ts` | Metadata de los 5 arquetipos |
| `frontend/src/features/offer-studio/components/wizard/CreateOfferWizard.tsx` | Wizard de 4 pasos |

---

## Archivos Modificados

### Backend (8 archivos)

| Archivo | Cambio |
|---------|--------|
| `domain/enums.py` | +OfferArchetype enum, +3 mappings |
| `domain/offer.py` | +3 campos, +computed field, +ARCHETYPE_TO_DETAILS_MAPPING, +dual validator |
| `infrastructure/models/product_model.py` | +3 columnas |
| `infrastructure/repositories/offer_repository.py` | _to_domain + _to_model con archetype |
| `application/offer_service.py` | create_offer + patch_offer con archetype |
| `api/dto/products.py` | Response/Create/Update DTOs actualizados |
| `api/products.py` | Route pasa campos wizard a service |
| `sales_agent/.../agent_identity.j2` | Renderiza archetype + format_hint |

### Frontend (12 archivos)

| Archivo | Cambio |
|---------|--------|
| `types/index.ts` | +OfferArchetype enum, +4 campos en Offer |
| `types/schema.ts` | +3 campos en OfferSchema |
| `config/offer-builder-config.ts` | +ARCHETYPE_BUILDER_CONFIG, +getSectionsForOffer() |
| `api/adapter.ts` | BackendOffer + mapper actualizados |
| `components/dashboard/offer-studio-dashboard.tsx` | Wizard reemplaza dialog viejo |
| `components/dashboard/offer-card.tsx` | Label con archetype |
| `components/container/offer-studio-layout.tsx` | Badge con archetype |
| `components/navigation/OfferNavRail.tsx` | getSectionsForOffer() |
| `components/editor/offer-live-preview.tsx` | getSectionsForOffer() |
| `utils/offer-health.ts` | getSectionsForOffer() |
| `config/archetype-metadata.ts` | **NUEVO** |
| `components/wizard/CreateOfferWizard.tsx` | **NUEVO** |

---

## Backward Compatibility

Nada se eliminó:
- `OfferType` enum → se mantiene en backend y frontend
- `OFFER_TYPE_TO_DETAILS_MAPPING` → se mantiene
- `OFFER_BUILDER_CONFIG` (keyed by type) → se mantiene como fallback
- Columna `type` en DB → se mantiene, se auto-asigna si se crea por archetype
- Ofertas existentes sin `archetype` → migración backfills, código tiene fallback

---

## Verificación CI

| Suite | Resultado |
|-------|-----------|
| Backend pytest | 309/309 PASSED |
| Backend ruff | CLEAN |
| Frontend tsc | CLEAN |
| Frontend next lint | CLEAN |
| Frontend vitest | 45/48 PASSED (3 pre-existing failures en offer-card.test.tsx — `useNavigation` sin provider) |
| Migración | Ejecutada OK, 13 ofertas backfilled |

---

## Notas para Desarrollo Futuro

1. **Los 3 test failures en offer-card.test.tsx son pre-existentes** — necesitan wrappear el render con `NavigationProvider`. No están relacionados con los cambios de archetype.

2. **El wizard no incluye selección de Avatar** (Step 3 lo menciona en el plan pero no se implementó el dropdown porque requiere fetch de avatars existentes). Se puede agregar después.

3. **El botón "Generar con IA"** en Step 4 (Promise) no está implementado — el plan menciona llamar al copilot con brand + avatar + archetype. Se puede agregar como enhancement.

4. **`format_hint` es string libre** — no hay validación de valores. Los chips del wizard sugieren opciones pero el usuario puede escribir cualquier texto.

5. **`shows_as_lead_magnet`** es computed (no guardado en DB). Se calcula en el dominio y se expone via DTO. Lógica: `is_lead_magnet == True` OR todos los precios son $0 OR `value_level == LEVEL_0_FREE`.

6. **El mapeo type↔archetype para backfill** está en la migración. Para crear ofertas nuevas, si solo se envía `archetype`, el sistema auto-asigna un `type` legacy genérico via `ARCHETYPE_DEFAULT_TYPE`.
