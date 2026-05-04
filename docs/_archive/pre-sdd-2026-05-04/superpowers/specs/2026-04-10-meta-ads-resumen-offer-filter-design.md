# Meta Ads Resumen — Filtro Unificado por Offer

**Fecha:** 2026-04-10
**Módulos afectados:** `advertising` (backend), `growth-studio/meta-ads` (frontend), `shared/domain/locale` (backend)
**Tipo:** Feature + fix de confiabilidad + remediación de deuda técnica
**Branch:** `development`

## Contexto y objetivo

La pestaña **Resumen** del dashboard Meta Ads es el vistazo diario del emprendedor — en palabras del usuario: *"el negocio en un solo dashboard"*. Un usuario que quiere ver el resumen de un producto/servicio específico debería poder hacer click en una oferta y que **toda la información abajo (KPIs, gráfico de inversión y embudo) se actualice** para mostrar solo esa oferta. Las otras pestañas (Campañas, Creativos, Audiencia, Costos) son para diagnóstico profundo, no para el vistazo diario.

**Atributo no negociable:** **confiabilidad de datos**. Si un número no puede computarse con certeza para un filtro, se muestra `—` con tooltip explicativo. Jamás un número aproximado sin etiqueta.

## Estado actual (verificado)

**`ResumenTab.tsx`** tiene este layout:
1. Health Check
2. Unassigned Banner
3. 6 KPI cards (globales)
4. **Offer Segmenter** ← actualmente abajo de los KPIs
5. Gráfico Inversión vs Resultados (ya reacciona al filtro)
6. Embudo de conversión (NO reacciona al filtro)

**Backend — `/advertising/metrics-by-offer`** (`metrics_by_offer_service.py:101-201`) ya retorna:
- Por offer: `spend`, `primary_result_count`, `primary_cost_per_result`, `roas` (si aplica), y un `secondary_metrics` dict con `{impressions, clicks, reach, ctr, cpc, cpm}`
- `unassigned`: `target_count`, `total_spend`, `impressions`, `clicks`
- `branding_only`: `target_count`, `total_spend`, `reach`, `impressions`

**Problemas identificados en el backend actual:**

1. **Bug de confiabilidad — reach se suma incorrectamente.** `metrics_by_offer_service.py` suma filas diarias de `reach` como si fuera aditiva. Reach es "personas únicas" y no es aditiva ni entre días ni entre campañas. El valor actual está sistemáticamente inflado.
2. **Funnel no existe por offer.** `MetaAdsMiniFunnel` lee `data.funnel.steps` del endpoint `/channel-dashboard/meta-ads`, que es global. Al filtrar por offer, el embudo muestra datos del channel completo (desconectado del filtro).
3. **Deuda técnica — `resolve_period_window` usa `date.today()` naive.** No respeta `TenantLocale.timezone` aunque `shared/domain/locale.py` ya define la estructura y `TenantModel` ya tiene `timezone` en DB. Off-by-one para tenants fuera de UTC.
4. **Branding/Unassigned DTOs** no exponen `ctr/cpm/cpc` (triviales de computar desde campos ya disponibles).

## Diseño

### Principio rector: una sola fuente de verdad por filtro

El `OfferSegmenter` es el único estado que condiciona qué ve el usuario en Resumen. KPIs, gráfico de Inversión y embudo leen del mismo objeto de datos derivado del filtro. Un solo endpoint extendido, un solo payload, cambios de filtro instantáneos sin refetch.

### Nuevo layout de ResumenTab

```
1. Health Check panel             (sin cambios)
2. UnassignedBanner (condicional) (sin cambios)
3. OfferSegmenter                 ← MOVIDO aquí (entre Health Check y KPIs)
4. 6 KPI cards                    ← reactivos al filtro + tooltips explicativos
5. Inversión vs Resultados        ← ya reactivo
6. Embudo de conversión           ← NUEVO: reactivo al filtro + tooltips
```

### Backend — extensión de `/metrics-by-offer`

#### Cambios en DTOs (`metrics_by_offer_dto.py`)

**Nuevo tipo reutilizable:**
```python
class FunnelStepDTO(_CamelModel):
    label: str              # "Impresiones", "Clics", ...
    metric_name: str        # "impressions", "clicks", ...
    value: float
    conversion_rate_from_previous: float | None  # null para el primer paso
```

**`OfferMetricsDTO` — añadir:**
- `funnel: list[FunnelStepDTO]` — 5 pasos recomputados filtrando por las campañas asociadas a esa offer

**`BrandingAggregateDTO` — añadir:**
- `ctr: float` — `clicks / impressions * 100`
- `cpm: float` — `spend / impressions * 1000`
- `cpc: float` — `spend / clicks`
- `frequency: float | None` — `impressions / reach` (solo si reach es correcto)
- `funnel: list[FunnelStepDTO]` — 5 pasos para campañas de branding
- **Nota:** `reach` se recalcula correctamente (ver abajo)

**`UnassignedAggregateDTO` — añadir:**
- `ctr: float`, `cpm: float`, `cpc: float`
- `reach: float | None` (si disponible en `period_metrics`)
- `funnel: list[FunnelStepDTO]` — 5 pasos para campañas sin asignar

**`MetricsByOfferDTO` — añadir (nivel raíz):**
- `funnel_all: list[FunnelStepDTO]` — estado "Todas" (5 pasos agregados de TODAS las campañas meta-ads del tenant)
- `reach_all: float | None` — reach correcto a nivel channel para el período

**Justificación del `funnel_all` en vez de reusar el existente:** el endpoint `/channel-dashboard/meta-ads` devuelve funnel global, pero el timezone es diferente y los pasos vienen de `channel_dashboard_service.py`. Para que "Todas" y "[Offer X]" sean comparables 1:1 deben construirse con la misma lógica, mismo timezone, mismo filtro base.

#### Fix de reach — lookup a `period_metrics`

Ubicación: `metrics_by_offer_service.py` (método `run` y helpers de agregación).

**Nuevo comportamiento:**
1. Al resolver el período, además de cargar `official_metrics` (daily rows), cargar `period_metrics` filtrado por:
   - `tenant_id = tenant_id`
   - `channel_slug = "meta-ads"`
   - `metric_name = "reach"`
   - `period_start = start_date` y `period_end = end_date` (o el período más cercano disponible; ver "Fallback de reach")
2. Para cada offer, hacer lookup de reach por `campaign_id IN (associated_campaigns)`. Si hay múltiples filas (una por campaña), **retornar `null` y mostrar `—` en UI** porque la suma entre campañas sigue siendo incorrecta (overlap de audiencia).
3. Para el estado "Todas" (`reach_all`), usar el row a nivel channel (`campaign_id IS NULL`).
4. Para branding/unassigned, misma regla: si hay múltiples campañas, retornar `null`.

**Fallback de reach (si `period_metrics` no tiene filas para el período exacto):**
- Retornar `null` — NO intentar derivarlo de `official_metrics`.
- La UI mostrará `—` con tooltip: *"Reach disponible solo al cierre del período. Se actualiza cada 24h."*
- Documentar en los tests que este fallback es intencional, no un bug.

**Excepción:** para **una sola campaña asociada a una offer**, el reach de esa campaña en `period_metrics` es correcto y se muestra directamente.

**Riesgo a verificar en Fase 1 (architect):** Se asume que `period_metrics` almacena reach a **nivel de campaña** para `meta-ads` (columna `campaign_id` existe, según `period_metrics_model.py`). Si el ETL actual solo inserta reach a **nivel channel** (`campaign_id IS NULL`), entonces **el reach por offer de 1 campaña también será `null`** hasta que el ETL se actualice. El architect debe verificar esto consultando datos reales y ajustar el spec si necesario. No bloquea la feature — solo cambia cuántos casos muestran `—`.

#### Fix de timezone — wire `TenantLocale.timezone`

Ubicación: `backend/src/modules/advertising/infrastructure/repositories/metrics_repository.py:97-104` (función `resolve_period_window`).

**Antes:**
```python
def resolve_period_window(period: str) -> tuple[date, date]:
    today = date.today()
    ...
```

**Después:**
```python
from zoneinfo import ZoneInfo
from datetime import datetime

def resolve_period_window(period: str, tz: str = "UTC") -> tuple[date, date]:
    """Translate a '7d'|'30d'|'90d' period to a (start, end) date tuple in the tenant's timezone."""
    try:
        tenant_tz = ZoneInfo(tz)
    except Exception:
        tenant_tz = ZoneInfo("UTC")
    today = datetime.now(tenant_tz).date()
    days_map = {"7d": 7, "30d": 30, "90d": 90}
    days = days_map.get(period, 30)
    start = today - timedelta(days=days - 1)
    return start, today
```

**Cadena de dependency injection:**
1. Crear/usar helper `get_tenant_locale(tenant_id, db)` en `shared/` que carga `TenantModel.timezone` + `TenantModel.default_currency` y retorna un `TenantLocale`. Si ya existe un `get_tenant_locale()` como FastAPI dependency (por `master-data.md` rule), reutilizarlo.
2. `MetricsByOfferService.run(tenant_id, period, tenant_locale)` acepta el locale como parámetro.
3. Ruta `/metrics-by-offer` inyecta `TenantLocale` vía `Depends(get_tenant_locale)`.
4. `resolve_period_window(period, tenant_locale.timezone)` usa el timezone real.
5. Tests cubren tenants en `America/Lima` y `America/Bogota` con datos cerca del boundary de medianoche.

**Nota:** Si `get_tenant_locale` aún no existe como dependency (aunque la rule lo menciona), la tarea del architect agent incluye crearlo en `shared/` y reutilizarlo.

#### Funnel por offer — recomputación

Ubicación: `metrics_by_offer_service.py` — nuevo helper `_build_funnel_for_campaigns(rows, campaign_ids)`.

**Algoritmo:**
1. Recibe todas las filas de `official_metrics` ya cargadas + el set de `campaign_ids` a filtrar.
2. Filtra `rows` a las que pertenecen a `campaign_ids` (o a `ad_set_ids` si la asociación es por ad set).
3. Suma por `metric_name` los 5 nombres: `impressions`, `clicks`, `meta_landing_page_views`, `meta_leads`, `conversions`.
4. Construye 5 `FunnelStepDTO` con `label` en español y `conversion_rate_from_previous` = `current / previous * 100` (null para el primer paso, null si previous=0).

**Reutiliza para:**
- Cada `OfferMetricsDTO.funnel` (filtered por campañas asociadas a la offer)
- `BrandingAggregateDTO.funnel` (filtered por `branded_campaign_ids`)
- `UnassignedAggregateDTO.funnel` (filtered por unassigned campaign ids)
- `funnel_all` (sin filtro = todas las campañas meta-ads del tenant)

### Frontend — refactor de `ResumenTab`

#### Hook unificado

**Nuevo hook:** `useResumenViewData(metricsByOffer, channelData, selectedOfferId, tenantCurrency)` en `features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/hooks/useResumenViewData.ts`.

**Entrada:**
- `metricsByOffer: MetricsByOffer | undefined` (response del endpoint extendido)
- `channelData: ChannelDashboardData | undefined` (response existente, solo usado como fallback si la extensión backend no está desplegada todavía — ver "Compatibilidad")
- `selectedOfferId: OfferSegmenterSelection`
- `tenantCurrency: string`

**Salida:**
```typescript
interface ResumenViewData {
  kpis: ResumenKpiCard[];        // array contextual según filtro
  timeSeries: MetricTimeSeries[]; // alimenta InversionChart
  funnel: FunnelStep[];           // alimenta MetaAdsMiniFunnel
  contextLabel: string;           // "Todas las offers" | "Offer: X" | "Campañas de branding" | "Sin asignar"
  emptyState: ResumenEmptyState | null; // si el filtro no tiene data
}

interface ResumenKpiCard {
  key: string;
  label: string;              // "Inversión", "ROAS", ...
  value: number | null;       // null → render "—"
  unit: 'currency' | 'percentage' | 'ratio' | 'count';
  currency?: string;
  deltaPct?: number | null;
  higherIsBetter?: boolean;
  tooltip: string;            // requerido, siempre presente
  unavailableReason?: string; // solo si value === null
}
```

#### Conjuntos contextuales de KPIs

**Filtro `all`:**
1. Inversión (`spend`)
2. ROAS
3. Resultados (`conversions` — suma ponderada de todas las offers)
4. CPA
5. CTR
6. Reach (del campo `reachAll`)

**Filtro `[offerId]` (offer específica):**
1. Inversión
2. ROAS (si `offer.roas != null`; si no, "Costo por resultado")
3. Resultados (con label = `offer.primaryMetricName`, e.g., "Leads", "Compras")
4. CPA (con label = `offer.primaryMetricName === 'Leads' ? 'CPL' : 'CPA'`)
5. CTR
6. Reach (valor si `reach != null`; `—` con tooltip si es null)

**Filtro `branding`:**
1. Inversión
2. Alcance (`reach`, `—` si multi-campaña y no reconciliable)
3. Impresiones
4. CPM
5. Frecuencia (`impressions/reach`, `—` si reach no reconciliable)
6. Campañas activas (`targetCount`)

> Nota: branding típicamente es multi-campaña, así que en la mayoría de tenants se mostrará `—` en alcance y frecuencia. El tooltip debe explicar que esos valores solo están disponibles cuando hay una sola campaña de branding (o cuando el ETL genera un row de reach consolidado para el segmento branding, que es trabajo futuro).

**Filtro `unassigned`:**
1. Inversión
2. Impresiones
3. Clics
4. CTR
5. Campañas sin asignar (`targetCount`)
6. **Card de acción** — botón "Asignar ahora" (no es un KPI, es una CTA contextual con background rojo/warning)

#### Tooltips — contenido (requerido para cada KPI y cada paso del funnel)

Entregable del agente **ux-designer**: archivo `features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/copy/tooltips.ts` con el texto completo en español, consistente, orientado a que un emprendedor sin background en marketing entienda cómo interpretar cada métrica.

Requisitos de los tooltips:
- **Qué es** (definición en una frase)
- **Por qué importa** (qué decisión toma con este número)
- **Rango sano** cuando aplica (ej.: "CTR bueno en e-commerce: 1-2%")
- **Qué hacer si está mal** (cuando aplica, en una frase)
- Máximo ~3 líneas por tooltip
- Tildes, ñ y signos correctos (regla `spanish-text.md`)

Ejemplo para CTR:
> CTR mide qué % de personas que ven tu anuncio hacen clic. Arriba de 1% es bueno; abajo de 0.5% indica que el anuncio no engancha — revisá creativa o audiencia.

#### Compatibilidad durante el deploy

El backend y el frontend se deployan juntos (misma branch, mismo commit). El frontend asume que la extensión backend ya está activa. No hay fallback a la versión vieja del DTO — si falta un campo nuevo, se muestra `—` con tooltip.

### Visualización — especialistas por gráfico

**Requisito del usuario:** cada gráfico debe tener atención específica de un especialista en visualización de datos.

**Gráficos bajo auditoría visual:**
1. **KPI Cards** — tipografía, jerarquía visual, spacing, color de delta, ubicación del tooltip, accesibilidad (aria-label con texto del tooltip), estado `—` vs valor normal.
2. **InversionChart** — eje secundario contextual al filtro, colores break-even, tooltip del chart rico en contexto, subtítulo narrativo (*"Cada $1 invertido en Producto X generó $2.40"*).
3. **MetaAdsMiniFunnel** — estado cuando un paso es 0 (¿muestra "—" o width 0?), tasa de conversión entre pasos visible sin hover, color ramp por tasa.
4. **OfferSegmenter** — visual del chip activo, spacing horizontal en mobile, contraste de chips branding vs unassigned (que son "especiales").

Cada uno será iterado por un agente especializado con skill `frontend-design` (o subagente general-purpose con prompt de data-viz senior) ANTES del merge.

### Edge cases

| Escenario | Comportamiento |
|---|---|
| Período sin datos | UI muestra "No hay datos para este período" en cada sección (no errores) |
| Offer sin campañas asociadas | KPIs = `—`, funnel = todos ceros con mensaje "Esta offer aún no tiene campañas asignadas", CTA "Asignar campañas" |
| Pixel no configurado (`conversions=0` para offer de purchase) | ROAS/CPA muestran `—` con tooltip "Requiere Meta Pixel configurado" |
| Reach de múltiples campañas | `—` con tooltip "Reach por offer no disponible cuando hay >1 campaña por solapamiento de audiencias. Ver pestaña Audiencia." |
| Backend sin datos de `period_metrics` aún | Reach = `—` con tooltip "Reach se actualiza cada 24h" |
| Filtro "Sin asignar" cuando `unassignedCount == 0` | El chip no se muestra (ya implementado en OfferSegmenter) |
| Filtro "Branding" cuando `hasBranding == false` | El chip no se muestra (ya implementado) |
| Offer con `metric_unavailable_reason != null` | KPIs de resultados = `—` con tooltip explicando razón ("metric_not_supported" → "Esta offer no soporta métricas de Meta"; "no_events_reported" → "No se reportaron eventos en este período") |

### Error handling

- Errores 5xx del endpoint → ErrorBoundary con mensaje genérico + botón "Reintentar"
- Errores 401 → auto-logout (ya manejado por `fetchClient`)
- Timezone inválido (fallback a UTC) → warning en logs backend + funciona normalmente
- Campos faltantes en response → renderizan `—` (no crashean)

### Testing

#### Backend

1. **Service tests** (`tests/modules/advertising/application/services/test_metrics_by_offer_service.py`):
   - Caso "Todas": funnel_all incluye suma de todas las campañas, reach_all viene de period_metrics channel-level
   - Caso offer con 1 campaña: reach correcto, funnel por offer es subset
   - Caso offer con 2+ campañas: `reach == null` (no inventar)
   - Caso branding: ctr/cpm/cpc computados, funnel solo de campañas excluded_branding
   - Caso unassigned: ctr computado, funnel solo de campañas sin asociación
   - Caso período sin datos en official_metrics: retorna estructura vacía sin errores
   - Caso período sin datos en period_metrics: reach = null (no fallback a suma)
   - Caso offer con conversions=0 (pixel off): roas/cpa = null

2. **Timezone tests** (`tests/modules/advertising/infrastructure/test_metrics_repository.py`):
   - `resolve_period_window("30d", "America/Lima")` vs `"UTC"` difiere en boundary casos
   - Timezone inválido → fallback a UTC sin crash

3. **Arch fitness** — ningún nuevo cross-module import, todos los endpoints con `response_model=`.

#### Frontend

1. **Hook test** (`hooks/__tests__/useResumenViewData.test.ts`):
   - Filtro `all` → 6 KPIs correctos
   - Filtro offer válida → KPIs contextuales con labels de la offer
   - Filtro branding → set de branding
   - Filtro offer inexistente → empty state
   - Reach null → card muestra `—` con `unavailableReason`

2. **Component tests** (`tabs/__tests__/ResumenTab.test.tsx`):
   - Renderiza con filtro default
   - Cambio de filtro actualiza KPIs, chart y funnel simultáneamente
   - Tooltips están presentes en todas las cards

3. **E2E smoke** (`frontend/e2e/specs/smoke/meta-ads-resumen.smoke.spec.ts`):
   - Click en chip de offer → verifica que los 6 KPI values y el funnel cambian
   - Screenshot baseline del layout nuevo

#### Lint, type-check, formato

- `cd backend && .venv/bin/ruff check src/ tests/ --no-cache` debe pasar clean
- `cd backend && .venv/bin/pytest tests/modules/advertising/ -x -q` debe pasar clean
- `cd frontend && npx tsc --noEmit` debe pasar clean
- `cd frontend && npx eslint src/features/growth-studio/` debe pasar clean
- `cd frontend && npx vitest run src/features/growth-studio/` debe pasar clean

### Plan multiagente

**Fase 1 — Contrato y diseño visual (paralelo)**
- `nicolify-architect`: produce `CONTRACT.md` con DTOs finales, tipos TypeScript espejo, firmas de métodos y queries SQL que el backend va a ejecutar. Verifica existencia de `get_tenant_locale` dependency; si no existe, la define.
- `nicolify-ux-designer`: produce `UI-SPEC.md` con jerarquía visual completa, tokens, todos los tooltips redactados, estados (loading/empty/error), interacción de cambio de filtro, y wireframes en ASCII/Markdown de los 4 filtros.

**Fase 2 — Implementación core (paralelo, lee CONTRACT + UI-SPEC)**
- `nicolify-backend`: implementa cambios en `metrics_by_offer_service.py`, DTOs, repositorio (`period_metrics` lookup), timezone fix, `resolve_period_window`, dependency wiring, tests unitarios y de timezone. Corre lint + tests nativamente.
- `nicolify-frontend`: implementa `useResumenViewData` hook, refactor de `ResumenTab`, mueve segmentador, conecta funnel reactivo, archivos de tooltips, tests de hook y component. NO polishea charts todavía — deja los charts funcionales pero básicos.

**Fase 3 — Polish visual por especialista (paralelo, uno por gráfico)**
- Agente "data-viz senior" (general-purpose con frontend-design skill) × 4:
  1. **KPI cards polish** — itera la visual de las cards (jerarquía, tipografía, color de delta, estado `—`, tooltip UX, aria-labels)
  2. **InversionChart polish** — subtítulo contextual, colores break-even, tooltip rico
  3. **MetaAdsMiniFunnel polish** — tasas de conversión visibles, color ramp, estado cero
  4. **OfferSegmenter polish** — active state, spacing, diferenciación branding/unassigned

Cada agente recibe (a) el archivo del componente, (b) UI-SPEC.md, (c) instrucción de iterar SOLO visual sin romper contratos. Corre `tsc --noEmit` + vitest del feature al final.

**Fase 4 — Auditoría y verificación (secuencial)**
- `nicolify-backend-auditor`: review completa del diff backend contra CONTRACT.md y `.claude/rules/`.
- Main thread: corre suite nativa completa (ruff, pytest advertising module, tsc, eslint growth-studio, vitest growth-studio, E2E smoke si aplica).
- Fix de cualquier falla antes del commit.

**Fase 5 — Commit y reporte (secuencial, main thread)**
- Commit único con mensaje convencional (posible split si el diff es muy grande).
- Working tree limpio en `development`.
- Reporte final al usuario con diff resumido, tests pasando, capturas si posible.

## Deuda técnica resuelta en este scope

1. ✅ Reach se suma mal por campaña (ahora usa `period_metrics` y retorna `null` si ambiguo)
2. ✅ Timezone naive en `resolve_period_window` (ahora respeta `TenantLocale.timezone`)
3. ✅ Branding/Unassigned DTOs sin CTR/CPM/CPC
4. ✅ Funnel del Resumen desconectado del filtro de offer

## Fuera de scope (deuda pendiente)

1. **Atribución pixel-event → offer.** Meta Insights API agrega eventos por campaña, no por offer. El mapeo actual (campaña → offer vía `ad_offer_associations`) es la única fuente de verdad posible sin cambios profundos. Documentado.
2. **Frequency per offer.** Requiere reach correcto por offer (no disponible si hay overlap de campañas). Solo se muestra para "Todas" y offers de 1 campaña.
3. **Dashboard de las otras pestañas (Campañas, Creativos, Audiencia, Costos).** Estas quedan como están — solo Resumen se refactoriza.
4. **Filtro por rango de fechas custom.** Mantiene los 3 presets `7d/30d/90d` actuales.
