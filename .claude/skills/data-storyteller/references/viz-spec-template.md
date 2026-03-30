# VIZ Spec Template

Use this template for Final Phase output. Fill every section. Mark N/A only if truly not applicable.

---

```markdown
# VIZ Spec: [Feature Name]

## Story
- **Question answered:** [The business question this visualization answers]
- **Audience:** [Who sees this — technical level, role]
- **Decision enabled:** [What action the user can take with this information]
- **Context:** [Where it appears — dashboard page, sidebar, widget, Copilot inline]
- **Update frequency:** [Real-time / hourly / daily / weekly — based on ETL cadence]

## Data Sources

| Source | Endpoint / Provider | Key Fields | Available? | Notes |
|--------|-------------------|------------|------------|-------|
| [platform] | [GET /api/v1/...] | [fields] | Yes/No | [needs integration / permission tier / etc.] |

## Metrics Displayed

| Metric | Type | Formula / Source | Display Format | Why This Metric |
|--------|------|-----------------|----------------|-----------------|
| [name] | KPI / chart-series / table-column | [formula or source field] | [$X,XXX / XX% / #,### ] | [justification — why this and not an alternative] |

## Visualization Design

### Layout (Desktop >= 1024px)
```
[ASCII mockup showing widget arrangement — or description if simple]
```

### Layout (Mobile < 768px)
```
[Scorecard-only adaptation — what collapses, what stays]
```

### Chart Specifications

| Chart ID | Type | Data Series | X-Axis | Y-Axis | Interaction | Notes |
|----------|------|-------------|--------|--------|-------------|-------|
| chart-1 | [line/bar/scorecard/funnel/...] | [series names] | [dimension] | [measure] | [hover tooltip / click-to-drill / both] | [special rules] |

### Scorecard Row

| Position | Metric | Format | Comparison | Sparkline? |
|----------|--------|--------|------------|------------|
| 1 | [metric] | [format] | vs previous period | Yes/No |
| 2 | [metric] | [format] | vs previous period | Yes/No |

### Time Handling
- **Default range:** [e.g., Last 30 days]
- **Comparison:** [e.g., vs previous period]
- **Granularity:** [daily / weekly / monthly]
- **Available presets:** [Last 7d, Last 30d, This Month, Custom]

## Progressive Disclosure

| Level | What's Shown | How to Access |
|-------|-------------|---------------|
| Glance | [scorecards, headline KPIs] | Default view |
| Explore | [charts, trends, breakdowns] | Scroll / tab |
| Analyze | [tables, campaign-level detail] | Click to drill down |
| Raw | [export CSV / API] | "Export" button |

## Component Tree

```
[PageName] (Server Component — src/app/{tenant}/{route}/page.tsx)
├── [DateRangePicker] (Client — date selection + comparison toggle)
├── [ScorecardsRow] (Client — KPI cards with sparklines)
│   ├── ScoreCard (Client — value + delta + sparkline)
│   └── ...
├── [ChartSection] (Client — main visualization area)
│   ├── [ChartComponent] (Client — uses {chart_library})
│   └── [ChartTooltip] (Client — hover detail)
└── [DrillDownTable] (Client — sortable detail table)
    └── Table (Shadcn)
```

## States

| State | Component | Behavior |
|-------|-----------|----------|
| Loading | [component] | [Skeleton pattern — number of cards, chart placeholder shape] |
| Empty (no source connected) | [component] | [CTA: "Conecta tu cuenta de {platform} para ver métricas"] |
| Empty (source connected, no data) | [component] | [Message: "Aún no hay datos para este período"] |
| Partial data | [component] | [Show available data + "Datos parciales" badge] |
| Error | [component] | [Alert with retry button] |

## Color Mapping

| Element | Color | Token / Hex |
|---------|-------|-------------|
| [channel/status] | [color name] | [value] |

## Responsive Behavior

| Breakpoint | Changes |
|------------|---------|
| Desktop >= 1024px | [Full layout as in mockup] |
| Tablet 768-1023px | [Specific adaptations — e.g., 2-col scorecards instead of 4] |
| Mobile < 768px | [Scorecards only, charts behind "Ver detalles", single column] |

## FSD File Structure

```
frontend/src/features/{domain}/
├── components/
│   ├── {feature}-dashboard.tsx     (Client Component — main layout)
│   ├── {feature}-scorecards.tsx    (Client Component — KPI row)
│   ├── {feature}-chart.tsx         (Client Component — main chart)
│   └── {feature}-drill-table.tsx   (Client Component — detail table)
├── types/
│   └── index.ts                    (TypeScript interfaces)
├── api/
│   └── {feature}-api.ts            (API functions using fetchClient)
├── hooks/
│   ├── use-{feature}-data.ts       (useQuery hook)
│   └── use-{feature}-filters.ts    (date range + source filter state)
└── index.ts                        (Public API exports)
```
```

---

## Checklist (before writing)

- [ ] Every metric has a "Why This Metric" justification
- [ ] All data sources verified against backend (endpoints exist or flagged as missing)
- [ ] Chart types validated against chart-selection-guide.md
- [ ] Loading, empty, error, AND partial-data states specified
- [ ] Responsive behavior defined (desktop, tablet, mobile)
- [ ] Time handling specified (default range, comparison, granularity)
- [ ] Progressive disclosure levels defined (glance → explore → analyze → raw)
- [ ] All Shadcn components verified in frontend/src/components/ui/
- [ ] Color mapping uses channel convention (Meta blue, Google red, etc.)
- [ ] The 5-Second Rule: main insight obvious at a glance
- [ ] One-liner story statement included in Story section
