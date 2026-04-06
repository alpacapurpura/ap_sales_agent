# Channel Dashboard Playbook

Guía para que un agente replique el patrón del Meta Ads Dashboard para cualquier otro canal (Google Ads, YouTube Ads, TikTok Ads, etc.). Cada canal tiene métricas propias, pero la arquitectura es idéntica.

## Arquitectura general

El flujo es: **Endpoint genérico** → **Sidebar 650px** → **Full dashboard con tabs**.

```
Backend (genérico, ya implementado):
  GET /api/v1/analytics/metrics/channel/{channel_slug}/dashboard?period=7d|30d|90d
  → ChannelDashboardService → ChannelDashboardDTO (kpis, time_series, funnel, frequency_alert)

Frontend (por canal):
  ChannelDetailSidebar → branch por slug → {Channel}OverviewPanel (sidebar 650px)
  → botón "Dashboard completo" → {Channel}Dashboard (full-page con tabs vía portal)
```

## Qué ya está implementado (reutilizable)

Estos archivos son **genéricos** — funcionan para CUALQUIER canal sin modificación:

| Archivo | Qué hace |
|---------|----------|
| `backend/.../channel_dashboard_service.py` | Servicio que arma el DTO. Usa `_HERO_METRICS`, `_TIMESERIES_METRICS`, `_FUNNEL_STEPS` como configuración por canal |
| `backend/.../channel_dashboard_dto.py` | DTOs: `ChannelDashboardDTO`, `MetricKpiDTO`, `MetricTimeSeriesDTO`, `AdFunnelDTO`, `FrequencyAlertDTO` |
| `backend/.../industry_benchmarks.py` | Benchmarks por industria + `normalize_industry()` fuzzy matching |
| `backend/.../official_metrics_repository.py` | `get_channel_daily_metrics()` y `get_channel_metrics_for_period()` |
| `backend/.../metrics.py` (endpoint) | `GET /channel/{channel_slug}/dashboard` — acepta cualquier slug |
| `frontend/.../channel-dashboard-api.ts` | `fetchChannelDashboard(token, slug, period)` — genérico |
| `frontend/.../useChannelDashboard.ts` | Hook React Query — acepta cualquier slug |
| `frontend/.../types/metrics.ts` | `ChannelDashboardData`, `MetricKpiData`, `BenchmarkRange`, etc. |
| `frontend/.../BenchmarkBadge.tsx` | Badge verde/amarillo/rojo vs benchmarks |
| `frontend/.../benchmark-parser.ts` | Parser fallback para strings de catálogo |
| `frontend/.../detail-panel.tsx` | `size` prop (`sm`/`md`/`lg`) para sidebars anchos |
| `frontend/.../MetaAdsPeriodSelector.tsx` | Selector 7d/30d/90d (reutilizable, renombrar a `PeriodSelector`) |

## Qué necesita cada canal nuevo

### 1. Backend: Configurar métricas del canal

En `channel_dashboard_service.py`, las constantes definen qué métricas se muestran. Actualmente están pensadas para Meta Ads. Para un canal nuevo necesitas **decidir** (no codificar nuevo):

```python
# Estos ya son genéricos — el servicio los usa para TODOS los canales.
# Si un canal no tiene cierta métrica, simplemente no aparece en el resultado.
_HERO_METRICS = ["spend", "ROAS", "CPL", "CTR", "CPC", "CPM", "CPA", "conversions"]
_TIMESERIES_METRICS = ["spend", "impressions", "clicks", "reach", ...]

# ESTO SÍ es específico de Meta Ads — los funnel steps:
_FUNNEL_STEPS = [
    ("Impresiones", "impressions"),
    ("Clics", "clicks"),
    ("Vistas de Landing", "meta_landing_page_views"),  # ← meta-specific
    ("Leads", "meta_leads"),                            # ← meta-specific
    ("Conversiones", "conversions"),
]
```

**Decisión clave:** Si el funnel es diferente por canal (Google Ads no tiene `meta_landing_page_views`), hay dos opciones:

- **Opción A (recomendada):** Hacer `_FUNNEL_STEPS` un dict por slug:
  ```python
  _FUNNEL_STEPS_BY_CHANNEL = {
      "meta-ads": [("Impresiones", "impressions"), ("Clics", "clicks"), ...],
      "google-ads": [("Impresiones", "impressions"), ("Clics", "clicks"), ("Conversiones", "conversions")],
      "yt-ads": [("Vistas", "views"), ("Clics", "clicks"), ("Conversiones", "conversions")],
  }
  ```
- **Opción B:** Funnel genérico que solo incluye steps con valor > 0.

También agregar el nombre del canal en `_CHANNEL_NAMES`:
```python
_CHANNEL_NAMES["google-ads"] = "Google Ads"
_CHANNEL_NAMES["yt-ads"] = "YouTube Ads"
```

### 2. Backend: Benchmarks por industria (opcional)

En `industry_benchmarks.py`, agregar benchmarks específicos del canal si los hay. Los benchmarks actuales (CTR, CPC, CPL, ROAS, CPA, CPM) son genéricos y aplican a todos los canales de paid ads. Si un canal tiene benchmarks diferentes (ej. YouTube tiene benchmarks de view rate), agregar nuevas entries:

```python
IndustryBenchmarkEntry(
    metric_name="view_rate",
    low=15.0, median=25.0, high=35.0,
    unit="percentage",
    interpretation_es="Porcentaje de personas que ven el video completo",
)
```

### 3. Frontend: Crear directorio del canal

Patrón exacto — copiar `sidebar/meta-ads/` y renombrar:

```
sidebar/{channel-slug}/
  {Channel}OverviewPanel.tsx    ← assembler del sidebar
  {Channel}HeroKpiGrid.tsx      ← 2×2 grid con sparklines
  {Channel}MiniFunnel.tsx        ← funnel horizontal (reutilizable tal cual)
  {Channel}Dashboard.tsx         ← full-page con portal
  ReachFrequencySection.tsx      ← mover a shared si >1 canal lo usa
  tabs/
    OverviewTab.tsx
    {TabEspecífico}Tab.tsx       ← tabs específicos del canal
```

**Lo que cambia por canal:**

| Componente | Qué personalizar |
|-----------|-----------------|
| `HeroKpiGrid` | `HERO_METRICS` array (qué 4 KPIs mostrar como hero) |
| `MiniFunnel` | Nada — es genérico, recibe `steps` como prop |
| `OverviewTab` | Chart composito: qué métricas en barras vs líneas |
| Tabs específicos | Google Ads: Keywords, Audiencia. YouTube: Retención, Videos. TikTok: Engagement, Sounds |
| `Dashboard` | Tabs list + tab content |

### 4. Frontend: Integrar en ChannelDetailSidebar

En `ChannelDetailSidebar.tsx`, agregar un branch **ANTES** del `return <DetailPanel>` default (línea ~137):

```tsx
// Ya existe:
if (channel.slug === 'meta-ads') {
  return (
    <DetailPanel open={isOpen} onClose={onClose} size="lg">
      <MetaAdsOverviewPanel channel={channel} onClose={onClose} onExpand={handleOpenMetaAdsDashboard} />
    </DetailPanel>
  );
}

// Agregar para el nuevo canal:
if (channel.slug === 'google-ads') {
  return (
    <DetailPanel open={isOpen} onClose={onClose} size="lg">
      <GoogleAdsOverviewPanel channel={channel} onClose={onClose} onExpand={handleOpenGoogleAdsDashboard} />
    </DetailPanel>
  );
}
```

### 5. Frontend: Extender GrowthStudioContext

En `GrowthStudioContext.tsx`, agregar estado para el nuevo dashboard:

```tsx
// Ya existe:
metaAdsDashboardOpen: boolean;
handleOpenMetaAdsDashboard: () => void;
handleCloseMetaAdsDashboard: () => void;

// Agregar:
googleAdsDashboardOpen: boolean;
handleOpenGoogleAdsDashboard: () => void;
handleCloseGoogleAdsDashboard: () => void;
```

**Alternativa mejor (refactor):** Cambiar a un solo estado genérico:
```tsx
channelDashboardSlug: string | null;  // 'meta-ads' | 'google-ads' | null
handleOpenChannelDashboard: (slug: string) => void;
handleCloseChannelDashboard: () => void;
```

### 6. Frontend: Renderizar en AttractionCaptureDetail

En `AttractionCaptureDetail.tsx`, agregar el wrapper del nuevo dashboard:

```tsx
// Ya existe:
<MetaAdsDashboardWrapper />

// Agregar:
<GoogleAdsDashboardWrapper />
```

O con el refactor genérico:
```tsx
<ChannelDashboardWrapper />  // lee slug del context, renderiza el dashboard correcto
```

### 7. Tests

#### Backend (ya cubierto por tests genéricos)
Los tests de `test_channel_dashboard_service.py` prueban la lógica genérica (deltas, funnel, frequency). No necesitan duplicarse por canal.

#### Frontend: Unit tests
Copiar patrón de `__tests__/MetaAdsPeriodSelector.test.tsx` y `__tests__/MetaAdsMiniFunnel.test.tsx`.

#### E2E: Playwright
Copiar patrón de `e2e/specs/smoke/meta-ads.smoke.spec.ts`:
1. Crear mock data en `e2e/fixtures/{channel}-mock-data.ts`
2. Crear POM en `e2e/pages/{channel}-dashboard.page.ts`
3. Crear spec en `e2e/specs/smoke/{channel}.smoke.spec.ts`

**Lección importante:** Los mocks deben interceptar TODAS las APIs que Growth Studio necesita (attraction, capture, summary, timeseries, catalog, connections, channel dashboard). Si falta alguna, el frontend muestra "Error al cargar metricas" y los channel rows no aparecen. Usar `setupMetaAdsMocks` como template en `e2e/fixtures/meta-ads-setup.ts`.

## Errores comunes y lecciones aprendidas

### Backend

1. **Cross-module import viola DDD:** Importar `BrandReadPortImpl` desde analytics requiere agregar la violación al allowlist en `tests/architecture/test_ddd_boundaries.py`. Patrón: `"analytics -> brand | analytics/api/metrics.py"`. Justificación: inyección de dependencia en endpoint, mismo patrón que `OfferReadPort`.

2. **Repository method `func.sum` import:** Al agregar `get_channel_daily_metrics` al repo, hay que agregar `func` al import de SQLAlchemy: `from sqlalchemy import func, select, text`.

3. **Métricas non-aggregable:** `reach` y `frequency` NO se pueden sumar cross-day. El repo usa el metric catalog (`get_metric_def`) para decidir SUM vs latest value. El frontend debe etiquetar "Personas únicas — no es suma diaria".

### Frontend

4. **`DetailPanel` size prop:** Default `'sm'` (400px). Sidebars de canal usan `'lg'` (650px). No rompe backwards compatibility.

5. **Strict mode violations en E2E:** Textos como "Inversión" aparecen tanto en la page principal como en el sidebar dialog. Usar `page.getByRole('dialog').getByText(...)` para scopear al sidebar.

6. **Tildes en textos:** Los componentes creados por agentes a veces omiten tildes ("dias" vs "días", "Campanas" vs "Campañas", "Conversion" vs "Conversión"). Los E2E locators deben coincidir EXACTAMENTE con lo renderizado. Verificar con screenshots.

7. **`createPortal` para full dashboard:** El dashboard full-page usa `createPortal(content, document.body)` para renderizar sobre todo. Guard de SSR: `if (typeof document === 'undefined') return null`.

8. **`useChannelDashboard` es genérico:** Acepta cualquier slug. No crear hooks por canal. Solo cambiar el slug: `useChannelDashboard('google-ads', period)`.

### E2E

9. **API URL desde e2e container:** El frontend usa `NEXT_PUBLIC_API_URL=https://dev-api.nicolify.com`. El mock pattern `**/api/v1/analytics/**` intercepta CUALQUIER dominio gracias al `**` prefix. Funciona tanto con localhost como con dev-api.

10. **Clerk auth es flaky:** El `clerk.signIn()` puede timeout intermitentemente. No es un bug de los tests — reintentar. El commit `005df11` ya documentó este issue.

11. **Mocks deben cubrir TODO:** Si el mock de `attraction` no intercepta, la page muestra error y los channel rows no aparecen. Template completo en `e2e/fixtures/meta-ads-setup.ts`.

## Checklist para nuevo canal

```
□ Backend: Agregar nombre a _CHANNEL_NAMES en channel_dashboard_service.py
□ Backend: Definir funnel steps (si diferente de Meta Ads) en _FUNNEL_STEPS_BY_CHANNEL
□ Backend: Agregar benchmarks específicos en industry_benchmarks.py (si aplica)
□ Backend: Verificar que las métricas del canal existen en METRIC_CATALOG
□ Backend: ruff check + pytest (incluye architecture tests)
□ Frontend: Crear directorio sidebar/{channel-slug}/ con componentes
□ Frontend: Definir HERO_METRICS para el HeroKpiGrid del canal
□ Frontend: Definir tabs específicos del canal
□ Frontend: Branch en ChannelDetailSidebar.tsx para el slug
□ Frontend: Estado en GrowthStudioContext (o refactor genérico)
□ Frontend: Wrapper en AttractionCaptureDetail.tsx
□ Frontend: tsc --noEmit + vitest run
□ E2E: Mock data + POM + smoke spec
□ E2E: Verificar con make e2e-smoke
□ Commit convencional + merge a main
```

## Métricas típicas por canal

| Canal | Hero KPIs | Funnel | Tabs específicos |
|-------|-----------|--------|-----------------|
| Meta Ads | spend, ROAS, CPL, CTR | impressions→clicks→LPV→leads→conversions | Campañas, Audiencia, Video, Costos |
| Google Ads | spend, ROAS, CPA, CTR | impressions→clicks→conversions | Campañas, Keywords, Audiencia, Costos |
| YouTube Ads | spend, CPV, view_rate, CTR | impressions→views→clicks→conversions | Campañas, Video, Audiencia, Costos |
| TikTok Ads | spend, ROAS, CPC, CTR | impressions→clicks→conversions | Campañas, Creativos, Audiencia, Costos |
| Google Analytics | sessions, bounce_rate, engagedSessions | sessions→engagedSessions→conversions | Páginas, Fuentes, Audiencia, Conversiones |
| Shopify | revenue, orders, AOV | visits→add_to_cart→checkout→purchase | Productos, Pedidos, Clientes, Descuentos |

## Archivos de referencia

```
# Backend (copiar patrón)
backend/src/modules/analytics/application/services/channel_dashboard_service.py
backend/src/modules/analytics/domain/industry_benchmarks.py
backend/tests/modules/analytics/test_channel_dashboard_service.py

# Frontend (copiar y adaptar)
frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/  ← directorio completo
frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/ChannelDetailSidebar.tsx:137-148  ← branch pattern
frontend/src/features/growth-studio/components/metrics-dashboard/context/GrowthStudioContext.tsx:84,129-137  ← state pattern
frontend/src/features/growth-studio/components/metrics-dashboard/detail-panels/AttractionCaptureDetail.tsx:27-29,377  ← wrapper pattern

# E2E (copiar y adaptar)
frontend/e2e/fixtures/meta-ads-mock-data.ts  ← mock data template
frontend/e2e/fixtures/meta-ads-setup.ts  ← mock setup template
frontend/e2e/pages/meta-ads-dashboard.page.ts  ← POM template
frontend/e2e/specs/smoke/meta-ads.smoke.spec.ts  ← smoke spec template
frontend/e2e/specs/regression/growth/meta-ads-dashboard.spec.ts  ← regression template
```
