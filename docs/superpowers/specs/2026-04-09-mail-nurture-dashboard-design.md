# Mail Channel Dashboard — Nurture Stage (Email Intelligence Hub)

**Date:** 2026-04-09
**Status:** Design approved
**Stage:** Nutrición (Nurture)
**Channel:** email-nurture (source-agnostic, currently Mailerlite)

## Summary

Redesign the Mail channel sidebar and extended dashboard in Growth Studio's Nurture stage. Replace the existing generic ~70% implementation with an expert-level "Email Intelligence Hub" that combines health scoring, campaign performance ranking, engagement segmentation, and actionable insights — all source-agnostic so switching from Mailerlite to Mailchimp requires zero frontend changes.

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Tooltip UX | Info icon `(i)` + Click Popover | Reliable on mobile/desktop, doesn't close accidentally, space for formula + benchmark + interpretation |
| Dashboard architecture | Email Intelligence Hub (hybrid) | Combines health score + campaign ranking + 6 dedicated tabs |
| Existing code | Full redesign | Replace existing Mail components entirely; reuse shared infrastructure (ChannelOverviewPanel, HeroKpiGrid, useChannelDashboard) |
| Source abstraction | Provider-agnostic DTO layer | Backend services return normalized DTOs; provider-specific logic stays in ETL providers |

## Sidebar Design (MailOverviewPanel)

Size: `lg` (same as Meta Ads). Rendered inside `DetailPanel`.

### Component Stack (top to bottom)

1. **Header**: Mail icon (amber-500), "Email Marketing", provider subtitle ("via MailerLite")
2. **Actions bar**: Period selector (7d/30d/90d) + Sync button + "Ver Dashboard Completo" button
3. **Email Health Score**: 0-100 composite score with 4 colored sub-bars
   - Engagement (weight: 30%) — based on open_rate vs benchmark
   - Entregabilidad (weight: 30%) — based on deliverability_rate
   - Crecimiento (weight: 20%) — based on list_growth_rate
   - Contenido (weight: 20%) — based on avg CTOR vs benchmark
   - Colors: ≥80 green, 60-79 yellow, <60 red
4. **4 Hero KPIs** (2×2 grid with sparklines):
   - Open Rate (benchmark: 21.5%)
   - Click-to-Open Rate / CTOR (benchmark: 10.5%)
   - Entregabilidad (target: >95%)
   - Crecimiento Lista (net growth rate)
   - Each with: value, sparkline, delta vs previous period, benchmark badge
5. **Mini Funnel**: Enviados → Abiertos → Clicks with conversion rates
6. **Best Campaign**: Card with green left border, name, open rate, CTOR, sent count, date
7. **Worst Campaign**: Card with red left border, same metrics
8. **Deliverability Health Indicator**: Semaphore dot (healthy/warning/critical) with bounce, spam, unsub rates

## Extended Dashboard (MailDashboard)

Full-screen portal with 6 tabs. Period selector in top bar.

### Tab 1: Panorama (Overview)

- **6 KPI cards** (row): Emails Enviados, Open Rate, Click Rate, CTOR, Entregabilidad, Suscriptores — each with delta, benchmark
- **Volumen vs Engagement chart** (dual axis): Bars (emails sent/week) + line (open rate/week)
- **Email Funnel**: Horizontal bars — Enviados → Entregados → Abiertos → Clicks → Bajas with conversion rates
- **Tu Performance vs Industria**: 4 bar comparisons with benchmark marker line
- **Campañas vs Automatizaciones**: Side-by-side table comparing engagement metrics + auto-generated insight
- **Campañas Recientes**: Quick table (top 5) with type tag, sortable, link to full Campañas tab

### Tab 2: Campañas

- **Rendimiento por Tipo de Email**: 4 type cards (Newsletter, Lanzamiento, Promoción, Contenido) with metrics, campaign count, ranking indicator, auto-insight
- **Open Rate y CTOR por Tipo**: Horizontal bar charts with industry benchmark line
- **Tabla Completa de Campañas**: All campaigns, sortable by any column, filterable by type. Columns: #, Name, Type (tag), Date, Enviados, Open Rate (with mini bar), Click Rate, CTOR, Bounces, Bajas, Best/Worst indicator
- **Mejores Subject Lines**: Top 3 ranked by open rate with pattern detection insight
- **Tendencia de Engagement por Tipo**: Multi-series line chart showing open rate evolution per type over 12 weeks

### Tab 3: Automatizaciones

- **3 KPI cards**: Emails via automations, Completion Rate, Avg Open Rate
- **Tabla de Automatizaciones Activas**: Name, Type (Welcome/Nurture/Re-engagement/Post-compra), Active subscribers, Completed, Open Rate, Click Rate, Completion Rate. Sortable, badge for active/paused
- **Funnel de Automatización Principal**: Vertical step-by-step for highest-volume automation — each step shows sent, open rate, clicks, drop-off between steps
- **Comparativa Automations vs Campañas**: Side-by-side engagement metrics + recommendation insight

### Tab 4: Audiencia

- **Segmentos por Engagement** (4 cards): Champions (open+click regularly), Activos (open but low click), En Riesgo (inactive 30-60 days), Dormidos (inactive 60+ days). Each with: count, %, Open Rate, Click Rate, CTOR, behavioral metric, **recommended action**
- **Matriz Segmento × Tipo de Email**: Grid showing open rate per segment per email type — reveals which content reactivates at-risk subscribers
- **Engagement por Fuente de Suscripción**: Table with source, subscriber count, open rate, click rate, % champions — shows acquisition quality
- **Ciclo de Vida del Engagement**: Decay curve showing how open rate drops by subscriber age (0-30d, 31-90d, 91-180d, 180+d)
- **Mapa de Actividad Semanal**: Heatmap (day × hour) of when subscribers open emails — identifies best send time
- **CTOR por Segmento × Tipo**: Per-segment breakdown of which content generates clicks — actionable content strategy

### Tab 5: Entregabilidad

- **Health Score**: 0-100 with sub-scores for bounce rate, spam rate, unsub rate. Thresholds: >90 green, 70-90 yellow, <70 red
- **Breakdown de Bounces**: Donut chart (hard vs soft vs delivered) + detail table with counts, rates, trends
- **Tendencia de Entregabilidad** (12 weeks): Line chart with deliverability_rate, bounce_rate, spam_rate. Shaded danger zones (>2% bounce = yellow, >5% = red)
- **Alertas y Recomendaciones**: Active alerts + automated recommendations (e.g., "Clean inactive subscribers >90 days")

### Tab 6: Crecimiento

- **4 KPI cards**: Active Subscribers, New (period), Unsubscribes (period), Net List Growth Rate
- **Gráfico de Crecimiento**: Stacked area (new subscribers green, unsubs red) per week + total active subscribers line (right axis)
- **Fuentes de Suscriptores**: Horizontal bars by source (Landing Page, Popup, Checkout, Import/API) with conversion rate
- **Ratio de Retención**: % subscribers still active at 30, 60, 90 days after signup

## Channel Row Metrics

In `channel-display-registry.ts`, update `email-nurture` summary metrics (shown in ChannelRow):

```
summaryMetrics: [
  { name: 'open_rate', label: 'Apertura', format: 'percentage' },
  { name: 'click_to_open_rate', label: 'CTOR', format: 'percentage' },
  { name: 'emails_sent', label: 'Enviados' },
  { name: 'active_subscribers', label: 'Suscriptores' },
]
primaryMetric: { name: 'open_rate', label: 'tasa de apertura' }
```

## Source-Agnostic Architecture

### Principle

The frontend never knows which email provider is behind the data. All provider-specific logic is encapsulated in the ETL layer and backend services. The API returns normalized DTOs.

### Backend Design

```
modules/analytics/
  domain/
    email_metrics.py          # EmailDashboardData, EmailCampaignDTO, 
                               # EmailAutomationDTO, EmailSegmentDTO,
                               # EmailHealthScore (value objects)
  infrastructure/
    providers/
      mailerlite_provider.py  # MailerLite-specific extraction (exists)
      # Future: mailchimp_provider.py, activecampaign_provider.py
  application/
    services/
      email_dashboard_service.py  # Orchestrates dashboard data from 
                                   # normalized metrics in official_metrics table
                                   # NO provider-specific imports
    stage_services/
      nurture_stage.py        # Existing stage service (no changes needed)
```

### Key abstraction points

1. **ETL providers** (infrastructure/) — Extract from provider API, transform to `official_metrics` rows. Provider-specific.
2. **Dashboard service** (application/) — Reads from `official_metrics` table only. Provider-agnostic. Computes health score, segments, rankings.
3. **API DTOs** (api/) — Return normalized shapes. Frontend consumes these.
4. **Frontend** — Displays whatever the API returns. Shows `provider_name` only as cosmetic subtitle.

### New API Endpoints

```
GET /api/v1/analytics/metrics/channel/email-nurture/dashboard?period=30d
  → EmailDashboardResponse (for sidebar + Panorama)

GET /api/v1/analytics/metrics/channel/email-nurture/campaigns?period=30d
  → EmailCampaignsResponse (campaign list + type breakdown)

GET /api/v1/analytics/metrics/channel/email-nurture/automations?period=30d
  → EmailAutomationsResponse (automation list + funnels)

GET /api/v1/analytics/metrics/channel/email-nurture/audience?period=30d
  → EmailAudienceResponse (segments, sources, lifecycle, heatmap)

GET /api/v1/analytics/metrics/channel/email-nurture/health?period=30d
  → EmailHealthResponse (deliverability details + alerts)

GET /api/v1/analytics/metrics/channel/email-nurture/growth?period=30d
  → EmailGrowthResponse (list growth, sources, retention)
```

## ETL Gaps to Fill

### High Priority (calculable from existing data)

| Metric | Formula | Source |
|--------|---------|--------|
| `deliverability_rate` | (sent - hard_bounces - soft_bounces) / sent × 100 | Derived |
| `list_growth_rate` | (new_subscribers - unsubscribes) / active_subscribers × 100 | Derived |
| `churn_rate` | unsubscribes / active_subscribers × 100 | Derived |
| `forward_rate` | forwards / emails_sent × 100 | Derived |

### Medium Priority (new data from Mailerlite API)

| Data | API Endpoint | Purpose |
|------|-------------|---------|
| `opens_count` (total, not unique) | Campaign stats | "Opens per reader" metric |
| `clicks_count` (total, not unique) | Campaign stats | "Clicks per reader" metric |
| Automation full stats | `GET /automations/{id}` | Per-step metrics, completion, queue |
| Form `opens_count` | `GET /forms/{type}` | Accurate form conversion rate |
| Campaign `subject` field | Campaign object | Subject line analysis |
| Campaign `type` field | Campaign object (`regular`, `ab`, `resend`) | Campaign type classification |
| Campaign `group_ids` | Campaign object | Stage-to-campaign mapping |

### Campaign Type Classification

Since Mailerlite doesn't have a native "campaign type" taxonomy (Newsletter, Launch, Promo, Content), we implement classification:

1. **ETL extracts** campaign `name` and `subject` fields
2. **Store in** `official_metrics.extra` as `{"campaign_name": "...", "campaign_subject": "...", "campaign_type": "..."}`
3. **Classification logic** (backend service, not ETL):
   - Keywords in name/subject: "newsletter", "semanal" → Newsletter
   - Keywords: "lanzamiento", "launch", "nuevo", "exclusivo" → Lanzamiento
   - Keywords: "promo", "descuento", "%", "oferta", "black friday" → Promoción
   - Default → Contenido
   - User can override via UI (future: manual tag in Mailerlite groups)

### Engagement Segmentation

Computed in `email_dashboard_service.py` from `official_metrics` aggregated data:

- **Champions**: open_rate > 50% AND click_rate > 5% in last 30 days
- **Activos**: open_rate > 15% AND click_rate <= 5%
- **En Riesgo**: open_rate < 15% OR no opens in 30-60 days
- **Dormidos**: No opens in 60+ days

Note: This is an approximation using aggregate campaign metrics, not per-subscriber data (which would require expensive API calls). Future enhancement could use subscriber-level activity for precise segmentation.

### Activity Heatmap

Derived from campaign send times + open rates:
- Group campaigns by day-of-week and approximate hour
- Use open_rate as the "heat" value
- Limitation: Without per-subscriber open timestamps, this reflects "which send times got best results", not "when subscribers actually open"

## Info Popover Component

Shared component used across all metric displays:

```typescript
interface MetricInfoPopover {
  metricName: string        // Unique ID for metric catalog lookup
  children: ReactNode       // The metric label/value it wraps
}

// Popover content from metric catalog:
{
  displayName: string       // "Tasa de Apertura"
  description: string       // "Porcentaje de emails abiertos vs enviados"
  formula?: string          // "unique_opens / emails_sent × 100"
  benchmark?: {
    value: number           // 21.5
    source: string          // "Campaign Monitor 2022"
    industry?: string       // From tenant's industry setting
  }
  interpretation?: string   // "Valores por encima de 25% son excelentes"
  higherIsBetter: boolean
}
```

Implementation: Shadcn `Popover` triggered on click of `(i)` icon. Closes on click outside or X button.

## Frontend Component Structure

```
features/growth-studio/components/metrics-dashboard/sidebar/mail/
  MailOverviewPanel.tsx          # Sidebar entry point (REDESIGN)
  MailDashboard.tsx              # Extended dashboard (REDESIGN)
  MailHealthScore.tsx            # NEW: Composite score with sub-bars
  MailCampaignCards.tsx          # NEW: Best/worst campaign in sidebar
  tabs/
    MailPanoramaTab.tsx          # NEW: Overview tab
    MailCampanasTab.tsx          # NEW: Campaigns tab
    MailAutomatizacionesTab.tsx  # NEW: Automations tab
    MailAudienciaTab.tsx         # NEW: Audience tab
    MailEntregabilidadTab.tsx    # REDESIGN: Deliverability tab
    MailCrecimientoTab.tsx       # NEW: Growth tab
  charts/
    MailVolumenEngagementChart.tsx  # Dual-axis bar + line
    MailEmailFunnel.tsx            # Horizontal funnel bars
    MailBenchmarkComparison.tsx    # Bar comparison with markers
    MailTypePerformance.tsx        # Horizontal bars by type
    MailEngagementHeatmap.tsx      # Day × hour heatmap
    MailDecayCurve.tsx             # Engagement lifecycle curve
    MailSegmentMatrix.tsx          # Segment × type grid

components/shared/
  MetricInfoPopover.tsx          # NEW: Reusable (i) click popover
```

## Hooks / API

```
features/growth-studio/
  hooks/
    useMailDashboard.ts           # Existing (enhance response type)
    useMailCampaigns.ts           # NEW
    useMailAutomations.ts         # NEW
    useMailAudience.ts            # NEW
    useMailHealth.ts              # NEW
    useMailGrowth.ts              # NEW
  api/
    mail-api.ts                   # NEW: API functions for all endpoints
  types/
    mail-types.ts                 # NEW: TypeScript interfaces for all DTOs
```

## Testing Strategy

### Backend
- `test_email_dashboard_service.py`: Health score calculation, segment classification, campaign type detection
- `test_email_metrics_dto.py`: DTO validation, derived metric formulas
- `test_mailerlite_provider_enhanced.py`: New fields extraction (subject, type, opens_count)

### Frontend
- `MailOverviewPanel.test.tsx`: Sidebar renders all sections, health score colors
- `MailDashboard.test.tsx`: Tab navigation, period switching
- `MailCampanasTab.test.tsx`: Campaign table sorting, type filtering, type cards
- `MailAudienciaTab.test.tsx`: Segment cards, heatmap rendering, matrix
- `MetricInfoPopover.test.tsx`: Click to open, close on outside click, content rendering

### E2E
- Smoke: `/growth/nurture` → click email-nurture channel → sidebar opens → expand to dashboard → navigate all 6 tabs
- Regression: Period switching updates data, campaign filter works, popover opens/closes

## Metrics Not Available via Mailerlite API

These metrics are shown as "N/D" or hidden entirely:

| Metric | Why unavailable |
|--------|----------------|
| Revenue per Email (RPE) | API has no campaign→order attribution |
| Email client/device breakdown | Not exposed in API |
| Best send time (per-subscriber) | Would require paginating all subscribers |
| Per-variation A/B test results | Only winner stats exposed |
| Link-level click tracking | Endpoint not documented |

## Mockup References

Interactive mockups saved in `.superpowers/brainstorm/66190-1775757369/content/`:
- `sidebar-mockup.html` — Full sidebar design
- `dashboard-panorama.html` — Tab Panorama
- `dashboard-campanas.html` — Tab Campañas
- `dashboard-audiencia.html` — Tab Audiencia
