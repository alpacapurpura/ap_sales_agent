# Website Channel Dashboard — Design Spec

**Fecha:** 2026-04-08
**Canal:** `website-total` (slug)
**Etapa:** Atracción
**Fuentes:** GA4 (primaria), Meta Pixel, Shopify

## Contexto

Growth Studio necesita un dashboard de detalle para el canal "Tu Sitio Web" en la etapa Atracción. Actualmente el canal `website-total` está registrado en el backend (channel_registry) y el ETL de GA4 extrae métricas, pero no existe sidebar, dashboard expandido, ni métricas inline en el ChannelRow.

El perfil de usuario es un creador/infoproductor (como visionarias.lat) que puede tener: blog + WhatsApp, landing + formulario, tienda Shopify, o sales page + payment link. El dashboard debe adaptarse mostrando solo las secciones con datos activos.

## Arquitectura Multi-Fuente

Cuando una métrica existe en múltiples fuentes (GA4 + Shopify + Meta Pixel):
- **Valor principal:** GA4 con logo de GA4 al costado
- **Fuentes alternativas:** Logos pequeños de Meta/Shopify debajo, con tooltip mostrando su valor
- Componente: `SourceAttribution` (nuevo, reutilizable)

## 1. Channel Row (4 métricas inline)

| Métrica | Nombre backend | Formato | Fuente |
|---------|---------------|---------|--------|
| Sesiones | `sessions` | number | GA4 |
| Engagement | `engagementRate` | percentage | GA4 |
| Bounce | `bounceRate` | percentage | GA4 |
| Conversiones | `conversions` | number | GA4 |

Config en `channel-display-registry.ts`:
```typescript
'website-total': {
  summaryMetrics: [
    { name: 'sessions', label: 'Sesiones' },
    { name: 'engagementRate', label: 'Engagement', format: 'percentage' },
    { name: 'bounceRate', label: 'Bounce', format: 'percentage' },
    { name: 'conversions', label: 'Conversiones' },
  ],
  primaryMetric: { name: 'sessions', label: 'sesiones' },
}
```

## 2. Sidebar (panel 650px)

Sigue el patrón `ChannelOverviewPanel` (shared). Componente: `WebsiteOverviewPanel`.

### Hero KPIs (grid 2x3)

| KPI | Métrica | Unit | Higher is better | Benchmark |
|-----|---------|------|-------------------|-----------|
| Sesiones | `sessions` | count | yes | B2C: 1,850-9,050/sem |
| Engagement Rate | `engagementRate` | percentage | yes | >50% saludable |
| Bounce Rate | `bounceRate` | percentage | **no** | <40% bueno |
| Conversiones | `conversions` | count | yes | — |
| Duración Promedio | `averageSessionDuration` | seconds | yes | >2min bueno |
| Visitantes Únicos | `users` | count (NON_AGGREGABLE) | yes | — |

### Mini-Funnel

```
Sesiones (sessions) → Comprometidas (engagedSessions) → Pág. Clave (screenPageViews) → Conversiones (conversions)
```

### Botón "Dashboard completo"

Navega a `/{tenantId}/growth-studio/atraccion-captura/website-total`.

## 3. Dashboard Expandido (full-page, 4 tabs)

Componente: `WebsiteDashboard` (sigue patrón `IgOrganicDashboard`).

### Tab 1: Overview

- Hero KPIs (3 cols): Sesiones, Engagement Rate, Conversiones
- Tendencia de Sesiones (AreaChart, 30d)
- Embudo Web (mini-funnel)

### Tab 2: Tráfico

- **Fuentes de Tráfico** — DonutChart: orgánico, directo, social, referral, email, otros
  - Fuente: `traffic_sources` (JSON metric from GA4)
- **País / Región** (top 5) — Horizontal bars con banderas
  - Fuente: GA4 `country` dimension (requiere nueva extracción o `extra` field)
- **Dispositivos** — Horizontal bars: mobile, desktop, tablet
  - Fuente: `device_split` (JSON metric from GA4)
- **Nuevo vs Recurrente** — Two cards with percentages
  - Fuente: `newUsers` / `users` ratio
- **Idioma** — DonutChart pequeño
  - Fuente: GA4 `language` dimension (future sprint, placeholder)

### Tab 3: Contenido

- **Top Páginas** (tabla con 7 columnas): #, Página, Vistas, Engagement Time, Bounce Rate, % Total, Barra
  - Fuente: `top_pages` (JSON metric from GA4) + columnas adicionales por página
- **Exit Pages** (top 10) — Tabla: Página, Salidas, % de Salida, Barra
  - Fuente: GA4 `pagePath` + `exits` metric (requiere nueva extracción)
- **Eventos Principales** — Grid 4 cols: CTA clicks, Scroll 90%, Descargas, Video plays
  - Fuente: GA4 enhanced measurement events (requiere nueva extracción)

### Tab 4: Conversiones

- **Tipos de Conversión** — Grid adaptativo (solo muestra tipos con datos >0):
  - Formularios (GA4 `form_submit` event)
  - WhatsApp clicks (GA4 outbound click to wa.me)
  - Add to Cart (GA4/Shopify `add_to_cart`)
  - Compras (GA4/Shopify `purchase`)
- **Embudo E-commerce** (solo si Shopify conectado):
  - Sessions → View Product → Add to Cart → Checkout → Purchase
  - Fuente: GA4 ecommerce events
- **KPIs E-commerce** (solo si Shopify conectado):
  - AOV (Average Order Value) — `purchaseRevenue / transactions`
  - Cart Abandonment — `1 - (purchases / begin_checkout)`
  - Revenue per Session — `purchaseRevenue / sessions`
  - Tasa de Conversión — `purchases / sessions`
- **Tasa de Conversión Trend** — AreaChart con delta vs periodo anterior

## 4. Tooltips (Popover clickeable)

Cada métrica y gráfico tiene un botón `ℹ` que abre un Popover con:

1. **Nombre** + **Fórmula** (si aplica)
2. **¿Por qué importa?** — descripción en español, orientada al negocio
3. **Benchmark de referencia** — valores por industria cuando disponibles
4. **¿Cómo interpretar?** — guía práctica de qué hacer si el valor es bueno/malo
5. **Indicador** — "Más es mejor" o "Menos es mejor"

Implementación: Extender `ChartInfoTooltip` existente (ya usa Popover + click) y `MetricInfoCard` (ya conecta con metric catalog).

Para gráficos: nuevo componente `ChartTooltipInfo` que acepta `why` + `interpretation` + `benchmarks` props.

## 5. Backend — Cambios Requeridos

### channel_dashboard_service.py

Agregar config para `website-total`:
```python
"website-total": ChannelDashboardConfig(
    channel_name="Tu Sitio Web",
    hero_metrics=["sessions", "engagementRate", "bounceRate", "conversions", "averageSessionDuration", "users"],
    timeseries_metrics=["sessions", "engagedSessions", "bounceRate", "conversions", "engagementRate", "users"],
    funnel_steps=[
        ("Sesiones", "sessions"),
        ("Comprometidas", "engagedSessions"),
        ("Pág. Vistas", "screenPageViews"),
        ("Conversiones", "conversions"),
    ],
    has_frequency_alert=False,
)
```

### industry_benchmarks.py

Agregar benchmarks para métricas web:
- `engagementRate`: low=45, median=56, high=70
- `bounceRate`: low=55 (peor), median=40, high=25 (mejor) — inverted
- `averageSessionDuration`: low=60, median=137, high=300 (seconds)
- `sessions`: informational only (varies too much by business size)

### Métricas JSON (top_pages, traffic_sources, device_split)

Ya extraídas por `google_analytics_provider.py`. El `ChannelDashboardService` necesita incluirlas en el response DTO (actualmente solo devuelve KPIs y time series). Opciones:
- A) Añadir campo `extra_data: dict` al ChannelDashboardDTO
- B) Endpoint separado `GET /channel/{slug}/content-breakdown`

**Decisión:** Opción A (campo extra_data) — menos endpoints, misma request.

### Exit Pages & Events (nuevas extracciones)

Requieren nuevas queries al GA4 Data API:
- `pagePath` + `exits` metric → exit pages
- `eventName` + `eventCount` → eventos principales

Estas se agregan al `google_analytics_provider.py` como sub-extractors (mismo patrón que `_extract_top_pages`).

## 6. Frontend — Componentes Nuevos

```
sidebar/website/
  WebsiteOverviewPanel.tsx      ← usa ChannelOverviewPanel base
  WebsiteDashboard.tsx           ← full-page con portal (patrón IgOrganicDashboard)
  tabs/
    WebsiteOverviewTab.tsx
    WebsiteTrafficTab.tsx        ← fuentes, país, dispositivos, nuevo/recurrente
    WebsiteContentTab.tsx        ← top pages, exit pages, eventos
    WebsiteConversionsTab.tsx    ← tipos, embudo e-commerce, KPIs
  components/
    SourceAttribution.tsx        ← badge multi-fuente reutilizable
    TrafficSourcesChart.tsx      ← donut chart de fuentes
    CountryBars.tsx              ← barras horizontales con banderas
    DeviceSplitBars.tsx          ← barras de dispositivos
    TopPagesTable.tsx            ← tabla con engagement time + bounce
    ExitPagesTable.tsx           ← tabla de páginas de salida
    EventsSummaryGrid.tsx        ← grid de eventos principales
    EcommerceFunnel.tsx          ← embudo e-commerce (condicional)
    EcommerceKpis.tsx            ← AOV, cart abandonment, RPS
    ChartTooltipInfo.tsx         ← tooltip mejorado para gráficos
```

## 7. Datos No Disponibles (Placeholders)

Métricas que requieren configuración del tenant y deben mostrar placeholder:
- **Exit pages:** Si GA4 no tiene enhanced measurement → "Activa Enhanced Measurement en GA4"
- **Eventos:** Si no hay eventos custom → mostrar solo scroll (siempre activo)
- **E-commerce:** Si no tiene Shopify → ocultar sección completa
- **WhatsApp clicks:** Si no tiene botón WA → ocultar card

## 8. Métricas Diferidas (siguiente sprint)

- Edad / Género (requiere Google Signals)
- Usuarios activos ahora (GA4 Realtime API)
- Site search queries (GA4 enhanced measurement)
- Top productos por revenue (Shopify ETL)
- Idioma (GA4, baja prioridad)

## 9. Métricas Futuras (requieren nueva integración)

- Search Console (queries, posición, CTR orgánico) — OAuth separado
- Core Web Vitals (CrUX API)
- Detección de anomalías — motor estadístico
- Customer LTV — cómputo histórico Shopify

## Verificación

1. `cd backend && .venv/bin/ruff check src/ tests/ --no-cache`
2. `cd backend && .venv/bin/pytest -x -q --tb=short`
3. `cd frontend && npx tsc --noEmit`
4. `cd frontend && npx eslint src/`
5. `cd frontend && npx vitest run`
6. Navegar a Growth Studio → Atracción → click en "Tu Sitio Web" → verificar sidebar
7. Click "Dashboard completo" → verificar 4 tabs con datos
8. Verificar tooltips clickeables en cada métrica y gráfico
