# Email Automations UX Redesign — Design Spec

**Date:** 2026-04-10
**Status:** Approved
**Mockup:** `docs/mockups/email-automations-redesign.html`
**Depends on:** `2026-04-10-email-automations-etl-design.md` (ETL must save per-automation rows first)

## Problem

The current Automatizaciones tab has critical data and UX issues:

1. **Bug: Suscriptores = 0** — reads `subscribers_in_queue` which is 0 for completed automations. Fix: `ingresados = completed + in_queue`.
2. **Bug: Completación shows CTOR** — `completion_rate` maps `click_to_open_rate` instead of actual completion. Fix: `completed / (completed + in_queue) × 100`.
3. **Bug: Status hardcoded "active"** — never reads MailerLite's `enabled` flag.
4. **Missing metrics:** CTOR, unsubscribes, per-email stats — all available in API response, discarded.
5. **No drill-down:** Can't see individual emails in a sequence or identify where engagement drops.
6. **No interpretation guidance:** Metrics lack context — a CEO can't tell if 66.7% open rate is good or bad.

## Design Overview

Three-level progressive disclosure:

| Level | View | Audience | Interaction |
|---|---|---|---|
| **L1: Table** | Automation list with health scores | CEO | Scan, filter, sort |
| **L2: Accordion** | Email sequence pipeline with drop-off visualization | Analyst | Click row → expand inline |
| **L3: Sidebar** | Individual email detail, preview, AI diagnosis | Analyst deep-dive | Click email node → DetailPanel |

Every metric at every level has an `ⓘ` info popover explaining: what it measures, formula, and how to interpret (color-coded thresholds).

## L1: Table Redesign

### Columns (replacing current)

| Column | Source | Description in tooltip |
|---|---|---|
| **Automatización** | `name` + `automation_type` + `steps_count` | Name, type badge, email count |
| **Ingresados** | `completed + in_queue` (NEW) | Total that entered the flow |
| **Completaron** | `completed` + `(completed/ingresados×100)%` | Count + completion rate |
| **Open Rate** | `open_rate` | % emails opened, color-coded vs benchmark |
| **Click Rate** | `click_rate` | % emails clicked, color-coded |
| **CTOR** | `click_to_open_rate` (NEW in DTO) | Clicks/Opens — purest engagement metric |
| **Unsubs** | `unsubscribes_count` (NEW in DTO) | Unsubscribes during this automation |
| **Salud** | Computed composite 0-100 (NEW) | Health bar + score |

### Removed columns
- **Estado** — moved to inline badge under name (less useful as standalone column since we only show active)
- **Emails enviados** — moved to accordion detail

### Health Score formula

```
health = (
  0.30 × normalize(open_rate, 0, 100)
  + 0.25 × normalize(click_rate, 0, 30)
  + 0.20 × normalize(ctor, 0, 50)
  + 0.15 × normalize(completion_rate, 0, 100)
  − 0.10 × normalize(unsub_rate, 0, 5)
) × 100
```

Color: green (>70), amber (40-70), red (<40), gray (no data).

### Filter pills
- Todas | Bienvenida | Nutrición | Workflow
- Filter by `automation_type`

### Info tooltips (ⓘ)
Every column header has an info popover with:
- **Title**: metric name
- **Description**: what it measures in plain language
- **Formula**: how it's calculated (monospace)
- **How to interpret**: color-coded thresholds (green/amber/red)

## L2: Accordion — Email Sequence Pipeline

Click a table row → inline accordion expands showing the email sequence visually.

### Data required (NEW — from MailerLite `steps[]` array)

Per automation, extract each step where `type == "email"`:

```typescript
interface AutomationStep {
  stepId: string;
  stepNumber: number;          // 1-based position
  type: 'email' | 'delay' | 'condition';
  // Email steps:
  subject?: string;
  fromName?: string;
  emailsSent: number;
  uniqueOpens: number;
  openRate: number;
  uniqueClicks: number;
  clickRate: number;
  unsubscribes: number;
  bounces: number;
  screenshotUrl?: string | null;
  previewUrl?: string | null;
  // Delay steps:
  delayValue?: number;
  delayUnit?: string;           // "minutes" | "hours" | "days"
}
```

### Visual pipeline layout

```
[Email 1] ——→ [Email 2] ——→ [Email 3]
  87.5%        ⏱ 3d         58.3%        ⏱ 5d          26.5%
  open         −29% drop     open         −45% drop      open
  15% click                  5% click                    0% click
  ★ Mejor                                               ⚡ Atención
```

- **Email nodes**: card with step number, subject (truncated), open rate, click rate
- **Connectors**: delay duration + drop-off percentage between steps
- **Badges**: `★ Mejor` (green) on highest open×click product, `⚡ Atención` (red) on lowest or 0% click
- **Funnel bar**: horizontal stacked bar showing retention across steps
- **AI Insight**: diagnosis box summarizing where engagement drops and suggested actions

### Drop-off calculation

```
dropoff_pct = (1 - step[n].emailsSent / step[n-1].emailsSent) × 100
```

Color: green (<10%), amber (10-30%), red (>30%).

### Info tooltips in pipeline
- Each Open/Click label in email nodes has `ⓘ` with contextual description
- Drop-off connector has `ⓘ` explaining what the percentage means

## L3: Sidebar — Email Detail (DetailPanel)

Click an email node in the pipeline → opens `DetailPanel` (size="md", 550px) from right.

### Sections

1. **Header**: Subject line + position in sequence + automation name
2. **Metrics grid** (3×2): Enviados, Abiertos, Clicks, Open Rate, Click Rate, CTOR — each with `ⓘ`
3. **vs Benchmarks**: Table comparing this email's metrics to industry averages — section header has `ⓘ` explaining benchmark source
4. **Vista previa**: 
   - If `screenshotUrl` available: render as `<img>`
   - If `previewUrl` available: link to open in new tab "Ver email completo en MailerLite"
   - Fallback: placeholder mock
5. **Diagnóstico Inteligente**: AI-generated analysis (computed client-side from metrics patterns):
   - High open + low click → "Subject line efectivo pero CTA débil"
   - Low open → "Revisar subject line o timing de envío"
   - High unsubs → "Contenido no alineado con expectativa del suscriptor"
   - Compare vs previous step → "Caída de X% vs email anterior"
6. **Detalles**: Subject, From, step type, position, created date

### Info tooltips in sidebar
- Every metric box label has `ⓘ` with description + interpretation thresholds
- Benchmark section header has `ⓘ` explaining data source
- Each benchmark row has `ⓘ` with industry average context

## Backend Changes

### 1. MailerLite Provider: Extract step data

**File:** `mailerlite_provider.py`, `_extract_automations()`

Currently discards `steps[]`. Change to iterate email-type steps and store in `extra`:

```python
extra = {
    "source": "automation",
    "automation_name": name,
    "automation_status": "active" if auto.get("enabled") else "paused",  # FIX: read actual
    "automation_type": classify_automation_type(name),
    "completed_subscribers": completed,
    "subscribers_in_queue": in_queue,
    "steps_count": len(steps),
    "steps": [                         # NEW
        {
            "step_id": step["id"],
            "step_number": idx + 1,
            "type": step.get("type", "email"),
            "subject": step.get("subject", ""),
            "from_name": step.get("from_name", ""),
            "emails_sent": step.get("email", {}).get("stats", {}).get("sent", 0),
            "unique_opens": step.get("email", {}).get("stats", {}).get("unique_opens_count", 0),
            "open_rate": parse_rate(step.get("email", {}).get("stats", {}).get("open_rate", 0)),
            "unique_clicks": step.get("email", {}).get("stats", {}).get("unique_clicks_count", 0),
            "click_rate": parse_rate(step.get("email", {}).get("stats", {}).get("click_rate", 0)),
            "unsubscribes": step.get("email", {}).get("stats", {}).get("unsubscribes_count", 0),
            "bounces": step.get("email", {}).get("stats", {}).get("hard_bounces_count", 0) + step.get("email", {}).get("stats", {}).get("soft_bounces_count", 0),
            "screenshot_url": step.get("email", {}).get("screenshot_url"),
            "preview_url": step.get("email", {}).get("preview_url"),
            # Delay steps:
            "delay_value": step.get("value"),
            "delay_unit": step.get("unit"),
        }
        for idx, step in enumerate(steps)
    ],
}
```

No additional API calls needed — data already in `GET /automations` response.

### 2. DTO: Extend `EmailAutomationDTO`

**File:** `email_dashboard_dto.py`

```python
class AutomationStepDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    step_id: str
    step_number: int
    type: str                          # "email" | "delay" | "condition"
    subject: str | None = None
    from_name: str | None = None
    emails_sent: int = 0
    unique_opens: int = 0
    open_rate: float = 0.0
    unique_clicks: int = 0
    click_rate: float = 0.0
    unsubscribes: int = 0
    bounces: int = 0
    screenshot_url: str | None = None
    preview_url: str | None = None
    delay_value: int | None = None
    delay_unit: str | None = None

class EmailAutomationDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    automation_id: str
    name: str
    automation_type: str
    status: str
    active_subscribers: int = 0        # RENAMED semantically to "ingresados" in frontend
    completed: int = 0
    emails_sent: int = 0
    open_rate: float = 0.0
    click_rate: float = 0.0
    click_to_open_rate: float = 0.0    # NEW
    completion_rate: float = 0.0       # FIX: actual completion, not CTOR
    unsubscribes: int = 0              # NEW
    steps: list[AutomationStepDTO] = []  # NEW
```

### 3. Service: Fix computation bugs

**File:** `email_dashboard_service.py`, `get_automations()`

```python
# FIX 1: active_subscribers = completed + in_queue (was just in_queue)
ingresados = int(extra.get("completed_subscribers", 0)) + int(extra.get("subscribers_in_queue", 0))

# FIX 2: completion_rate = actual completion (was CTOR)
completion_rate = (completed / ingresados * 100) if ingresados > 0 else 0

# FIX 3: status from API (was hardcoded "active")
status = extra.get("automation_status", "active")

# NEW: click_to_open_rate from metric row
ctor = float(m.get("click_to_open_rate", 0))

# NEW: unsubscribes from metric row
unsubs = int(m.get("unsubscribes", 0))

# NEW: parse steps from extra
steps = [AutomationStepDTO(**s) for s in extra.get("steps", [])]
```

## Frontend Changes

### 1. Types: Extend `EmailAutomation`

**File:** `mail-types.ts`

```typescript
export interface AutomationStep {
  stepId: string;
  stepNumber: number;
  type: 'email' | 'delay' | 'condition';
  subject?: string;
  fromName?: string;
  emailsSent: number;
  uniqueOpens: number;
  openRate: number;
  uniqueClicks: number;
  clickRate: number;
  unsubscribes: number;
  bounces: number;
  screenshotUrl?: string | null;
  previewUrl?: string | null;
  delayValue?: number | null;
  delayUnit?: string | null;
}

export interface EmailAutomation {
  automationId: string;
  name: string;
  automationType: string;
  status: string;
  activeSubscribers: number;      // Now: completed + in_queue
  completed: number;
  emailsSent: number;
  openRate: number;
  clickRate: number;
  clickToOpenRate: number;        // NEW
  completionRate: number;         // FIXED: actual completion
  unsubscribes: number;           // NEW
  steps: AutomationStep[];        // NEW
}
```

### 2. Components

#### `MailAutomatizacionesTab.tsx` — Rewrite

- **KPI row**: 4 cards (Ingresados, Open Rate Prom, Click Rate Prom, Salud General) — each with `MetricInfoPopover`
- **Table**: New columns (Ingresados, Completaron, Open, Click, CTOR, Unsubs, Salud)
  - Each header wrapped in Shadcn `Tooltip` with `Info` icon and description
  - Filter pills for automation_type
  - Click row → toggle accordion
- **Accordion row**: Inline `AutomationPipeline` component
- Compute `healthScore` client-side per automation

#### `AutomationPipeline.tsx` — NEW component

- Renders email steps as horizontal card pipeline with connectors
- Each email node: step number, subject, open rate, click rate with `ⓘ` tooltips
- Connectors: delay duration + drop-off % with `ⓘ` tooltip
- Badges: `★ Mejor` / `⚡ Atención`
- Funnel bar below
- AI insight box (deterministic rules, not LLM)
- Click email node → open sidebar

#### `AutomationStepSidebar.tsx` — NEW component

- Uses `DetailPanel` (size="md")
- State: local `useState<AutomationStep | null>` in parent
- Sections: metrics grid with `ⓘ`, benchmarks with `ⓘ`, preview, diagnosis, details
- Diagnosis rules (client-side):

```typescript
function diagnoseStep(step: AutomationStep, prevStep?: AutomationStep): string[] {
  const insights: string[] = [];
  if (step.openRate > 50 && step.clickRate < 2)
    insights.push("Subject line efectivo pero CTA débil — prueba un botón más visible o copy más directo");
  if (step.openRate < 25)
    insights.push("Apertura baja — prueba un subject más específico o personalizado");
  if (step.unsubscribes > 2)
    insights.push("Desuscripciones altas — el contenido no cumple la expectativa del suscriptor");
  if (prevStep && step.openRate < prevStep.openRate * 0.6)
    insights.push(`Caída de ${((1 - step.openRate/prevStep.openRate) * 100).toFixed(0)}% vs email anterior — posible fatiga de secuencia`);
  return insights;
}
```

### 3. Info Tooltip Content Dictionary

Central dictionary for all metric descriptions, to be used across KPIs, table headers, pipeline nodes, and sidebar:

```typescript
export const METRIC_INFO: Record<string, {
  title: string;
  description: string;
  formula?: string;
  interpret?: { good: string; mid: string; bad: string };
}> = {
  ingresados: {
    title: "Ingresados",
    description: "Total de suscriptores que entraron a este flujo automatizado.",
    formula: "completados + en cola",
    interpret: { good: "Más ingresados = mayor alcance automatizado", mid: "", bad: "" },
  },
  completaron: {
    title: "Completaron",
    description: "Suscriptores que recibieron TODOS los emails de la secuencia.",
    formula: "completados / ingresados × 100",
    interpret: { good: ">60% excelente retención", mid: "30-60% revisar contenido medio", bad: "<30% secuencia pierde gente" },
  },
  open_rate: {
    title: "Open Rate",
    description: "Porcentaje de emails abiertos sobre el total entregado. Refleja la calidad de tus subject lines.",
    formula: "emails abiertos / emails entregados × 100",
    interpret: { good: ">50% excelente", mid: "30-50% aceptable", bad: "<30% mejorar subjects" },
  },
  click_rate: {
    title: "Click Rate",
    description: "Porcentaje de emails donde al menos un enlace fue clickeado. Mide si tu contenido genera acción.",
    formula: "emails con click / emails entregados × 100",
    interpret: { good: ">5% muy bueno", mid: "2-5% promedio", bad: "<2% CTA no conecta" },
  },
  ctor: {
    title: "Click-to-Open Rate (CTOR)",
    description: "De los que abrieron, ¿cuántos hicieron click? La métrica más pura de engagement.",
    formula: "clicks únicos / aperturas únicas × 100",
    interpret: { good: ">15% contenido muy relevante", mid: "8-15% normal", bad: "<8% contenido no convence" },
  },
  unsubs: {
    title: "Desuscripciones",
    description: "Personas que se desuscribieron durante esta automatización.",
    interpret: { good: "0-1 normal", mid: "2-3 monitorear", bad: ">3 revisar frecuencia y relevancia" },
  },
  health: {
    title: "Score de Salud",
    description: "Índice compuesto 0-100 que combina apertura, clicks, CTOR, completación y penaliza desuscripciones.",
    formula: "0.3×open + 0.25×click + 0.2×CTOR + 0.15×completion − 0.1×unsub_rate",
    interpret: { good: ">70 saludable", mid: "40-70 oportunidad de mejora", bad: "<40 acción urgente" },
  },
};
```

## Test Strategy

### Backend
- `test_email_dashboard_service.py`: Test `ingresados = completed + in_queue`, actual `completion_rate`, CTOR mapping, unsubs, steps parsing
- `test_mailerlite_provider_enhanced.py`: Test step extraction from mock API response

### Frontend
- `MailTabs.test.tsx`: Table renders new columns (CTOR, Unsubs, Salud), accordion toggles, health score computation
- New: `AutomationPipeline.test.tsx`: Pipeline renders steps, badges, drop-off calculation, AI insight generation
- New: `AutomationStepSidebar.test.tsx`: Sidebar renders metrics, benchmarks, diagnosis

## Out of Scope

- Revenue attribution per automation (MailerLite API does not provide this)
- Per-subscriber activity (`GET /automations/{id}/activity` — costs N API calls, defer to v2)
- A/B test split display (not available in current data)
- Historical trend per automation (would need time-series storage of per-automation snapshots)

## Migration

No database migration needed. Changes are:
1. ETL: extract more data from same API call (store in `extra` JSON field)
2. Service: fix field mappings + parse steps from `extra`
3. Frontend: new components consuming existing API endpoint
