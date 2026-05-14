---
story_id: luana-vitalia-bootstrap
surface: FE
sub_architect: architect-fe
arch_version: 1
last_modified: 2026-05-13
links:
  spec: "01-spec.md"
  agentic_design: "02-design-agentic.md"
  consolidated_arch: "03-arch.md"
  story_yaml: "../00-story.md"
  story_10_precedent: "../../../../archive/2026/stories/luana-nicolify-migration/"
  rules:
    - ".claude/rules/frontend-fsd.md"
    - ".claude/rules/frontend-quality.md"
    - ".claude/rules/spanish-text.md"
    - ".claude/rules/tenant-isolation.md"
    - ".claude/rules/form-runtime-array.md"
    - ".claude/rules/e2e-testing.md"
    - ".claude/rules/anti-duplication.md"
---

# 03-arch-fe.md — Story 11 vitalia frontend surface

> Owner: `architect-fe` skill. Documento técnico capa FE.

---

## § 1. Decisión arquitectónica clave

**App Next.js 16 nueva en `luana-platform/vitalia/frontend/`** consumiendo `@luana/ui` (16 Shadcn primitives) + `@luana/shared` (8 shared components). FSD-Lite estricto: `app/` thin routes Server Components default + `features/vitalia/` para business logic + `widget/` separate bundle iframe embeddable. 7 NEW vitalia-specific components (justificación inline anti-duplication). 9 routes onboarding/brand-studio/offers/bookings/treatments/patients/appointments/compliance/widget. React Query data fetch + RHF+Zod forms + Tailwind tokens + `cn()` utility. NO `any` (`unknown` + type guards). NO default exports (excepto Next.js pages).

**Tradeoff aceptado:** Story 11 NO comparte routes con Nicolify — vitalia es app FE independent (workspace member `@luana/vitalia` separate Next.js build/deploy). Esto duplica `app/` boilerplate (layout / sidebar / auth wrapper) pero garantiza brand isolation per Chris framework "cada marca su propio deploy".

---

## § 2. Pre-flight anti-duplication grep

Per `.claude/rules/anti-duplication.md`:
- `@luana/ui/*` SSoT for Shadcn primitives → REUSE 16 components (zero new).
- `@luana/shared/*` SSoT for cross-brand components → REUSE 8 components.
- 7 NEW vitalia-specific components in `vitalia/frontend/src/features/vitalia/components/` — all JUSTIFIED inline spec § 6.3 (medical-vertical specific, no generic equivalent in core).

---

## § 3. Routes (Next.js 16 App Router)

### 3.1 Routes inventory

```
luana-platform/vitalia/frontend/src/app/
├── layout.tsx                            # Root layout (ClerkProvider + QueryProvider + Toaster)
├── page.tsx                              # Landing page (public)
├── (auth)/
│   ├── sign-in/page.tsx                  # Clerk sign-in
│   └── sign-up/page.tsx                  # Clerk sign-up
├── onboarding/
│   ├── layout.tsx                        # Wizard layout with progress bar
│   ├── step-1/page.tsx                   # Clinic profile
│   ├── step-2/page.tsx                   # Plan tier selection
│   └── step-3/page.tsx                   # First offer wizard launch
├── (dashboard)/
│   ├── layout.tsx                        # Sidebar + header (clinic_owner context)
│   ├── page.tsx                          # Dashboard home
│   ├── brand-studio/
│   │   ├── page.tsx                      # Studio with section nav
│   │   └── [section]/page.tsx            # Dynamic section editor (identity/contact/team/testimonials)
│   ├── offers/
│   │   ├── page.tsx                      # Offer list
│   │   ├── new/page.tsx                  # New offer wizard (medical_services preset)
│   │   └── [id]/page.tsx                 # Offer detail
│   ├── bookings/
│   │   ├── page.tsx                      # Bookings calendar admin
│   │   └── [id]/page.tsx                 # Booking detail
│   ├── treatments/
│   │   ├── page.tsx                      # Treatment list
│   │   ├── [id]/page.tsx                 # Treatment detail
│   │   └── [id]/followup/page.tsx        # Treatment followup dashboard
│   ├── patients/
│   │   ├── page.tsx                      # Patient list (CDP medical-flavor)
│   │   └── [id]/page.tsx                 # Patient detail
│   ├── appointments/
│   │   └── page.tsx                      # Calendar consume @luana/core/scheduling
│   └── medical-compliance/
│       └── page.tsx                      # HIPAA-lite audit log admin
├── public/
│   └── [clinic-slug]/                    # Canonical booking page per clinic (Q5=B canonical)
│       ├── page.tsx                      # Landing page tenant-branded
│       └── booking/page.tsx              # Public booking widget canonical URL
└── api/                                  # Next.js API routes for OAuth callbacks etc (no business logic)
```

### 3.2 Routes summary

| Path | Type | Component | Auth |
|---|---|---|---|
| `/` | Server | `LandingPage` | Public |
| `/sign-in`, `/sign-up` | Server | Clerk components | Public |
| `/onboarding/step-1` | Server + Client | `Step1Client` | Clerk JWT |
| `/onboarding/step-2` | Server + Client | `Step2Client` | Clerk JWT |
| `/onboarding/step-3` | Server + Client | `Step3Client` | Clerk JWT |
| `/brand-studio` | Server | `BrandStudioPage` | Clerk JWT |
| `/brand-studio/[section]` | Server + Client | `BrandStudioSectionClient` | Clerk JWT |
| `/offers` | Server | `OffersListPage` | Clerk JWT |
| `/offers/new` | Server + Client | `OfferWizardClient` | Clerk JWT |
| `/offers/[id]` | Server | `OfferDetailPage` | Clerk JWT |
| `/bookings` | Server | `BookingsAdminPage` | Clerk JWT |
| `/bookings/[id]` | Server | `BookingDetailPage` | Clerk JWT |
| `/treatments` | Server | `TreatmentsListPage` | Clerk JWT |
| `/treatments/[id]` | Server | `TreatmentDetailPage` | Clerk JWT |
| `/treatments/[id]/followup` | Server + Client | `TreatmentFollowupClient` | Clerk JWT |
| `/patients` | Server | `PatientsListPage` | Clerk JWT |
| `/patients/[id]` | Server | `PatientDetailPage` | Clerk JWT |
| `/appointments` | Server + Client | `AppointmentsCalendarClient` | Clerk JWT |
| `/medical-compliance` | Server + Client | `CompliancePageClient` | Clerk JWT (admin role) |
| `/public/[clinic-slug]` | Server | `PublicClinicLanding` | Public (no auth) |
| `/public/[clinic-slug]/booking` | Server + Client | `PublicBookingWidget` | Public (signed patient token) |

### 3.3 Server-first boundaries

Per `.claude/rules/frontend-fsd.md`:
- **Server Components default** for data fetching + initial render.
- **`"use client"` only when:** interactive forms (RHF state), useState/useEffect needed, event handlers, Clerk hooks, React Query hooks.
- Pattern per Tessl `nextjs-app-router-modularization`: `page.tsx` Server + `*Client.tsx` Client.

Example:
```tsx
// app/(dashboard)/brand-studio/[section]/page.tsx (Server)
import { BrandStudioSectionClient } from "@/features/vitalia/components/brand-studio-section-client";

export default async function BrandStudioSectionPage({ params }: { params: { section: string } }) {
  // Server-side initial fetch
  return <BrandStudioSectionClient section={params.section} />;
}

// features/vitalia/components/brand-studio-section-client.tsx (Client)
"use client";
import { useBrandStudioSection } from "@/features/vitalia/hooks/use-brand-studio-section";
// ...
```

---

## § 4. Features (FSD-Lite)

### 4.1 Feature layout

```
luana-platform/vitalia/frontend/src/features/vitalia/
├── api/
│   ├── use-clinic-profile-create.ts       # POST onboarding/clinic-profile
│   ├── use-plan-tiers.ts                  # GET onboarding/plans
│   ├── use-subscribe.ts                   # POST onboarding/subscribe
│   ├── use-brand-studio-sections.ts       # GET brand-studio/sections
│   ├── use-brand-studio-section-patch.ts  # PATCH brand-studio/sections/{id}
│   ├── use-offer-preset.ts                # GET offers/presets/medical_services_v1
│   ├── use-offer-create.ts                # POST offers
│   ├── use-offer-list.ts                  # GET offers?status=published
│   ├── use-available-slots.ts             # GET bookings/available-slots
│   ├── use-booking-create.ts              # POST bookings
│   ├── use-booking-cancel.ts              # POST bookings/{id}/cancel
│   ├── use-booking-reschedule.ts          # POST bookings/{id}/reschedule
│   ├── use-treatment-list.ts              # GET treatments
│   ├── use-treatment-detail.ts            # GET treatments/{id}
│   ├── use-treatment-followup.ts          # GET treatments/{id}/followup
│   ├── use-treatment-manual-handoff.ts    # POST treatments/{id}/manual-handoff
│   ├── use-patient-list.ts                # GET patients
│   ├── use-patient-detail.ts              # GET patients/{id}
│   ├── use-patient-upload-medical-pdf.ts  # POST patients/{id}/upload-medical-pdf
│   ├── use-compliance-events.ts           # GET medical-compliance/events
│   └── use-compliance-export-csv.ts       # GET medical-compliance/export-csv
├── components/
│   ├── clinic-type-picker.tsx              # NEW vitalia-specific (spec § 6.3)
│   ├── medical-services-offer-wizard-steps.tsx  # NEW
│   ├── treatment-timeline.tsx              # NEW
│   ├── consent-signature-modal.tsx         # NEW
│   ├── compliance-stats-cards.tsx          # NEW
│   ├── doctor-avatar-picker.tsx            # NEW
│   ├── medical-disclaimer-banner.tsx       # NEW
│   ├── brand-studio-section-client.tsx
│   ├── onboarding-step-1-client.tsx
│   ├── onboarding-step-2-client.tsx
│   ├── onboarding-step-3-client.tsx
│   ├── offer-wizard-client.tsx
│   ├── bookings-admin-calendar.tsx
│   ├── booking-detail-card.tsx
│   ├── treatment-followup-dashboard-client.tsx
│   ├── treatment-list-table.tsx
│   ├── patient-list-table.tsx
│   ├── patient-detail-panel.tsx
│   ├── patient-medical-pdf-upload.tsx
│   ├── appointments-calendar-client.tsx
│   ├── compliance-page-client.tsx
│   ├── compliance-event-row.tsx
│   ├── public-clinic-landing.tsx
│   └── public-booking-widget.tsx
├── hooks/
│   ├── use-flow-context.ts                 # multi-step wizard state
│   ├── use-clinic-type.ts                  # derived state from /onboarding step 1
│   └── use-tenant-clinic.ts                # tenant_profile.clinic_type accessor
├── schemas/
│   ├── clinic-profile-schema.ts            # Zod for /onboarding step 1
│   ├── plan-tier-schema.ts
│   ├── offer-wizard-schema.ts              # Zod offer creation 5-step
│   ├── booking-create-schema.ts
│   ├── consent-sign-schema.ts
│   ├── manual-handoff-schema.ts
│   └── compliance-filter-schema.ts
├── types/
│   ├── vitalia.types.ts                    # TypeScript types mirror Pydantic Response DTOs
│   ├── booking.types.ts
│   ├── treatment.types.ts
│   ├── consent.types.ts
│   ├── compliance.types.ts
│   └── plan-tier.types.ts
├── utils/
│   ├── format-medical-disclaimer.ts        # disclaimer text composer per channel
│   ├── parse-fdi-notation.ts               # dental chart FDI 11-48 parser
│   └── calc-deposit-amount.ts              # deposit_percent → amount calc
└── config/
    └── vitalia.config.ts                   # Feature flags consumed from BrandConfig
```

### 4.2 Boundary matrix per FSD-Lite

Per `.claude/rules/frontend-fsd.md`:

| From \ To | features/vitalia | features:vitalia (own) | @luana/shared | @luana/ui | lib | util | hooks |
|---|---|---|---|---|---|---|---|
| app | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ |
| features/vitalia | own only | ✅ | ✅ | — | ✅ | ✅ | — |
| features:vitalia (own) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| @luana/shared | — | — | ✅ | ✅ | ✅ | ✅ | — |
| lib | — | — | — | — | — | ✅ | — |

Cross-feature imports forbidden default. NO `from "@/features/nicolify/..."` o `from "@/features/comunify/..."` — brand isolation per path.

---

## § 5. Components inventory

### 5.1 Reuse `@luana/ui` Shadcn primitives (16 components, zero new)

Per spec § 6.1 — all reused via workspace import `from "@luana/ui/{component}"`:

`Button`, `Input`, `Select`, `RadioGroup`, `Checkbox`, `Dialog`, `Toast`, `Form`, `Progress`, `Skeleton`, `Avatar`, `Badge`, `Card`, `Sheet`, `Tabs`, `Table`.

### 5.2 Reuse `@luana/shared` cross-brand components (8 components)

Per spec § 6.2:

| Component | Path | Uso Story 11 |
|---|---|---|
| `DataTable` | `@luana/shared/data-table` | Audit log table, treatments list, patients list |
| `FormWizard` | `@luana/shared/form-wizard` | Onboarding 3-step, offer 5-step wizards |
| `EmptyState` | `@luana/shared/empty-state` | All empty UI states (empty treatments, empty offers, etc) |
| `ErrorBoundary` | `@luana/shared/error-boundary` | All routes (root layout wrap) |
| `TenantSwitcher` | `@luana/shared/tenant-switcher` | Header (multi-clinic future) |
| `SidebarLayout` | `@luana/shared/sidebar-layout` | App shell (dashboard layout) |
| `PageHeader` | `@luana/shared/page-header` | Breadcrumbs + page action CTAs |
| `FormRuntime` | `@luana/shared/form-runtime` | Brand Studio sections (autosave per `form-runtime-array.md`) |

### 5.3 NEW vitalia-specific components (7 — justification anti-duplication)

#### 5.3.1 `ClinicTypePicker`

```tsx
// features/vitalia/components/clinic-type-picker.tsx
"use client";
import { RadioGroup, RadioGroupItem } from "@luana/ui/radio-group";
import { Label } from "@luana/ui/label";
import { ToothIcon, BrainIcon, HeartPulseIcon, SparkleIcon } from "lucide-react";

type ClinicType = "dental" | "psychology" | "psychiatry" | "wellness";

interface ClinicTypePickerProps {
  value: ClinicType | null;
  onChange: (value: ClinicType) => void;
  disabled?: boolean;
}

export function ClinicTypePicker({ value, onChange, disabled }: ClinicTypePickerProps) {
  return (
    <RadioGroup value={value ?? ""} onValueChange={(v) => onChange(v as ClinicType)} disabled={disabled}>
      <RadioGroupItem value="dental" aria-label="Dental">
        <ToothIcon /> Dental
        <span className="hint">Implantes, ortodoncia, limpiezas</span>
      </RadioGroupItem>
      <RadioGroupItem value="psychology" aria-label="Psicología">
        <BrainIcon /> Psicología
        <span className="hint">Terapia individual, pareja, infanto-juvenil</span>
      </RadioGroupItem>
      <RadioGroupItem value="psychiatry" aria-label="Psiquiatría">
        <HeartPulseIcon /> Psiquiatría
        <span className="hint">Tratamiento médico, prescripción</span>
      </RadioGroupItem>
      <RadioGroupItem value="wellness" aria-label="Wellness">
        <SparkleIcon /> Wellness
        <span className="hint">Kinesiología, nutrición, otro</span>
      </RadioGroupItem>
    </RadioGroup>
  );
}
```

**Justification:** vertical-medical clinic type selection with iconography + suitability hints. No generic equivalent in `@luana/ui` (other brands have own picker — Comunify community-type, Lupulo grow-type).

#### 5.3.2 `MedicalServicesOfferWizardSteps`

5-step wizard component composing FormWizard from `@luana/shared` with medical_services-preset-specific step contents:
- Step 1: Tipo de servicio (offer category)
- Step 2: Para qué paciente (target description)
- Step 3: Precio (currency + base_price + requires_prepay + deposit_percent)
- Step 4: Consentimiento (requires_informed_consent + consent_template_slug)
- Step 5: Duración + profesional (duration_min + doctor_id)

**Justification:** preset `medical_services_v1` specific fields (prepay_policy + consent_template + doctor_assigned + duration). Luana core offer wizard is preset-agnostic.

#### 5.3.3 `TreatmentTimeline`

Visual horizontal timeline for D0/D5/D14/D90 milestones + adherence score badge. Renders milestones from `treatment.current_step` enum. Used in `/treatments/[id]/followup` dashboard.

**Justification:** Medical-specific timeline pattern. Generic timeline (e.g., `@luana/shared/event-timeline`) insufficient — needs medical milestone names + adherence overlay.

#### 5.3.4 `ConsentSignatureModal`

Modal for HIPAA-lite consent capture:
- Scrollable terms markdown
- `consent.scrolled_to_end` flag (validation)
- "Acepto" checkbox
- Signature pad OR typed name input
- Patient IP + user_agent captured server-side via signature endpoint

**Justification:** HIPAA-lite specific (signature audit trail + scroll-to-end validation + dual input mode). Security-critical, vertical-specific.

#### 5.3.5 `ComplianceStatsCards`

Stats card grid for `/medical-compliance` page: total_events, critical, blocked + breakdown by event_type bar chart.

**Justification:** HIPAA-lite metrics aggregation, medical-vertical specific.

#### 5.3.6 `DoctorAvatarPicker`

Doctor selection grid for offer wizard step 5 + booking widget. Displays doctor avatar + name + specialties tooltip + availability badge.

**Justification:** Medical-vertical specific (specialties tooltip + availability indicator).

#### 5.3.7 `MedicalDisclaimerBanner`

Contextual banner inserted at top of pages where sensitive medical content appears (treatment detail, offer detail). Configurable copy per context.

**Justification:** HIPAA-lite reminder, vertical-specific copy ("Esto no reemplaza consulta médica profesional").

---

## § 6. React Query hooks (data flow)

### 6.1 Query keys (spec § 7.2)

```typescript
// features/vitalia/api/query-keys.ts
export const vitaliaQueryKeys = {
  onboarding: {
    plans: () => ["vitalia", "onboarding", "plans"] as const,
  },
  brandStudio: {
    sections: () => ["vitalia", "brand-studio", "sections"] as const,
    section: (sectionId: string) => ["vitalia", "brand-studio", "sections", sectionId] as const,
  },
  offers: {
    list: (filters?: object) => ["vitalia", "offers", "list", filters] as const,
    detail: (id: string) => ["vitalia", "offers", "detail", id] as const,
    preset: (slug: string) => ["vitalia", "offers", "presets", slug] as const,
  },
  bookings: {
    slots: (filters: { doctor_id: string; offer_id?: string }) => ["vitalia", "bookings", "slots", filters] as const,
    detail: (id: string) => ["vitalia", "bookings", "detail", id] as const,
  },
  treatments: {
    list: () => ["vitalia", "treatments", "list"] as const,
    detail: (id: string) => ["vitalia", "treatments", "detail", id] as const,
    followup: (id: string) => ["vitalia", "treatments", "followup", id] as const,
  },
  patients: {
    list: (filters?: object) => ["vitalia", "patients", "list", filters] as const,
    detail: (id: string) => ["vitalia", "patients", "detail", id] as const,
  },
  compliance: {
    events: (filters: object) => ["vitalia", "compliance", "events", filters] as const,
  },
} as const;
```

### 6.2 Mutation invalidations (spec § 7.3)

```typescript
// features/vitalia/api/use-offer-create.ts
export function useOfferCreate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: OfferCreateRequest) =>
      fetchClient.post<OfferCreateResponse>("/api/v1/offers", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: vitaliaQueryKeys.offers.list() });
    },
  });
}

// features/vitalia/api/use-booking-create.ts
export function useBookingCreate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: BookingCreateRequest) =>
      fetchClient.post<BookingCreateResponse>("/api/v1/vitalia/bookings", data),
    onSuccess: (_, vars) => {
      queryClient.invalidateQueries({
        queryKey: vitaliaQueryKeys.bookings.slots({ doctor_id: vars.doctor_id }),
      });
    },
  });
}

// features/vitalia/api/use-treatment-manual-handoff.ts
export function useTreatmentManualHandoff(treatmentId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () =>
      fetchClient.post<ManualHandoffResponse>(`/api/v1/vitalia/treatments/${treatmentId}/manual-handoff`),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: vitaliaQueryKeys.treatments.detail(treatmentId),
      });
    },
  });
}
```

### 6.3 `fetchClient` auto-inject `X-Tenant-ID`

Per `.claude/rules/tenant-isolation.md`:
```typescript
// @luana/shared/lib/fetch-client.ts (shared base, vitalia consumes)
import { useAuth } from "@clerk/nextjs";

export async function fetchClient<T>(url: string, options?: RequestInit): Promise<T> {
  const { getToken, sessionClaims } = useAuth();
  const token = await getToken();
  const tenantId = sessionClaims?.public_metadata?.active_tenant_id;
  
  const response = await fetch(url, {
    ...options,
    headers: {
      ...options?.headers,
      Authorization: `Bearer ${token}`,
      "X-Tenant-ID": tenantId,  // Auto-injected; middleware authoritative ignores client override
    },
  });
  if (!response.ok) throw new ApiError(response);
  return response.json();
}
```

---

## § 7. Zod schemas (shared validation BE + FE contract)

### 7.1 Pattern (per `tessl__zod`)

```typescript
// features/vitalia/schemas/clinic-profile-schema.ts
import { z } from "zod";

export const clinicProfileSchema = z.object({
  clinic_name: z.string().min(2, "Mínimo 2 caracteres").max(120),
  clinic_type: z.enum(["dental", "psychology", "psychiatry", "wellness"]),
  country: z.enum(["AR", "CL", "MX", "BR", "CO", "PE", "UY", "US"]),
  city: z.string().min(2).max(120),
});

export type ClinicProfileInput = z.infer<typeof clinicProfileSchema>;
```

### 7.2 Schemas inventory

- `clinicProfileSchema` (`onboarding/step-1`)
- `planTierSelectSchema` (`onboarding/step-2`)
- `offerWizardSchemaStep1`, `offerWizardSchemaStep2`, `offerWizardSchemaStep3`, `offerWizardSchemaStep4`, `offerWizardSchemaStep5` (`offers/new`)
- `bookingCreateSchema` (`bookings`)
- `consentSignSchema` (`bookings/{id}/consent-sign`)
- `manualHandoffSchema` (`treatments/{id}/manual-handoff`)
- `complianceFilterSchema` (`medical-compliance`)
- `medicalPdfUploadSchema` (`patients/{id}/upload-medical-pdf`)

---

## § 8. TypeScript types (mirror Pydantic Response DTOs)

### 8.1 Pattern

```typescript
// features/vitalia/types/booking.types.ts
import type { Booking as BookingPyDantic } from "vitalia-api-spec"; // OpenAPI generated

export type BookingStatus = 
  | "pending_payment"
  | "awaiting_consent"
  | "confirmed_deposit"
  | "confirmed_full"
  | "cancelled"
  | "completed";

export interface Booking {
  id: string;
  tenant_id: string;
  offer_id: string;
  doctor_id: string;
  patient_id: string;
  slot_iso: string;  // ISO 8601 UTC
  status: BookingStatus;
  payment_status: string;
  amount_paid: string | null;  // Decimal serialized as string
  amount_pending: string | null;
  currency: string | null;
  deposit_percent: number | null;
  created_at: string;
}
```

### 8.2 OpenAPI types generation

- Backend FastAPI emits OpenAPI spec at `/api/v1/vitalia/openapi.json`.
- Build step `vitalia-api-spec` package generates TS types from OpenAPI via `openapi-typescript`.
- FE imports types from `vitalia-api-spec` workspace package.
- Arch fitness test `test_ts_types_mirror_python_dataclasses.py` (Story 9 cement) verifies.

---

## § 9. Booking widget bundle (iframe embeddable)

### 9.1 Bundle structure

```
luana-platform/vitalia/frontend/widget/
├── src/
│   ├── widget-entry.tsx                    # entry point
│   ├── components/
│   │   ├── BookingWidgetRoot.tsx
│   │   ├── CalendarSlotPicker.tsx
│   │   ├── ConsentStep.tsx                 # Reuses ConsentSignatureModal
│   │   ├── PaymentStep.tsx                 # MP + Stripe iframe redirect
│   │   └── SuccessStep.tsx
│   ├── postmessage-protocol.ts             # iframe resize + payment redirect handling
│   └── styles.css                          # Scoped Tailwind subset
├── vite.config.ts                          # Vite builds UMD bundle
└── dist/                                   # Output: widget.umd.js + widget.css
```

### 9.2 postMessage protocol

```typescript
// vitalia/frontend/widget/src/postmessage-protocol.ts
export type WidgetMessage =
  | { type: "widget:resize"; height: number }
  | { type: "widget:loaded" }
  | { type: "widget:booking-confirmed"; booking_id: string }
  | { type: "widget:payment-redirect"; url: string }
  | { type: "widget:error"; message: string };

// Iframe sends → parent listens
window.parent.postMessage({ type: "widget:resize", height: 800 } satisfies WidgetMessage, "*");
```

### 9.3 Embed snippet (clinic_owner copy-paste)

```html
<!-- vitalia/docs/booking-widget-embed.md ships this -->
<div id="vitalia-booking-widget" data-clinic-slug="{clinic-slug}" data-offer-id="{offer_id}"></div>
<script src="https://cdn.vitalia.health/widget/widget.umd.js"></script>
<link rel="stylesheet" href="https://cdn.vitalia.health/widget/widget.css" />
```

### 9.4 Canonical URL alternative

Same booking flow accessible at `https://landing.vitalia.health/{clinic-slug}/booking?offer_id={id}` (Server Component page route `app/public/[clinic-slug]/booking/page.tsx`). Aurora fixture demoes iframe embed; Sanaré + Mindful demo canonical.

---

## § 10. Manual handoff CTA flow (clinic_owner takes over conversation)

Per spec § 3.5.A + 02-design § 2.1:

### 10.1 UI flow

1. `/treatments/[id]/followup` page shows "Tomar conversación" CTA.
2. Click → `useTreatmentManualHandoff()` mutation → POST `/api/v1/vitalia/treatments/{id}/manual-handoff`.
3. Backend emits `ManualHandoffStartedV1` event → sales_agent silenced for this conversation.
4. UI updates → chat takeover panel visible + "Liberar conversación" CTA.
5. clinic_owner types messages → POST `/api/v1/vitalia/conversations/{id}/messages` (sent as clinic_owner persona).
6. Idle 30min → backend auto-releases → sales_agent resumes with anchor "Retomo donde quedó {clinic_owner_name}" (02-design § 2.1).

### 10.2 Component

```tsx
// features/vitalia/components/treatment-followup-dashboard-client.tsx (excerpt)
{handoff.active ? (
  <ManualHandoffPanel
    treatmentId={treatment.id}
    onRelease={() => releaseHandoffMutation.mutate()}
  />
) : (
  <Button onClick={() => takeoverHandoffMutation.mutate()}>
    Tomar conversación
  </Button>
)}
```

---

## § 11. Tests required

### 11.1 Vitest unit

```
vitalia/frontend/tests/
├── unit/
│   ├── features/vitalia/components/
│   │   ├── clinic-type-picker.test.tsx
│   │   ├── treatment-timeline.test.tsx
│   │   ├── consent-signature-modal.test.tsx
│   │   ├── compliance-stats-cards.test.tsx
│   │   ├── doctor-avatar-picker.test.tsx
│   │   ├── medical-disclaimer-banner.test.tsx
│   │   └── medical-services-offer-wizard-steps.test.tsx
│   ├── features/vitalia/hooks/
│   │   ├── use-flow-context.test.ts
│   │   └── use-tenant-clinic.test.ts
│   ├── features/vitalia/schemas/
│   │   ├── clinic-profile-schema.test.ts
│   │   ├── offer-wizard-schema.test.ts
│   │   └── booking-create-schema.test.ts
│   └── features/vitalia/utils/
│       ├── format-medical-disclaimer.test.ts
│       └── calc-deposit-amount.test.ts
└── integration/
    ├── onboarding-wizard-flow.test.tsx     # 3-step wizard integration
    ├── offer-wizard-flow.test.tsx          # 5-step wizard integration
    └── booking-widget-flow.test.tsx        # widget bundle integration test
```

### 11.2 Playwright E2E (per spec § 13.3 matrix — 18 specs total)

```
vitalia/frontend/e2e/
├── fixtures/
│   ├── aurora-dental-ar.fixture.ts
│   ├── mindful-psych-cl.fixture.ts
│   └── sanare-latam-mx.fixture.ts
├── specs/vitalia/
│   ├── onboarding-dental-aurora.spec.ts
│   ├── onboarding-psych-mindful.spec.ts
│   ├── onboarding-psych-sanare.spec.ts
│   ├── brand-studio-dental.spec.ts
│   ├── brand-studio-psych.spec.ts
│   ├── brand-studio-sanare.spec.ts
│   ├── offer-wizard-implant.spec.ts
│   ├── offer-wizard-individual-session.spec.ts
│   ├── offer-wizard-packages.spec.ts
│   ├── booking-prepaid-sanare.spec.ts
│   ├── booking-deposit-aurora.spec.ts
│   ├── booking-full-prepay-mindful.spec.ts
│   ├── treatment-followup-aurora.spec.ts
│   ├── treatment-followup-mindful.spec.ts
│   ├── treatment-followup-sanare.spec.ts
│   ├── compliance-audit-log.spec.ts
│   ├── cross-tenant-isolation.spec.ts
│   └── consent-flow-implant.spec.ts
└── auth.fixture.ts                          # Clerk testing token per playwright-expert
```

### 11.3 E2E Native WSL (NEVER Docker — playwright-expert SSoT)

```bash
# Preflight obligatorio
cd /home/chris/luana-platform && bash scripts/e2e-preflight.sh

# Run smoke
cd vitalia/frontend && E2E_BASE_URL=http://localhost:3000 npx playwright test --project=smoke
```

---

## § 12. Spanish neutro chrome UI enforcement

Per `.claude/rules/spanish-text.md` R2 + Q1=B ratified spec § 17:

### 12.1 Arch fitness test

```typescript
// vitalia/frontend/src/__tests__/architecture/test-vitalia-ui-strings-no-voseo.test.ts
import { describe, it, expect } from "vitest";
import { readFileSync, readdirSync } from "fs";
import { join } from "path";

const VOSEO_VERBS = [
  /\bvos\b/, /\bsos\b/, /\btenés\b/, /\bquerés\b/, /\bpodés\b/,
  /\bhacés\b/, /\bvenís\b/, /\bdecís\b/, /\bmirá\b/, /\bdejá\b/,
  /\bagregá\b/, /\bconfigurá\b/, /\bguardá\b/, /\bcambiá\b/, /\bprobá\b/,
];

describe("Vitalia chrome UI Spanish neutro (Q1=B ratified)", () => {
  it("NO voseo verbs in src/features/vitalia/ user-facing strings", () => {
    const files = walkSync("src/features/vitalia/");
    for (const file of files) {
      // Skip non-component files
      if (!file.match(/\.(tsx|ts)$/)) continue;
      const content = readFileSync(file, "utf-8");
      // Skip files with magic comment voseo-allowed
      if (content.includes("voseo-allowed")) continue;
      // Check user-facing strings
      const userFacingStrings = extractUserFacingStrings(content);
      for (const str of userFacingStrings) {
        for (const voseoRegex of VOSEO_VERBS) {
          expect(str).not.toMatch(voseoRegex);
        }
      }
    }
  });
});
```

### 12.2 SSoT spec § 8 microcopy (immutable)

All vitalia chrome UI strings sourced from spec § 8.1–§ 8.6 microcopy table. Ticket T-X creates `vitalia/frontend/src/features/vitalia/config/microcopy.ts` mirror.

---

## § 13. Cross-cutting concerns (FE)

| Concern | Pattern |
|---|---|
| Tenant isolation | `fetchClient` auto-injects `X-Tenant-ID` from Clerk session_claims.public_metadata.active_tenant_id. NEVER hardcoded. |
| Master data | `useTenantLocale()` hook returns `{ currency, timezone }`. `formatMoney(amount, currency)` consumes data source currency or fallback. `formatTenantDate*()` for date display. |
| PII | Patient phone/email already masked at BE response. FE displays as-received (no further processing). NO patient PII in localStorage / sessionStorage / URL params. |
| Spanish neutro | Microcopy SSoT spec § 8. Arch fitness gate. Magic comment `// voseo-allowed: ...` honored. |
| Error boundaries | All routes wrapped in `@luana/shared/error-boundary`. Toast on API errors. |
| Loading/empty states | All async data uses Skeleton + EmptyState pattern. NO blank screens. |
| Form runtime autosave | Brand Studio sections only (per `form-runtime-array.md`). Other forms = explicit submit. |
| Accessibility | All inputs aria-label/required/invalid. Focus rings. Color contrast. Screen reader aria-live. Keyboard navigation. Color-blind mode for severity badges. (Per spec § 10.) |
| Responsive | Breakpoints per spec § 9: mobile <768 / tablet 768-1024 / desktop >1024. |

---

## § 14. Risks + mitigations (FE-specific)

| Risk | Severity | Mitigation |
|---|---|---|
| Voseo leak in microcopy | medium | Arch fitness gate + magic comment + microcopy SSoT spec § 8 single source |
| Cross-feature import (Comunify code reaches Vitalia) | medium | FSD-Lite boundary plugin error level + per-brand workspace isolation pattern |
| Booking widget XSS via clinic-slug | high | Server-side render via Next.js Server Component + sanitize patient input + audit log XSS attempts |
| iframe widget origin spoofing | medium | postMessage origin validation + signed patient token + HMAC verify |
| Patient PII in URL params | medium | All patient data via POST body + signed JWT tokens for public booking flow |
| Date timezone confusion (clinic_owner UTC-3 viewing patient UTC-6) | medium | UTC storage + `useTenantLocale()` display + arch fitness gate `test_no_hardcoded_timezone.test.ts` |
| Vitest coverage <20% threshold | medium | Per-ticket coverage gate enforced via validators YAML |
| Playwright E2E flakiness with Clerk auth | medium | playwright-expert SSoT freshness gate + retry + sanity check (auth.fixture) |

---

## § 15. Próximo paso

`architect-fe` returns: `done -> 03-arch-fe.md`. /architect orchestrator consolidates.

done -> docs/product/stories/luana-vitalia-bootstrap/03-arch-fe.md
