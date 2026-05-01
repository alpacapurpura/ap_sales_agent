# CONTRACT — PR-11-fe-primitives-and-contactos-page

> Owner: PM main session (Opus 4.7) — architect spawn pattern reservada para PRs de mayor complejidad. Surface FE puramente. SSoT pre-implementación para `nicolify-frontend` (Sonnet) builder.

## § 0 Context Summary

| Campo | Valor |
|---|---|
| Architect run on | 2026-04-30 |
| Surface scope | frontend — `frontend/src/{components/shared,features/crm-hub,app/(main)/[tenantId]/(dashboard)/sales/contactos}/` |
| Builder | `nicolify-frontend` (Sonnet) |
| Auditor | `nicolify-frontend-auditor` (Opus) |
| Skills consulted | frontend-expert (FSD-Lite + Server/Client patterns), tessl__shadcn-ui, tessl__tailwind, tessl__react-patterns |
| Migrations | 0 |
| New deps | `@tanstack/react-table` (FE table primitive — verificado NO existe en package.json; agregado en PR-11) |

### Surface ownership mapping

Todos los paths bajo `nicolify-frontend` builder + `nicolify-frontend-auditor`:
- `frontend/src/components/shared/data-table/**` (NEW)
- `frontend/src/features/crm-hub/**` (NEW)
- `frontend/src/app/(main)/[tenantId]/(dashboard)/sales/contactos/page.tsx` (REPLACE stub)
- `frontend/src/__tests__/architecture/test_contact_*.test.ts` (NEW arch tests — 4)
- `frontend/e2e/specs/regression/sales/contactos.spec.ts` (NEW)
- `frontend/package.json` (ADD `@tanstack/react-table`)

## § 1 Existing systems audit (NO NEW LAYER rule)

### Audit cross-FE (PM main session, 2026-04-30)

```bash
find frontend/src/components/shared -type d
ls frontend/src/components/ui/   # Shadcn primitives existentes
grep "@tanstack" frontend/package.json
ls frontend/src/features/        # bounded contexts
ls frontend/src/features/closer-studio/components/inbox/  # pattern reference (PR-8)
grep -rn "useForm\|zodResolver" frontend/src/features/  # form pattern reference
grep -rn "useQuery\|@tanstack/react-query" frontend/src/features/  # query pattern
cat "frontend/src/app/(main)/[tenantId]/(dashboard)/sales/contactos/page.tsx"  # current stub
```

### Sistemas existentes encontrados

| Sistema | Path | Estado | Decisión |
|---|---|---|---|
| `components/shared/` (cross-feature primitives) | `app-header/`, `layout/`, `navigation/`, `ErrorBoundary.tsx`, etc. | active | **EXTEND** — agregar `data-table/` siguiendo mismo pattern |
| `components/ui/` (Shadcn primitives) | `table.tsx`, `sheet.tsx`, `dialog.tsx`, `badge.tsx`, `checkbox.tsx`, `input.tsx`, `popover.tsx`, `command.tsx`, `sonner.tsx`, `card.tsx`, `tooltip.tsx`, etc. | active | **REUSE direct** — no wrappers paralelos |
| `@tanstack/react-query` (^5.90.19) | `package.json` | active | **REUSE direct** — patterns existing en features (closer-studio uses) |
| `@tanstack/react-table` | NO instalado | absent | **ADD dep** — table headless primitive (1000 clientes virtualization PI-3 ready) |
| `closer-studio/components/inbox/CampaignTag.tsx` | `frontend/src/features/closer-studio/components/inbox/CampaignTag.tsx` (PR-8) | active | **REFERENCE pattern** (Shadcn Badge clickable + Tooltip — copy pattern para LifecycleStageChip + ScoreBadge) |
| `lib/http-client::fetchClient` | `frontend/src/lib/http-client.ts:64` | active | **REUSE direct** — auto-injects `X-Tenant-ID` |
| `/sales/contactos/page.tsx` (stub "Próximamente") | `frontend/src/app/(main)/[tenantId]/(dashboard)/sales/contactos/page.tsx` | placeholder | **REPLACE entire file** — Server Component thin → renders `ContactsPageClient` |
| `useFormRuntime` (brand-studio internal) | `frontend/src/features/brand-studio/actions/ThemeInjectorAction.tsx` + `components/form-runtime/` | active (brand-studio specific) | **OFF-SCOPE** PR-11 — usar `react-hook-form + zodResolver` pattern estándar para `CreateSegmentDialog` (PR-12) |

### Decisión: NEW DataTable shared primitive

**NEW** en `components/shared/data-table/`, NO en `features/crm-hub/`. Razones:

1. **Cross-feature reuse**: PR-12 + PI-3 expandirán uso a campaigns + segmentos. Si nace en feature crm-hub, refactor garantizado PI-3.
2. **TanStack headless**: maneja virtualization 10k rows PI-3 (1000 clientes lens). Custom Shadcn = refactor a TanStack en PI-3 doloroso.
3. **Cero deuda**: arch test enforces `data-table/` lives en `components/shared/` (PR-11 incluye este test).
4. **No-skip rule**: si emerge primitive, forzar location correcta desde día 1 (Chris framing).

## § 2 TS Types — mirror Pydantic (CRITICAL forward-compat)

```typescript
// frontend/src/features/crm-hub/types/index.ts

import { z } from "zod";

/** Mirror exacto de backend ContactFilterParams (CANONICAL_FILTER_FIELDS).
 *  Arch test test_filter_params_subset valida que estos keys matchean Pydantic.
 */
export const CONTACT_FILTER_FIELDS = [
  "lifecycle_stage_in", "score_min", "score_max",
  "source_in",
  "has_email", "has_phone", "has_telegram_id", "has_whatsapp_id",
  "has_instagram_id", "has_tiktok_id",
  "created_after", "created_before", "last_activity_after", "last_activity_before",
  "is_inactive",
  "has_campaign_engagement",
  "country_in",
  "q",
] as const;

export type ContactFilterField = (typeof CONTACT_FILTER_FIELDS)[number];

export const lifecycleStageSchema = z.enum([
  "subscriber", "lead", "mql", "sql", "opportunity",
  "customer", "evangelist", "churned",
]);
export type LifecycleStage = z.infer<typeof lifecycleStageSchema>;

export const contactFilterParamsSchema = z.object({
  lifecycle_stage_in: z.array(lifecycleStageSchema).optional(),
  score_min: z.number().int().min(0).max(100).optional(),
  score_max: z.number().int().min(0).max(100).optional(),
  source_in: z.array(z.string()).optional(),
  has_email: z.boolean().optional(),
  has_phone: z.boolean().optional(),
  has_telegram_id: z.boolean().optional(),
  has_whatsapp_id: z.boolean().optional(),
  has_instagram_id: z.boolean().optional(),
  has_tiktok_id: z.boolean().optional(),
  created_after: z.string().datetime().optional(),
  created_before: z.string().datetime().optional(),
  last_activity_after: z.string().datetime().optional(),
  last_activity_before: z.string().datetime().optional(),
  is_inactive: z.boolean().optional(),
  has_campaign_engagement: z.boolean().optional(),
  country_in: z.array(z.string().length(2)).optional(),
  q: z.string().max(120).optional(),
});
export type ContactFilterParams = z.infer<typeof contactFilterParamsSchema>;

export interface ContactListItem {
  id: string;
  full_name: string | null;
  primary_email: string | null;
  primary_phone: string | null;
  lifecycle_stage: LifecycleStage;
  lead_score: number;
  is_inactive: boolean;
  last_activity_at: string | null;
  lead_source: string | null;
  country: string | null;
  has_telegram_id: boolean;
  has_whatsapp_id: boolean;
  has_instagram_id: boolean;
  has_tiktok_id: boolean;
  has_email: boolean;
  has_phone: boolean;
  has_recent_campaign_engagement: boolean | null;
  created_at: string;
}

export interface ContactIdentity {
  type: string;
  value: string;
  is_primary: boolean;
  verification_status: string;
  last_seen_at: string;
}

export interface ContactDetail {
  id: string;
  full_name: string | null;
  primary_email: string | null;
  primary_phone: string | null;
  lifecycle_stage: LifecycleStage;
  lead_score: number;
  rfm_segment: string | null;
  lifetime_value: number;
  is_inactive: boolean;
  first_conversion_at: string | null;
  first_seen_at: string | null;
  last_activity_at: string | null;
  lead_source: string | null;
  lead_source_detail: string | null;
  traits: Record<string, unknown>;
  computed_traits: Record<string, unknown>;
  created_at: string;
  updated_at: string | null;
  // Lead-level optional
  lead_id: string | null;
  telegram_id: string | null;
  whatsapp_id: string | null;
  instagram_id: string | null;
  tiktok_id: string | null;
  api_id: string | null;
  fit_score: number | null;
  intent_score: number | null;
  temperature: string | null;
  is_blacklisted: boolean | null;
  last_interaction_date: string | null;
  country: string | null;
  conversation_summary: string | null;
  identities: ContactIdentity[];
}

export interface PaginatedResponse<T> {
  items: T[];
  total_count: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

/** Slot pattern PI-3 expansion. */
export interface SelectedContactsBarAction {
  id: string;
  label: string;
  icon?: React.ReactNode;
  variant?: "default" | "secondary" | "destructive";
  onClick: (selectedIds: string[]) => void | Promise<void>;
  /** Si requires ≥1 selected (default true). */
  requiresSelection?: boolean;
}
```

## § 3 React Query hooks

### 3.1 `use-contacts-query.ts`

```typescript
// frontend/src/features/crm-hub/api/use-contacts-query.ts
import { useQuery } from "@tanstack/react-query";
import { fetchClient } from "@/lib/http-client";
import type { ContactListItem, ContactFilterParams, PaginatedResponse } from "../types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "";

export interface UseContactsQueryParams {
  filters: ContactFilterParams;
  limit: number;
  offset: number;
}

export function useContactsQuery(params: UseContactsQueryParams) {
  return useQuery<PaginatedResponse<ContactListItem>>({
    queryKey: ["crm", "contacts", params],
    queryFn: async () => {
      const search = buildSearchParams(params);
      const res = await fetchClient(`${API_URL}/api/v1/contacts?${search.toString()}`);
      if (!res.ok) throw new Error(`Failed to load contacts: ${res.status}`);
      return res.json();
    },
    staleTime: 30_000,
    placeholderData: (prev) => prev, // pagination smooth UX
  });
}

function buildSearchParams(p: UseContactsQueryParams): URLSearchParams {
  const sp = new URLSearchParams();
  sp.set("limit", String(p.limit));
  sp.set("offset", String(p.offset));
  for (const [k, v] of Object.entries(p.filters)) {
    if (v === undefined || v === null) continue;
    if (Array.isArray(v)) {
      // Comma-separated for list filters (compact URL)
      if (v.length > 0) sp.set(k, v.join(","));
    } else {
      sp.set(k, String(v));
    }
  }
  return sp;
}
```

### 3.2 `use-contact-detail-query.ts`

```typescript
import { useQuery } from "@tanstack/react-query";
import { fetchClient } from "@/lib/http-client";
import type { ContactDetail } from "../types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "";

export function useContactDetailQuery(contactId: string | null) {
  return useQuery<ContactDetail>({
    queryKey: ["crm", "contact-detail", contactId],
    queryFn: async () => {
      const res = await fetchClient(`${API_URL}/api/v1/contacts/${contactId}`);
      if (!res.ok) throw new Error(`Failed to load contact ${contactId}: ${res.status}`);
      return res.json();
    },
    enabled: !!contactId,
    staleTime: 60_000,
  });
}
```

### 3.3 `use-filter-schema-query.ts`

```typescript
// metadata para FE dynamic filter UI (lite consume subset hoy; PI-3 expand)
import { useQuery } from "@tanstack/react-query";
import { fetchClient } from "@/lib/http-client";

export interface FilterFieldMeta {
  name: string;
  type: "enum_list" | "int_range" | "bool" | "datetime" | "string";
  enum_values: string[] | null;
  description: string | null;
}

export interface FilterSchemaResponse {
  version: string;
  fields: FilterFieldMeta[];
}

export function useFilterSchemaQuery() {
  return useQuery<FilterSchemaResponse>({
    queryKey: ["crm", "contacts", "filter-schema"],
    queryFn: async () => {
      const res = await fetchClient(`${process.env.NEXT_PUBLIC_API_URL ?? ""}/api/v1/contacts/_filter-schema`);
      if (!res.ok) throw new Error(`Failed to load filter schema: ${res.status}`);
      return res.json();
    },
    staleTime: Infinity, // metadata estable
  });
}
```

## § 4 Components — interfaces & responsabilities

### 4.1 `components/shared/data-table/DataTable.tsx`

```typescript
import type { ColumnDef, Row } from "@tanstack/react-table";

export interface DataTableProps<TData> {
  data: TData[];
  columns: ColumnDef<TData>[];
  totalCount: number;
  limit: number;
  offset: number;
  onPageChange: (newOffset: number) => void;
  onRowClick?: (row: TData) => void;
  selectedIds?: string[];
  onSelectionChange?: (ids: string[]) => void;
  getRowId: (row: TData) => string;
  isLoading?: boolean;
  emptyMessage?: string;
  className?: string;
}

/** Wrapper TanStack + Shadcn Table. NO contiene business logic — 100% genérico. */
export function DataTable<TData>(props: DataTableProps<TData>): React.ReactElement;
```

Internamente: usa `useReactTable` con `getCoreRowModel`, sorting state local, selection state lifted (controlled).

### 4.2 `features/crm-hub/components/ContactFiltersPanel.tsx`

Props:
```typescript
interface ContactFiltersPanelProps {
  filters: ContactFilterParams;
  onChange: (filters: ContactFilterParams) => void;
  className?: string;
}
```

Subset filters lite (S4):
- Lifecycle stage (multi-select Shadcn Command)
- Score range (Shadcn Slider 0-100 dual)
- Has Telegram ID (Shadcn Checkbox)
- Has Email (Checkbox)
- Has Phone (Checkbox)
- Is inactive (Checkbox)
- Has campaign engagement (Checkbox tri-state: any/yes/no)
- Country select (Shadcn Command multi-select desde lista hardcoded LATAM: AR, MX, CO, PE, CL, EC, BO, UY, PY, VE)

Resto filters (created/updated dates, source, instagram_id, tiktok_id, whatsapp_id) → **PI-3 UI expansion**. Schema TS los soporta; UI lite NO los expone.

Layout: vertical stack en sidebar 280px wide, sticky, scrollable interno.

### 4.3 `features/crm-hub/components/ContactDetailContent.tsx`

```typescript
interface ContactDetailContentProps {
  detail: ContactDetail | null;
  isLoading?: boolean;
  className?: string;
}
```

**Aislado**: NO depende de Sheet/Drawer/Dialog. Solo recibe data y renderiza. Drawer-host (PR-11) y future page-host (PI-3) lo importan igual. Arch test enforces.

Sections:
- Header: full_name + lifecycle_stage chip + score_badge + temperature
- Identities list (`IdentityList`)
- Contact channels: telegram_id, whatsapp_id, etc. (mostrar solo presentes)
- Scoring panel: lead_score, fit_score, intent_score, lifetime_value
- Activity: last_activity_at, first_conversion_at, lead_source
- Traits + computed_traits (JSON expanded → key-value list)
- Conversation summary (text)

### 4.4 `features/crm-hub/components/IdentityList.tsx`

```typescript
interface IdentityListProps {
  identities: ContactIdentity[];
}
```

Render lista vertical: `[icon-by-type] {value} {is_primary ? "★" : ""} {verification_status}`.

### 4.5 `features/crm-hub/components/ScoreBadge.tsx`

```typescript
interface ScoreBadgeProps {
  score: number; // 0-100
  className?: string;
}
```

Pattern PR-8 `CampaignTag.tsx` — Shadcn Badge variant per range:
- 0-39 → `variant="secondary"` gray
- 40-69 → `variant="default"` warm
- 70-100 → `variant="destructive"` (color = "hot lead" — Tailwind tokens; reaprovecha existing variant naming)

### 4.6 `features/crm-hub/components/LifecycleStageChip.tsx`

```typescript
interface LifecycleStageChipProps {
  stage: LifecycleStage;
  className?: string;
}
```

Map per stage (8 stages) → Tailwind tokens. Spanish neutro labels:
- subscriber → "Suscriptor"
- lead → "Lead"
- mql → "MQL"
- sql → "SQL"
- opportunity → "Oportunidad"
- customer → "Cliente"
- evangelist → "Evangelista"
- churned → "Churn"

### 4.7 `features/crm-hub/components/SelectedContactsBar.tsx`

```typescript
interface SelectedContactsBarProps {
  selectedIds: string[];
  actions: SelectedContactsBarAction[];   // slot pattern PI-3
  onClearSelection: () => void;
}
```

Sticky bottom bar. Visible cuando `selectedIds.length > 0`. Renders:
- "{N} contactos seleccionados"
- Cada action button (PR-11 ship 0 actions; PR-12 inyecta "Crear segmento"; PI-3 más)
- "Limpiar selección" button

**Slot pattern**: `actions` prop array → arch test enforces.

### 4.8 `features/crm-hub/components/ContactsPageClient.tsx`

```typescript
"use client";

interface ContactsPageClientProps {
  // initial state hydration desde server search params (SSR-friendly)
  initialFilters: ContactFilterParams;
  initialLimit: number;
  initialOffset: number;
}
```

Layout responsive:
- xl (≥1280px): grid `[280px filters | flex 1 table | 480px drawer-overlay]`
- lg (≥1024px): grid `[240px filters | flex 1 table]`, drawer = Sheet overlay
- md+ (<1024px): tabs "Filtros / Tabla", drawer = Sheet overlay
- mobile: tabs, drawer = full-screen Sheet

State:
- `filters` (URL state via `useSearchParams` + `router.replace` debounced 300ms)
- `selectedIds` (local React state)
- `selectedContactId` (drawer open trigger; URL searchParam `?contact={id}`)
- `pagination.{limit,offset}` (URL state)

Search bar top: input con debounce 300ms → updates `filters.q`.

## § 5 Page — Server Component thin

```typescript
// frontend/src/app/(main)/[tenantId]/(dashboard)/sales/contactos/page.tsx
import { ContactsPageClient } from "@/features/crm-hub/components/ContactsPageClient";
import type { ContactFilterParams } from "@/features/crm-hub/types";

interface PageProps {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}

export default async function SalesContactosPage({ searchParams }: PageProps) {
  const params = await searchParams;
  const initialFilters = parseFiltersFromSearchParams(params);
  const initialLimit = clampInt(params.limit, 1, 100, 50);
  const initialOffset = clampInt(params.offset, 0, Number.MAX_SAFE_INTEGER, 0);

  return (
    <div className="flex flex-col h-full">
      <header className="px-6 py-4 border-b">
        <h2 className="text-2xl font-bold">Contactos</h2>
        <p className="text-sm text-muted-foreground">
          Tu base completa. Filtra, busca y selecciona para crear segmentos o lanzar campañas.
        </p>
      </header>
      <ContactsPageClient
        initialFilters={initialFilters}
        initialLimit={initialLimit}
        initialOffset={initialOffset}
      />
    </div>
  );
}
```

`parseFiltersFromSearchParams` lives en `features/crm-hub/utils/url-state.ts`.

## § 6 Arch tests forward-compat (4)

### 6.1 `test_contact_detail_content_isolated.test.ts`

```typescript
// frontend/src/__tests__/architecture/test_contact_detail_content_isolated.test.ts
import { test, expect } from "vitest";
import * as fs from "node:fs";
import * as path from "node:path";

test("ContactDetailContent does NOT import Sheet/Drawer/Dialog (drawer-host agnostic)", () => {
  const filePath = path.resolve(__dirname, "../../features/crm-hub/components/ContactDetailContent.tsx");
  const source = fs.readFileSync(filePath, "utf-8");
  expect(source).not.toMatch(/from\s+["']@\/components\/ui\/sheet["']/);
  expect(source).not.toMatch(/from\s+["']@\/components\/ui\/dialog["']/);
});
```

### 6.2 `test_data_table_in_components_shared.test.ts`

```typescript
test("DataTable lives in components/shared/, not in features/", () => {
  const sharedPath = path.resolve(__dirname, "../../components/shared/data-table/DataTable.tsx");
  expect(fs.existsSync(sharedPath)).toBe(true);

  // ensure NOT in features
  const featuresPath = path.resolve(__dirname, "../../features/crm-hub/components/DataTable.tsx");
  expect(fs.existsSync(featuresPath)).toBe(false);
});
```

### 6.3 `test_filter_params_subset.test.ts`

```typescript
import { CONTACT_FILTER_FIELDS, contactFilterParamsSchema } from "@/features/crm-hub/types";

const CANONICAL_PYDANTIC_FIELDS = [
  "lifecycle_stage_in", "score_min", "score_max",
  "source_in",
  "has_email", "has_phone", "has_telegram_id", "has_whatsapp_id",
  "has_instagram_id", "has_tiktok_id",
  "created_after", "created_before", "last_activity_after", "last_activity_before",
  "is_inactive",
  "has_campaign_engagement",
  "country_in",
  "q",
] as const;

test("CONTACT_FILTER_FIELDS mirror Pydantic ContactFilterParams CANONICAL_FILTER_FIELDS", () => {
  expect(new Set(CONTACT_FILTER_FIELDS)).toEqual(new Set(CANONICAL_PYDANTIC_FIELDS));
});

test("contactFilterParamsSchema includes all canonical keys", () => {
  const schemaKeys = Object.keys(contactFilterParamsSchema.shape);
  expect(new Set(schemaKeys)).toEqual(new Set(CANONICAL_PYDANTIC_FIELDS));
});
```

### 6.4 `test_selected_contacts_bar_slot_pattern.test.ts`

```typescript
import { SelectedContactsBar } from "@/features/crm-hub/components/SelectedContactsBar";

test("SelectedContactsBar accepts actions slot prop (PI-3 expansion)", () => {
  // Type-level test: the prop signature MUST be `actions: SelectedContactsBarAction[]`
  // Arch fitness via TS structural typing — if removed, tsc fails.
  type Props = React.ComponentProps<typeof SelectedContactsBar>;
  const sample: Props = {
    selectedIds: [],
    actions: [],
    onClearSelection: () => {},
  };
  expect(sample.actions).toBeDefined();
});
```

## § 7 E2E test (Playwright)

`frontend/e2e/specs/regression/sales/contactos.spec.ts` — pattern siguiendo PR-9 (mock fixture o real API + seed).

Cases:
1. Smoke nav → table renders with seed data
2. Filter `lifecycle_stage_in=mql` → URL updates, results filter
3. Click row → drawer opens with detail
4. Search `q=juan` → debounced URL update, results filtered
5. Check 2 rows → SelectedContactsBar shows count="2 contactos seleccionados"
6. Click "Limpiar selección" → bar disappears

Si infra gap (BE no levantado en test env) → `test.skip` con `// TODO PI-1 closure: real API setup` documented (heredando pattern PR-9).

## § 8 Vitest unit tests (componentes + hooks)

Listados en `PR.md § Tests requeridos`. Strict para:
- Cada component tiene test render + interaction
- Hook tests con `QueryClientProvider` wrapper
- Mock `fetchClient` con `vi.mock`

## § 9 Quality gates expectations

- `npx tsc --noEmit` 0 errors
- `npx eslint src/components/shared/data-table src/features/crm-hub src/__tests__/architecture src/app/\(main\)/\[tenantId\]/\(dashboard\)/sales/contactos` 0 errors
- `npx vitest run src/components/shared/data-table src/features/crm-hub src/__tests__/architecture` verde
- `npx playwright test --project=smoke regression/sales/contactos.spec.ts` verde (o test.skip documented)
- jscpd no >5% duplication
- knip no unused exports en feature
- madge no circular deps

## § 10 Spanish neutro LATAM

Todas las UI strings:
- Labels (filters, table headers, drawer sections, buttons)
- Empty states ("No hay contactos", "Selecciona filtros para ver más")
- Toast messages
- Aria labels accesibilidad
- Tooltips

NO voseo (regla `spanish-text.md` aplica — sales_agent excepción no aplica aquí).

## § 11 Tailwind tokens — NO hardcoded colors

- Lifecycle chips: usar `bg-blue-100 text-blue-900` style + Shadcn Badge variants. NO `bg-[#1a2b3c]`.
- ScoreBadge: variant per range usando design tokens.
- DataTable selection highlight: `bg-accent` (Shadcn token).

## § 12 FSD-Lite boundaries

- `components/shared/data-table/` consume solo `components/ui/*` + `lib/utils` + `@tanstack/react-table`
- `features/crm-hub/` consume `components/shared/*` + `components/ui/*` + `lib/*` + own subdirs
- App page `app/.../sales/contactos/page.tsx` consume `features/crm-hub` (solo)
- ESLint `boundaries/dependencies` enforces

## § 13 Open questions for PM

**Ninguna.** Decisiones cerradas:

| Decisión | Resolución |
|---|---|
| TanStack Table vs custom | TanStack headless (1000 clientes ready) |
| Drawer vs page detail | Drawer S4, page PI-3, ContactDetailContent shared |
| URL vs Zustand state | URL (deep-link, browser-back) |
| SelectedContactsBar API | `actions: ActionDef[]` slot prop |
| Search debounce | 300ms |
| Filter URL encoding | comma-separated lists, compact |
| Filters lite subset | 8 lite (lifecycle, score range, has_* identifiers, is_inactive, has_campaign_engagement, country) |

---

<!-- @pm: CONTRACT.md ready. Surface mapping: frontend → nicolify-frontend (Sonnet) + nicolify-frontend-auditor (Opus). EXTEND-vs-NEW: NEW DataTable in components/shared/, NEW features/crm-hub/, NEW arch tests. ADD dep @tanstack/react-table. Próximo paso: ejecutar prompts/02-builder-start.md cuando PR-10 BE merge. -->
