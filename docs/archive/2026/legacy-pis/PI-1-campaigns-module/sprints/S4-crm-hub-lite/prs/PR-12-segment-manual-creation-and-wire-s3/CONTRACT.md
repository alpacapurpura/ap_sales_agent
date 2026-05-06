# CONTRACT — PR-12-segment-manual-creation-and-wire-s3

> Owner: PM main session (Opus 4.7). Cross-stack: BE (modules/campaigns) + FE (features/crm-hub + features/campaigns-lite + app routes). Builders: `nicolify-backend` (Sonnet) + `nicolify-frontend` (Sonnet) paralelo.

## § 0 Context Summary

| Campo | Valor |
|---|---|
| Architect run on | 2026-04-30 |
| Surface scope | cross-stack — BE `modules/campaigns/` (extend SegmentCreate DTO) + FE `frontend/src/features/{crm-hub,campaigns-lite}/` + app routes |
| Builders | `nicolify-backend` (Sonnet) BE delta + `nicolify-frontend` (Sonnet) FE primary |
| Auditors | `nicolify-backend-auditor` (REVIEW-backend.md) + `nicolify-frontend-auditor` (REVIEW-frontend.md) |
| Skills | backend-expert (BE delta), frontend-expert + tessl__zod + tessl__shadcn-ui (FE), tessl__react-patterns |
| Migrations | 0 (extend Pydantic DTO + service path) |

### Surface ownership mapping

| Path | Builder | Auditor |
|---|---|---|
| `backend/src/modules/campaigns/application/dtos/segment_dtos.py` (EXTEND) | `nicolify-backend` | `nicolify-backend-auditor` |
| `backend/src/modules/campaigns/application/services/segment_service.py` (EXTEND `create()` STATIC path) | mismo | mismo |
| `backend/tests/modules/campaigns/test_segment_create_static_with_lead_ids.py` (NEW integration) | mismo | mismo |
| `frontend/src/features/crm-hub/components/CreateSegmentDialog.tsx` (NEW) | `nicolify-frontend` | `nicolify-frontend-auditor` |
| `frontend/src/features/crm-hub/components/LaunchCampaignChoiceDialog.tsx` (NEW) | mismo | mismo |
| `frontend/src/features/crm-hub/components/SelectedContactsBar.tsx` (EXTEND PR-11 con action) | mismo | mismo |
| `frontend/src/features/crm-hub/api/use-create-segment-mutation.ts` (NEW) | mismo | mismo |
| `frontend/src/features/campaigns-lite/` (NEW feature) | mismo | mismo |
| `frontend/src/features/campaigns-lite/components/{CampaignNewClient,CampaignDetailClient,CampaignStatsCard,CampaignLifecycleButtons}.tsx` (NEW) | mismo | mismo |
| `frontend/src/features/campaigns-lite/api/{use-create-campaign-mutation,use-campaign-detail-query,use-campaign-stats-query,use-add-campaign-step-mutation,use-schedule-campaign-mutation}.ts` (NEW) | mismo | mismo |
| `frontend/src/features/campaigns-lite/types/index.ts` (NEW) | mismo | mismo |
| `frontend/src/app/(main)/[tenantId]/(dashboard)/sales/campañas/nuevo/page.tsx` (NEW) | mismo | mismo |
| `frontend/src/app/(main)/[tenantId]/(dashboard)/sales/campañas/[id]/page.tsx` (NEW) | mismo | mismo |
| `frontend/src/__tests__/architecture/test_campaign_new_consumes_canonical_api.test.ts` (NEW) | mismo | mismo |
| `frontend/e2e/specs/regression/sales/segment-create-and-launch-campaign.spec.ts` (NEW) | mismo | mismo |

## § 1 Existing systems audit

### Audit BE (PM main session, 2026-04-30)

```bash
grep -A 30 "@router.post" backend/src/modules/campaigns/api/routers/segments_router.py
grep -A 30 "@router.post" backend/src/modules/campaigns/api/routers/campaigns_router.py
grep -A 30 "class SegmentCreate\|class CampaignCreate\|class CampaignStepCreate" backend/src/modules/campaigns/application/dtos/
grep "SegmentType\|PredefinedSegmentFilter" backend/src/modules/campaigns/domain/
```

### Findings BE — gap detectado en SegmentCreate STATIC

| Sistema | Estado | Decisión |
|---|---|---|
| `POST /api/v1/segments/` con `SegmentCreate` | active | **EXTEND** — agregar campo `lead_ids: list[UUID] \| None` mutuamente exclusivo con `filter_dsl` para `segment_type=STATIC` |
| `SegmentCreate.filter_dsl: PredefinedSegmentFilter` | currently REQUIRED always | **EXTEND** — make Optional + add validator: `STATIC` requires `lead_ids` non-empty; `DYNAMIC` requires `filter_dsl` |
| `SegmentService.create()` | active (DYNAMIC path) | **EXTEND** — STATIC branch persiste lead_ids snapshot en `Segment.static_lead_ids` JSONB column existente (verificar migration history) o crea entries en tabla join existente |
| `POST /api/v1/campaigns/` con `CampaignCreate` | active | **REUSE direct** — soporta `segment_id` + `campaign_type` + `name` + `description` ready |
| `POST /api/v1/campaigns/{id}/steps/` | active (S1 PR-4) | **REUSE direct** — `CampaignStepCreate` con `step_type=CALL_SUBAGENT_BRIEF` + `step_index=0` + `step_config={}` |
| `POST /api/v1/campaigns/{id}/schedule` | active | **REUSE direct** — `scheduled_for: datetime` body |
| `POST /api/v1/campaigns/{id}/launch` | active | **REUSE direct** — transition SCHEDULED → RUNNING |
| `GET /api/v1/campaigns/{id}` | active | **REUSE direct** |
| `GET /api/v1/campaigns/{id}/stats` (PR-8) | active | **REUSE direct** |

**BE delta justificado**: extender `SegmentCreate` para STATIC con lead_ids es necesario para PI-1 cierre — sin esto, S4↔S3 wire incompleto. Cero migration (asumir column existente o usar JSONB en filter_dsl) — architect verifica + decide.

### Findings FE

| Sistema | Estado | Decisión |
|---|---|---|
| `features/crm-hub/components/SelectedContactsBar.tsx` (PR-11) | active post PR-11 | **EXTEND** — recibe action "Crear segmento" via slot pattern (PR-11 ya entrega API) |
| `frontend/src/components/ui/dialog.tsx` (Shadcn) | active | **REUSE direct** |
| `frontend/src/components/ui/sonner.tsx` (toast) | active | **REUSE direct** |
| RHF + Zod pattern | existing en otras features | **REUSE pattern** |
| `frontend/src/features/closer-studio/components/inbox/CampaignTag.tsx` (PR-8) | active | **REFERENCE pattern** + path link `/campañas/{id}` ahora resuelve real (era placeholder PR-8) |
| `lib/http-client::fetchClient` | active | **REUSE direct** |
| `features/campaigns-lite/` | NEW | **NEW feature** dedicated (separado de Growth Studio campaigns dashboard que tiene scope analytics) |

## § 2 BE delta — SegmentCreate extend

### 2.1 Pydantic DTO extension

```python
# backend/src/modules/campaigns/application/dtos/segment_dtos.py

from typing import Self
from pydantic import BaseModel, ConfigDict, Field, model_validator
from uuid import UUID
from src.modules.campaigns.domain.enums import SegmentType
from src.modules.campaigns.domain.segment_filter import PredefinedSegmentFilter


class SegmentCreate(BaseModel):
    """POST /api/v1/segments/ request body. Soporta DYNAMIC (filter_dsl) o STATIC (lead_ids)."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=1000)
    segment_type: SegmentType = SegmentType.DYNAMIC
    filter_dsl: PredefinedSegmentFilter | None = Field(
        default=None,
        description="Required when segment_type=DYNAMIC. None for STATIC.",
    )
    lead_ids: list[UUID] | None = Field(
        default=None,
        description="Required when segment_type=STATIC. Snapshot at creation. Max 10000.",
        max_length=10000,
    )

    @model_validator(mode="after")
    def _validate_dsl_xor_lead_ids(self) -> Self:
        if self.segment_type == SegmentType.STATIC:
            if not self.lead_ids or len(self.lead_ids) == 0:
                raise ValueError("STATIC segment requires non-empty lead_ids.")
            if self.filter_dsl is not None:
                raise ValueError("STATIC segment must not have filter_dsl.")
        else:  # DYNAMIC
            if self.filter_dsl is None:
                raise ValueError("DYNAMIC segment requires filter_dsl.")
            if self.lead_ids is not None:
                raise ValueError("DYNAMIC segment must not have lead_ids.")
        return self
```

### 2.2 Service extension

`SegmentService.create()` — agregar branch STATIC:

```python
async def create(self, *, tenant_id, dto: SegmentCreate, session) -> SegmentResponse:
    if dto.segment_type == SegmentType.STATIC:
        # Validate all lead_ids exist + belong to tenant (security gate)
        await self._validate_lead_ids_belong_to_tenant(tenant_id, dto.lead_ids, session)
        # Persist Segment with lead_ids snapshot
        segment = SegmentModel(
            tenant_id=tenant_id,
            name=dto.name,
            description=dto.description,
            segment_type=SegmentType.STATIC,
            filter_dsl=None,  # NULL para STATIC
            static_lead_ids=dto.lead_ids,  # JSONB column — verificar existence en migration
            ...
        )
    else:
        # existing DYNAMIC path
        ...
```

**Architect-instruction al builder**: verificar `SegmentModel.static_lead_ids` column existence. Si NO existe:
- Opción A: store en `filter_dsl` JSONB con shape `{"_static": True, "lead_ids": [...]}`
- Opción B: nueva tabla `segment_static_members(segment_id, lead_id, tenant_id)` — requiere migration idempotente
- **Builder decide en IMPL-LOG con justificación cuantitativa**

### 2.3 BE tests requeridos

```python
# backend/tests/modules/campaigns/test_segment_create_static_with_lead_ids.py

# Sin mocks (política PR-4)
async def test_segment_create_static_with_lead_ids_persists_snapshot(): ...
async def test_segment_create_static_validates_lead_ids_belong_to_tenant(): ...
async def test_segment_create_static_rejects_empty_lead_ids(): ...
async def test_segment_create_static_rejects_with_filter_dsl(): ...
async def test_segment_create_dynamic_still_works(): ...  # baseline preservado
async def test_segment_resolve_static_returns_persisted_lead_ids(): ...  # SegmentService.resolve() STATIC path
```

## § 3 FE — TS Types

```typescript
// frontend/src/features/campaigns-lite/types/index.ts

import { z } from "zod";

export const campaignTypeSchema = z.enum([
  "AGENT_CONVERSATION",
  // resto enum values existing — verificar al implementar
]);
export type CampaignType = z.infer<typeof campaignTypeSchema>;

export const campaignStatusSchema = z.enum([
  "DRAFT", "SCHEDULED", "RUNNING", "PAUSED", "COMPLETED", "CANCELLED",
]);
export type CampaignStatus = z.infer<typeof campaignStatusSchema>;

export interface CampaignResponse {
  id: string;
  tenant_id: string;
  name: string;
  description: string | null;
  campaign_type: CampaignType;
  status: CampaignStatus;
  segment_id: string | null;
  channel_priority: string[];
  offer_id: string | null;
  brand_summary_id: string | null;
  config: Record<string, unknown>;
  created_at: string;
  updated_at: string | null;
  scheduled_for: string | null;
  launched_at: string | null;
}

export interface CampaignStatsResponse {
  campaign_id: string;
  total_tasks: number;
  sent_count: number;
  responded_count: number;
  converted_count: number;
  response_rate: number;
  conversion_rate: number;
  currency: string | null;  // master-data
}

// Segment types extension PR-12
export const segmentCreateSchema = z.object({
  name: z.string().min(1).max(128),
  description: z.string().max(1000).optional(),
  segment_type: z.enum(["DYNAMIC", "STATIC"]),
  lead_ids: z.array(z.string().uuid()).max(10000).optional(),
  // filter_dsl optional — para PR-12 lite solo STATIC; DYNAMIC lo maneja PI-3 builder
}).refine(
  (data) => {
    if (data.segment_type === "STATIC") return data.lead_ids && data.lead_ids.length > 0;
    return true;
  },
  { message: "STATIC segment requires non-empty lead_ids" },
);
export type SegmentCreate = z.infer<typeof segmentCreateSchema>;

// Form Zod (CreateSegmentDialog)
export const createSegmentFormSchema = z.object({
  name: z.string().min(1, "El nombre es requerido").max(128),
  description: z.string().max(1000).optional(),
});
export type CreateSegmentFormValues = z.infer<typeof createSegmentFormSchema>;

// Form Zod (CampaignNewClient)
export const createCampaignFormSchema = z.object({
  name: z.string().min(1, "El nombre es requerido").max(255),
  description: z.string().max(2000).optional(),
  scheduled_for: z.string().datetime().optional(), // si vacío → DRAFT, no schedule
});
export type CreateCampaignFormValues = z.infer<typeof createCampaignFormSchema>;
```

## § 4 FE — Components

### 4.1 `CreateSegmentDialog.tsx`

```typescript
interface CreateSegmentDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  selectedLeadIds: string[];
  onSuccess: (segmentId: string) => void;  // → opens LaunchCampaignChoiceDialog
}
```

Body: Shadcn Dialog + RHF Form con `react-hook-form` + `zodResolver(createSegmentFormSchema)`. 2 fields visible (name required, description optional). Submit:
1. POST `/api/v1/segments/` con body `{name, description, segment_type: "STATIC", lead_ids: selectedLeadIds}`
2. Success → toast Sonner + onSuccess(segmentId)
3. Error → form error messages inline

### 4.2 `LaunchCampaignChoiceDialog.tsx`

```typescript
interface LaunchCampaignChoiceDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  segmentId: string;
  segmentName: string;
}
```

Body: Shadcn Dialog choice modal:
- Title: "Segmento '{segmentName}' creado"
- Body: "¿Quieres lanzar una campaña Telegram a estos contactos ahora?"
- Buttons:
  - Primary: "Sí, crear campaña" → `router.push("/sales/campañas/nuevo?segment_id={id}")` + close
  - Secondary: "Más tarde" → close

### 4.3 `CampaignNewClient.tsx`

```typescript
"use client";

interface CampaignNewClientProps {
  segmentId: string | null;
}
```

Body:
- Header: "Nueva campaña Telegram"
- Subtitle: si `segmentId` set → "Para segmento '{nombre}'" (fetch segment name); sino warning "Selecciona un segmento primero" + button back
- Form (RHF + Zod):
  - Name (required)
  - Description (optional textarea)
  - Schedule: opcional datetime picker (Shadcn `smart-datetime-picker` existing) — si vacío → crear DRAFT; si fecha → schedule
- Submit pipeline:
  1. POST `/api/v1/campaigns/` con `{name, description, campaign_type: "AGENT_CONVERSATION", segment_id, channel_priority: ["telegram"], created_by_source: "manual"}`
  2. Recibe `{id}` → POST `/api/v1/campaigns/{id}/steps/` con `{step_type: "CALL_SUBAGENT_BRIEF", step_index: 0, step_config: {}}`
  3. Si `scheduled_for` set → POST `/api/v1/campaigns/{id}/schedule` con `{scheduled_for}`
  4. Toast success + `router.push("/sales/campañas/{id}")`

### 4.4 `CampaignDetailClient.tsx` (placeholder lite)

```typescript
"use client";

interface CampaignDetailClientProps {
  campaignId: string;
}
```

Sections:
- Header: campaign name + status badge + segment_id link
- `CampaignStatsCard` (sub-component) consume `GET /api/v1/campaigns/{id}/stats` PR-8 — render: total_tasks, sent_count, responded_count, conversion_rate, currency-formatted spend (master-data rule)
- `CampaignLifecycleButtons` (sub-component) — botones según status:
  - DRAFT → "Lanzar" → POST `/launch` (o si era SCHEDULED → "Activar ahora")
  - RUNNING → "Pausar" (transition placeholder; full UX PI-3)
  - SCHEDULED → "Cancelar" (placeholder)
  - PAUSED/COMPLETED → no actions

## § 5 Pages

### 5.1 `/sales/campañas/nuevo/page.tsx`

```typescript
import { CampaignNewClient } from "@/features/campaigns-lite/components/CampaignNewClient";

interface PageProps {
  searchParams: Promise<{ segment_id?: string }>;
}

export default async function CampaignNewPage({ searchParams }: PageProps) {
  const params = await searchParams;
  return (
    <div className="container mx-auto p-6 max-w-2xl">
      <CampaignNewClient segmentId={params.segment_id ?? null} />
    </div>
  );
}
```

### 5.2 `/sales/campañas/[id]/page.tsx`

```typescript
import { CampaignDetailClient } from "@/features/campaigns-lite/components/CampaignDetailClient";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default async function CampaignDetailPage({ params }: PageProps) {
  const { id } = await params;
  return (
    <div className="container mx-auto p-6">
      <CampaignDetailClient campaignId={id} />
    </div>
  );
}
```

## § 6 Wire S4↔S3 — flow completo

```
[ContactsPage]
  user selects 3 contactos
  ↓
[SelectedContactsBar shows action "Crear segmento"]  ← PR-12 inyecta action via slot
  click → opens CreateSegmentDialog
  ↓
[CreateSegmentDialog]
  user fills name → submit
  POST /api/v1/segments/ {type: STATIC, lead_ids: [3 UUIDs]}  ← BE delta
  201 → toast "Segmento creado"
  ↓
[LaunchCampaignChoiceDialog opens]
  user clicks "Sí, crear campaña"
  router.push("/sales/campañas/nuevo?segment_id={id}")
  ↓
[/sales/campañas/nuevo]
  CampaignNewClient form
  user fills name → submit
  POST /api/v1/campaigns/ {type: AGENT_CONVERSATION, segment_id, channel_priority: ["telegram"]}
  201 → POST /api/v1/campaigns/{id}/steps/ {step_type: CALL_SUBAGENT_BRIEF, ...}
  (optional) POST /api/v1/campaigns/{id}/schedule {scheduled_for}
  toast → router.push("/sales/campañas/{id}")
  ↓
[/sales/campañas/{id}]
  CampaignDetailClient renders stats card + Lanzar button
  user click "Lanzar" → POST /launch
  S3 OutboundOrchestrator (PR-7) ejecuta tasks Telegram
  PR-8 inbound recognition tags conversaciones cuando lead responde
```

## § 7 Arch test

```typescript
// frontend/src/__tests__/architecture/test_campaign_new_consumes_canonical_api.test.ts

import { test, expect } from "vitest";
import * as fs from "node:fs";
import * as path from "node:path";

test("CampaignNewClient consume solo API canonical /api/v1/campaigns + /api/v1/segments", () => {
  const filePath = path.resolve(__dirname, "../../features/campaigns-lite/components/CampaignNewClient.tsx");
  const source = fs.readFileSync(filePath, "utf-8");

  // No FE-fabricated endpoints (anti-drift)
  const apiCalls = source.match(/\/api\/v1\/[^"`'\s)]+/g) ?? [];
  for (const call of apiCalls) {
    expect(call).toMatch(/^\/api\/v1\/(campaigns|segments)/);
  }
});
```

## § 8 E2E Playwright

`frontend/e2e/specs/regression/sales/segment-create-and-launch-campaign.spec.ts` — flow completo § 6.

Si infra gap (Telegram bot mock no levantado en CI) → `test.skip` documented similar pattern PR-9.

**Manual checklist Chris real gate ship MVP S4** — heredando learning S3 PR-9. Después merge S4, Chris ejecuta flow real staging:
1. Login tenant testing → `/sales/contactos`
2. Seleccionar 3 contactos con telegram_id
3. Crear segmento "Test S4"
4. Lanzar campaña → schedule 1 min future
5. Verificar Telegram delivery 3 mensajes (voice fidelity tenant)
6. Responder desde Telegram → verificar inbound recognition tag campaign chip en Inbox

## § 9 Open questions for PM

| Decisión | Resolución |
|---|---|
| EXTEND SegmentCreate vs new endpoint | EXTEND con XOR validator (filter_dsl XOR lead_ids) |
| `static_lead_ids` storage column vs JSONB filter_dsl | Builder decide en IMPL-LOG (verificar `SegmentModel` columns first) |
| Modal vs inline form | Modal Dialog focused |
| Choice modal vs auto-redirect | Choice (user agency) |
| Single-step vs full DAG | Single-step `CALL_SUBAGENT_BRIEF` (S4 lite scope) |
| Schedule mechanism | Separate POST `/schedule` after create + step (existing API) |
| `/campañas/[id]` lite | Stats card + lifecycle buttons (no full overview) |
| Telegram channel hardcoded | `channel_priority: ["telegram"]` PR-12 lite. PI-2 multi-canal expand |

## § 10 Quality gates expectations

- BE: ruff + mypy + pytest tests verde nativo. Cero migration (extend DTO + service path solamente, salvo builder decide tabla nueva).
- FE: tsc strict + ESLint + Vitest verde. E2E smoke (o test.skip documented).
- Arch tests: forward-compat verde. NO new layer paralelo.

---

<!-- @pm: CONTRACT.md ready cross-stack. BE delta = SegmentCreate extend STATIC + lead_ids XOR validator. FE delta = 4 new components + 2 routes + features/campaigns-lite/. Auto-loop: BE-builder + FE-builder paralelo, cada uno spawnea SU auditor. Próximo paso: ejecutar prompts/02-builder-start.md cuando PR-11 FE merge. -->
