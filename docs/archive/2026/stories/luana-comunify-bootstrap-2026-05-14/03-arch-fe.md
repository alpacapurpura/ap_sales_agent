---
story_id: luana-comunify-bootstrap
surface: FE
sub_architect: architect-fe
arch_version: 1
last_modified: 2026-05-14
links:
  spec: "01-spec.md"
  agentic_design: "02-design-agentic.md"
  consolidated_arch: "03-arch.md"
  story_11_fe_precedent: "../../../../archive/2026/stories/luana-vitalia-bootstrap-2026-05-14/03-arch-fe.md"
  rules:
    - ".claude/rules/frontend-fsd.md"
    - ".claude/rules/frontend-quality.md"
    - ".claude/rules/spanish-text.md"
    - ".claude/rules/tenant-isolation.md"
    - ".claude/rules/form-runtime-array.md"
    - ".claude/rules/e2e-testing.md"
    - ".claude/rules/anti-duplication.md"
---

# 03-arch-fe.md — Story 12 comunify frontend surface

> Owner: `architect-fe` skill. Documento técnico capa FE.

---

## § 1. Decisión arquitectónica clave

**App Next.js 16 nueva en `luana-platform/comunify/frontend/`** consumiendo `@luana/ui` (16 Shadcn primitives) + `@luana/shared` (10 shared components — adds `AsyncJobStatus` + `FileUploadZone` over Story 11's 8). FSD-Lite estricto: `app/` thin routes Server Components default + `features/comunify/` para business logic + `widget/` separate bundle iframe embeddable subscription. **11 NEW comunify-specific components** (justificación inline anti-duplication). 13 routes onboarding/brand-studio (10 sections)/offers/ladder/cohorts/community/authority/subscriptions/moderation/public landing per creator-handle. React Query data fetch + RHF+Zod forms + Tailwind tokens + `cn()` utility. NO `any` (`unknown` + type guards). NO default exports (excepto Next.js pages).

**Tradeoff aceptado:** Story 12 NO comparte routes con Nicolify/Vitalia — comunify es app FE independent (workspace member `@luana/comunify` separate Next.js build/deploy). Esto duplica `app/` boilerplate (layout / sidebar / auth wrapper) pero garantiza brand isolation per Chris framework "cada marca su propio deploy".

---

## § 2. Pre-flight anti-duplication grep

Per `.claude/rules/anti-duplication.md`:
- `@luana/ui/*` SSoT for Shadcn primitives → REUSE 16 components (zero new).
- `@luana/shared/*` SSoT for cross-brand components → REUSE 10 components.
- **11 NEW comunify-specific components** in `comunify/frontend/src/features/comunify/components/` — all JUSTIFIED inline spec § 6.3 (creator-economy-vertical-specific, no generic equivalent in core).

---

## § 3. Routes (Next.js 16 App Router)

### 3.1 Routes inventory

```
luana-platform/comunify/frontend/src/app/
├── layout.tsx                            # Root layout (ClerkProvider + QueryProvider + Toaster)
├── page.tsx                              # Landing page (public)
├── (auth)/
│   ├── sign-in/page.tsx                  # Clerk sign-in
│   └── sign-up/page.tsx                  # Clerk sign-up
├── onboarding/
│   ├── layout.tsx                        # Wizard layout with progress bar
│   ├── step-1/page.tsx                   # Creator profile
│   ├── step-2/page.tsx                   # Niche + audience
│   ├── step-3/page.tsx                   # Plan tier
│   └── step-4/page.tsx                   # First offer ladder seed
├── (dashboard)/
│   ├── layout.tsx                        # Sidebar + header (creator context)
│   ├── page.tsx                          # Dashboard home
│   ├── brand-studio/
│   │   ├── page.tsx                      # Studio with section nav (10 sections)
│   │   └── [section]/page.tsx            # Dynamic section editor (incluye /voz voice cloning)
│   ├── offers/
│   │   ├── page.tsx                      # Offer list
│   │   ├── new/page.tsx                  # New offer wizard (coaching_offers preset 5-step)
│   │   └── [id]/page.tsx                 # Offer detail
│   ├── ladder/
│   │   └── page.tsx                      # 4-level ladder visualizer
│   ├── cohorts/
│   │   ├── page.tsx                      # Cohort list
│   │   ├── new/page.tsx                  # Create cohort
│   │   └── [id]/
│   │       ├── page.tsx                  # Cohort detail (Roster | Comunicación | Recursos | Calendario)
│   │       ├── roster/page.tsx
│   │       └── broadcasts/page.tsx
│   ├── community/
│   │   ├── page.tsx                      # Cross-cohort feed
│   │   └── moderation/page.tsx           # Pending moderation inbox
│   ├── authority/
│   │   └── page.tsx                      # Authority vault editor
│   ├── subscriptions/
│   │   ├── page.tsx                      # Subscriptions admin (MRR + active + churn)
│   │   └── [id]/page.tsx                 # Subscription detail
│   ├── voice/                            # Direct route to voice cloning
│   │   └── page.tsx
│   └── community-audit/
│       └── page.tsx                      # Compliance audit log
├── public/
│   └── [creator-handle]/
│       ├── page.tsx                      # Public creator landing
│       └── subscribe/page.tsx            # Subscription canonical URL (Q5=B canonical)
└── api/                                  # Next.js API routes (no business logic)
```

### 3.2 Routes summary

| Path | Type | Component | Auth |
|---|---|---|---|
| `/` | Server | `LandingPage` | Public |
| `/sign-in`, `/sign-up` | Server | Clerk components | Public |
| `/onboarding/step-1..4` | Server + Client | `Step{N}Client` | Clerk JWT |
| `/brand-studio` | Server | `BrandStudioPage` | Clerk JWT |
| `/brand-studio/[section]` | Server + Client | `BrandStudioSectionClient` | Clerk JWT |
| `/offers` | Server | `OffersListPage` | Clerk JWT |
| `/offers/new` | Server + Client | `OfferWizardClient` | Clerk JWT |
| `/offers/[id]` | Server | `OfferDetailPage` | Clerk JWT |
| `/ladder` | Server + Client | `LadderVisualizerClient` | Clerk JWT |
| `/cohorts` | Server | `CohortsListPage` | Clerk JWT |
| `/cohorts/new` | Server + Client | `CreateCohortClient` | Clerk JWT |
| `/cohorts/[id]` | Server + Client | `CohortDetailClient` | Clerk JWT |
| `/community` | Server + Client | `CommunityFeedClient` | Clerk JWT |
| `/community/moderation` | Server + Client | `CommunityModerationClient` | Clerk JWT |
| `/authority` | Server + Client | `AuthorityVaultClient` | Clerk JWT |
| `/subscriptions` | Server + Client | `SubscriptionsAdminClient` | Clerk JWT |
| `/subscriptions/[id]` | Server | `SubscriptionDetailPage` | Clerk JWT |
| `/voice` | Server + Client | `VoiceCloningClient` | Clerk JWT |
| `/community-audit` | Server + Client | `CommunityAuditClient` | Clerk JWT (creator) |
| `/public/[creator-handle]` | Server | `PublicCreatorLanding` | Public |
| `/public/[creator-handle]/subscribe` | Server + Client | `PublicSubscribeWidget` | Public (signed subscriber token) |

### 3.3 Server-first boundaries

Per `.claude/rules/frontend-fsd.md`:
- **Server Components default** for data fetching + initial render.
- **`"use client"` only when:** interactive forms (RHF state), useState/useEffect needed, event handlers, Clerk hooks, React Query hooks.
- Pattern per Tessl `nextjs-app-router-modularization`: `page.tsx` Server + `*Client.tsx` Client.

---

## § 4. Features (FSD-Lite)

### 4.1 Feature layout

```
luana-platform/comunify/frontend/src/features/comunify/
├── api/
│   ├── use-creator-profile-create.ts
│   ├── use-handle-check.ts
│   ├── use-plan-tiers.ts
│   ├── use-subscribe.ts
│   ├── use-brand-studio-sections.ts
│   ├── use-brand-studio-section-patch.ts
│   ├── use-voice-samples-upload.ts
│   ├── use-voice-samples-status.ts
│   ├── use-voice-distillation-kick.ts
│   ├── use-voice-distillation-poll.ts        # polling React Query
│   ├── use-voice-ratify.ts
│   ├── use-authority-vault.ts
│   ├── use-authority-credential-add.ts
│   ├── use-authority-case-study-add.ts
│   ├── use-authority-press-mention-add.ts
│   ├── use-authority-validate-url.ts
│   ├── use-offer-preset.ts                    # GET coaching_offers_v1
│   ├── use-offer-create.ts
│   ├── use-offer-list.ts
│   ├── use-ladder.ts
│   ├── use-ladder-update-connections.ts
│   ├── use-cohort-create.ts
│   ├── use-cohort-list.ts
│   ├── use-cohort-detail.ts
│   ├── use-cohort-roster.ts
│   ├── use-cohort-enroll.ts
│   ├── use-cohort-broadcast-send.ts
│   ├── use-cohort-broadcasts.ts
│   ├── use-community-feed.ts
│   ├── use-community-post-create.ts
│   ├── use-community-moderation-inbox.ts
│   ├── use-community-moderation-action.ts
│   ├── use-subscription-list.ts
│   ├── use-subscription-detail.ts
│   ├── use-subscription-cancel.ts
│   ├── use-subscription-resend-payment-link.ts
│   ├── use-subscription-metrics.ts
│   ├── use-community-audit-events.ts
│   └── use-community-audit-export-csv.ts
├── components/
│   ├── creator-niche-picker.tsx              # NEW comunify-specific (spec § 6.3)
│   ├── voice-samples-uploader.tsx            # NEW
│   ├── voice-distilled-preview.tsx           # NEW
│   ├── ladder-visualizer.tsx                 # NEW
│   ├── authority-vault-editor.tsx            # NEW
│   ├── cohort-roster-table.tsx               # NEW
│   ├── cohort-broadcast-composer.tsx         # NEW
│   ├── community-moderation-card.tsx         # NEW
│   ├── subscription-metrics-cards.tsx        # NEW
│   ├── dunning-active-banner.tsx             # NEW
│   ├── creator-landing-hero.tsx              # NEW
│   ├── brand-studio-section-client.tsx
│   ├── onboarding-step-1-client.tsx
│   ├── onboarding-step-2-client.tsx
│   ├── onboarding-step-3-client.tsx
│   ├── onboarding-step-4-client.tsx
│   ├── offer-wizard-client.tsx
│   ├── cohort-detail-client.tsx
│   ├── community-feed-client.tsx
│   ├── community-moderation-client.tsx
│   ├── subscriptions-admin-client.tsx
│   ├── voice-cloning-client.tsx
│   ├── public-creator-landing.tsx
│   └── public-subscribe-widget.tsx
├── hooks/
│   ├── use-flow-context.ts                   # multi-step wizard state
│   ├── use-creator-niche.ts
│   ├── use-tenant-creator.ts
│   └── use-poll-distillation-job.ts          # custom polling
├── schemas/
│   ├── creator-profile-schema.ts
│   ├── niche-audience-schema.ts
│   ├── plan-tier-schema.ts
│   ├── coaching-offer-wizard-schema.ts       # 5-step
│   ├── cohort-create-schema.ts
│   ├── broadcast-compose-schema.ts
│   ├── community-post-schema.ts
│   ├── moderation-action-schema.ts
│   ├── subscription-cancel-schema.ts
│   ├── voice-samples-upload-schema.ts
│   ├── authority-credential-schema.ts
│   ├── authority-case-study-schema.ts
│   ├── authority-press-mention-schema.ts
│   └── audit-filter-schema.ts
├── types/
│   ├── comunify.types.ts
│   ├── cohort.types.ts
│   ├── community.types.ts
│   ├── subscription.types.ts
│   ├── voice-cloning.types.ts
│   ├── authority-vault.types.ts
│   ├── ladder.types.ts
│   └── plan-tier.types.ts
├── utils/
│   ├── format-engagement-bucket.ts
│   ├── format-mrr.ts                          # MRR aggregator
│   ├── calc-ladder-completeness.ts            # 0-100 score
│   └── parse-whatsapp-zip.ts                  # client-side validate ZIP structure pre-upload
└── config/
    └── comunify.config.ts                     # Feature flags + microcopy SSoT
```

### 4.2 Boundary matrix per FSD-Lite

Same as Story 11 — brand isolation per path. NO cross-brand imports.

---

## § 5. Components inventory

### 5.1 Reuse `@luana/ui` Shadcn primitives (16 components, zero new)

Per spec § 6.1 — all reused: `Button`, `Input`, `Select`, `RadioGroup`, `Checkbox`, `Dialog`, `Toast`, `Form`, `Progress`, `Skeleton`, `Avatar`, `Badge`, `Card`, `Sheet`, `Tabs`, `Table`, `Tooltip`, `Slider`.

### 5.2 Reuse `@luana/shared` cross-brand components (10 — adds 2 over Story 11)

| Component | Path | Uso Story 12 |
|---|---|---|
| `DataTable` | `@luana/shared/data-table` | Roster, subscriptions, audit log, broadcasts |
| `FormWizard` | `@luana/shared/form-wizard` | Onboarding 4-step, offer 5-step, broadcast compose |
| `EmptyState` | `@luana/shared/empty-state` | All empty UI states |
| `ErrorBoundary` | `@luana/shared/error-boundary` | All routes |
| `TenantSwitcher` | `@luana/shared/tenant-switcher` | Header (single-tenant Story 12) |
| `SidebarLayout` | `@luana/shared/sidebar-layout` | App shell |
| `PageHeader` | `@luana/shared/page-header` | Breadcrumbs + actions |
| `FormRuntime` | `@luana/shared/form-runtime` | Brand Studio sections autosave (10 sections!) |
| **`FileUploadZone`** | `@luana/shared/file-upload-zone` | **★ NEW reuse for voice cloning samples upload** |
| **`AsyncJobStatus`** | `@luana/shared/async-job-status` | **★ NEW reuse for distillation progress polling** |

### 5.3 NEW comunify-specific components (11 — justification anti-duplication)

#### 5.3.1 `CreatorNichePicker`

```tsx
type CreatorNiche = "business_coaching" | "health_creator" | "course_creator" | "content_creator" | "expert_author" | "consultant";

interface CreatorNichePickerProps {
  value: CreatorNiche | null;
  onChange: (value: CreatorNiche) => void;
  disabled?: boolean;
}
```

**Justification:** creator-economy niche selection with iconography + niche taxonomy. No equivalent en @luana/ui (Vitalia tiene ClinicTypePicker para medical verticales — distinct).

#### 5.3.2 `VoiceSamplesUploader`

```tsx
interface VoiceSamplesUploaderProps {
  tenantId: string;
  onUploadComplete: (samplesCount: number) => void;
}
```

- Composes `FileUploadZone` from `@luana/shared`.
- WhatsApp ZIP parser (`parse-whatsapp-zip.ts` util) — validates structure + counts distinct conversations client-side BEFORE upload.
- Voice notes audio upload (.m4a/.mp3 — Whisper transcription downstream).
- Progress counter "N/50 chats" + disabled CTA tooltip.

**Justification:** voice_cloning_pipeline-specific (WhatsApp ZIP parser + voice notes + sample counter + threshold gate). NEW Story 12.

#### 5.3.3 `VoiceDistilledPreview`

```tsx
interface VoiceDistilledPreviewProps {
  jobId: string;
  compiledBlocks: CompiledVoice;  // 6 bloques
  onRatify: () => void;
  onEdit: (block: keyof CompiledVoice) => void;
  onReDistill: () => void;
}
```

- 6-block compiled voice display (identidad / dialecto / vocabulario / registro / asíNO / anclajes).
- Per-block inline edit mode.
- Ratify CTA.
- Re-distill option (más samples).

**Justification:** vertical-creator-economy + voice_cloning_pipeline specific. NO existing voice display component.

#### 5.3.4 `LadderVisualizer`

```tsx
interface LadderVisualizerProps {
  offers: OfferLadder;  // 4 levels
  conversionProjections?: { l1_to_l2: number; l2_to_l3: number; l3_to_l4: number };
  onEdit: (level: 1 | 2 | 3 | 4) => void;
  onAddOffer: (level: 1 | 2 | 3 | 4) => void;
  onDragReorder: (from: number, to: number) => void;
}
```

- 4-column DAG (Lead Magnet → Tripwire → Core → Premium).
- Drag-drop reorder (`@dnd-kit/core`).
- Conversion projection annotations.
- Completeness badge.
- Per-level card with offer name + price + delivery + completeness bar.

**Justification:** creator-economy-specific 4-level ladder visualization. NEW Story 12.

#### 5.3.5 `AuthorityVaultEditor`

```tsx
interface AuthorityVaultEditorProps {
  vault: AuthorityVault;  // {credentials, case_studies, press_mentions, awards, social_proof}
  onAddCredential, onAddCaseStudy, onAddPressMention, onAddAward;  // callbacks
}
```

- Multi-subsection editor with URL validation status badges.
- Case study templates.
- Social proof aggregator.

**Justification:** authority_vault required vertical-creator-economy specific. NEW Story 12.

#### 5.3.6 `CohortRosterTable`

```tsx
interface CohortRosterTableProps {
  cohortId: string;
  filters: { tier?: "regular" | "premium"; engagementBucket?: "high" | "medium" | "low" };
  members: CohortMember[];
  onMemberClick: (memberId: string) => void;
}
```

- Members table: avatar + name + tier badge + engagement bucket + last_active.
- Status indicator color (🟢 active recent / 🟡 medium / 🔴 inactive 7d+).
- Filter combinations.

**Justification:** community/cohort specific. NEW Story 12.

#### 5.3.7 `CohortBroadcastComposer`

```tsx
interface CohortBroadcastComposerProps {
  cohortId: string;
  membersCount: number;
  onSend: (payload: BroadcastPayload) => void;
}
```

- Multi-channel composer (text + voice embed + video link + attachment).
- Audience segmenter (All | Engaged only | Inactive 7d+).
- Rate-limit pre-flight check display.

**Justification:** cohort + multi-channel + rate-limit specific. NEW Story 12.

#### 5.3.8 `CommunityModerationCard`

```tsx
interface CommunityModerationCardProps {
  post: CommunityPost;
  classifierScores: { spam: number; nsfw: number; doxxing: boolean };
  memberContext: { tier: string; cohort: string; firstPost: boolean };
  onAction: (action: "approve" | "reject" | "ban") => void;
}
```

- Pending post card with classifier scores annotated.
- Member context badges.
- 3 action CTAs.

**Justification:** agentic moderator coupled vertical-creator-economy specific. NEW Story 12.

#### 5.3.9 `SubscriptionMetricsCards`

```tsx
interface SubscriptionMetricsCardsProps {
  mrr: { amount: number; currency: string };
  activeCount: number;
  churnRate: number;
  distribution: { active: number; past_due: number; cancelled: number };
}
```

- MRR + active subs + churn rate cards.
- Distribution bar chart.

**Justification:** recurring-billing creator-economy specific. NEW Story 12.

#### 5.3.10 `DunningActiveBanner`

```tsx
interface DunningActiveBannerProps {
  count: number;
  nextRetryIn: number;  // seconds
  onResendLinks: () => void;
}
```

- Top-of-page amber alert when past-due subscribers exist.
- "Reenviar links de pago" CTA.

**Justification:** recurring-billing dunning state specific. NEW Story 12.

#### 5.3.11 `CreatorLandingHero`

```tsx
interface CreatorLandingHeroProps {
  creator: { name: string; tagline: string; photoUrl: string };
  authoritySnippets: { credentials: number; case_studies: number; press: number; nps?: number };
  offerLadderPreview: OfferLadder;
}
```

- Public landing hero (`/public/[creator-handle]`).
- Creator photo + tagline + authority signals stack.
- Offer ladder visible.

**Justification:** public-facing creator-economy vertical specific. NEW Story 12.

---

## § 6. React Query hooks (data flow)

### 6.1 Query keys (per spec § 7.2)

```typescript
export const comunifyQueryKeys = {
  onboarding: {
    plans: () => ["comunify", "onboarding", "plans"] as const,
    handleCheck: (handle: string) => ["comunify", "onboarding", "handle-check", { handle }] as const,
  },
  brandStudio: {
    sections: () => ["comunify", "brand-studio", "sections"] as const,
  },
  voiceCloning: {
    samples: () => ["comunify", "voice-cloning", "samples", "status"] as const,
    distillation: (jobId: string) => ["comunify", "voice-cloning", "distillation", { jobId }] as const,
  },
  authorityVault: {
    all: () => ["comunify", "authority-vault"] as const,
  },
  offers: {
    list: (filters?: object) => ["comunify", "offers", "list", filters] as const,
    preset: () => ["comunify", "offers", "presets", "coaching_offers_v1"] as const,
  },
  ladder: () => ["comunify", "ladder"] as const,
  cohorts: {
    list: () => ["comunify", "cohorts", "list"] as const,
    detail: (id: string) => ["comunify", "cohorts", "detail", id] as const,
    roster: (id: string, filters: object) => ["comunify", "cohorts", "roster", id, filters] as const,
    broadcasts: (id: string) => ["comunify", "cohorts", "broadcasts", id] as const,
  },
  community: {
    feed: (filters: object) => ["comunify", "community", "feed", filters] as const,
    moderationInbox: () => ["comunify", "community", "moderation", "inbox"] as const,
  },
  subscriptions: {
    list: (filters: { status?: string }) => ["comunify", "subscriptions", "list", filters] as const,
    detail: (id: string) => ["comunify", "subscriptions", "detail", id] as const,
    metrics: () => ["comunify", "subscriptions", "metrics"] as const,
  },
  audit: {
    events: (filters: object) => ["comunify", "audit", "events", filters] as const,
  },
} as const;
```

### 6.2 Mutation invalidations (per spec § 7.3)

```typescript
// voice ratify → invalidates brand-studio sections + Slot 5 (server-side)
export function useVoiceRatify() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (jobId: string) => fetchClient.post(`/api/v1/comunify/voice-cloning/ratify`, { job_id: jobId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: comunifyQueryKeys.brandStudio.sections() });
    },
  });
}

// cohort broadcast → invalidates broadcasts list for that cohort
export function useCohortBroadcastSend(cohortId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: BroadcastPayload) =>
      fetchClient.post(`/api/v1/comunify/cohorts/${cohortId}/broadcasts`, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: comunifyQueryKeys.cohorts.broadcasts(cohortId) });
    },
  });
}

// moderation action → invalidates inbox
export function useModerationAction() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ postId, action }: { postId: string; action: string }) =>
      fetchClient.post(`/api/v1/comunify/community/moderation/${postId}/action`, { action }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: comunifyQueryKeys.community.moderationInbox() });
    },
  });
}
```

### 6.3 `fetchClient` auto-inject `X-Tenant-ID`

Same pattern Story 11 — Clerk session_claims authoritative.

### 6.4 Voice distillation polling pattern

```typescript
export function useVoiceDistillationPoll(jobId: string | null) {
  return useQuery({
    queryKey: comunifyQueryKeys.voiceCloning.distillation(jobId ?? ""),
    queryFn: () => fetchClient.get<DistillJobStatus>(`/api/v1/comunify/voice-cloning/distillation/${jobId}`),
    enabled: !!jobId,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (!data) return 5000;
      if (data.status === "completed" || data.status === "failed") return false;
      return 5000;  // 5s poll
    },
  });
}
```

---

## § 7. Zod schemas (shared validation BE + FE contract)

### 7.1 Pattern

```typescript
export const creatorProfileSchema = z.object({
  creator_name: z.string().min(2).max(120),
  creator_handle: z.string().min(3).max(40).regex(/^[a-z0-9-]+$/, "Solo letras, números, guion"),
  country: z.enum(["AR", "CL", "MX", "CO", "PE", "BR", "UY", "US", "ES"]),
  city: z.string().min(2).max(120),
  main_language: z.enum(["es-neutral", "es-AR", "es-CL", "es-MX"]),
});

export type CreatorProfileInput = z.infer<typeof creatorProfileSchema>;
```

### 7.2 Schemas inventory (14 total — see § 4.1)

---

## § 8. TypeScript types (mirror Pydantic Response DTOs)

### 8.1 Pattern

```typescript
export type CohortStatus =
  | "draft" | "active" | "in_progress" | "completed" | "cancelled";

export interface Cohort {
  id: string;
  tenant_id: string;
  name: string;
  slug: string;
  offer_id: string;
  capacity_max: number;
  capacity_filled: number;
  start_date: string;  // ISO 8601
  end_date: string;
  status: CohortStatus;
  enrollment_criteria: Record<string, unknown>;
  created_at: string;
}

export interface CompiledVoice {
  identidad: string;
  dialecto: string;
  vocabulario: string[];
  registro: string;
  asi_no: string[];
  anclajes: string[];
  confidence_score: number;
}
```

### 8.2 OpenAPI types generation

Same pattern Story 11 — `comunify-api-spec` workspace package generates TS types from FastAPI OpenAPI.

---

## § 9. Subscription widget bundle (iframe embeddable)

### 9.1 Bundle structure

```
luana-platform/comunify/frontend/widget/
├── src/
│   ├── widget-entry.tsx
│   ├── components/
│   │   ├── SubscribeWidgetRoot.tsx
│   │   ├── PlanTierStep.tsx
│   │   ├── PaymentStep.tsx                   # MP + Stripe iframe redirect
│   │   └── SuccessStep.tsx
│   ├── postmessage-protocol.ts
│   └── styles.css                            # Scoped Tailwind subset
├── vite.config.ts                            # Vite builds UMD bundle
└── dist/                                     # widget.umd.js + widget.css
```

### 9.2 Embed snippet (creator copy-paste)

```html
<!-- comunify/docs/widget-embed.md ships this -->
<div id="comunify-subscribe-widget" data-creator-handle="{handle}" data-offer-id="{offer_id}"></div>
<script src="https://cdn.comunify.io/widget/widget.umd.js"></script>
<link rel="stylesheet" href="https://cdn.comunify.io/widget/widget.css" />
```

### 9.3 Canonical URL alternative

`https://landing.comunify.io/{creator-handle}/subscribe?offer_id={id}` (Server Component page route).

---

## § 10. Tests required

### 10.1 Vitest unit

```
comunify/frontend/tests/
├── unit/
│   ├── features/comunify/components/         (11 new component tests)
│   ├── features/comunify/hooks/              (use-flow-context, use-poll-distillation-job)
│   ├── features/comunify/schemas/            (creator-profile, coaching-offer-wizard, cohort-create, ...)
│   └── features/comunify/utils/              (calc-ladder-completeness, format-mrr, parse-whatsapp-zip)
└── integration/
    ├── onboarding-wizard-flow.test.tsx       (4-step)
    ├── offer-wizard-flow.test.tsx            (5-step coaching)
    ├── ladder-build-flow.test.tsx
    └── widget-flow.test.tsx                   (subscribe widget integration)
```

### 10.2 Playwright E2E (per spec § 13.3 matrix — 24 specs)

```
comunify/frontend/e2e/
├── fixtures/
│   ├── anabella-coach-ar.fixture.ts
│   ├── trini-nutrition-cl.fixture.ts
│   └── pablo-productivity-mx.fixture.ts
├── specs/comunify/
│   ├── onboarding-anabella.spec.ts
│   ├── onboarding-trini.spec.ts
│   ├── onboarding-pablo.spec.ts
│   ├── brand-studio-anabella.spec.ts          (10 sections + voice cloning)
│   ├── brand-studio-trini.spec.ts
│   ├── brand-studio-pablo.spec.ts
│   ├── voice-cloning-pipeline-anabella.spec.ts
│   ├── voice-cloning-pipeline-trini.spec.ts
│   ├── voice-cloning-pipeline-pablo.spec.ts
│   ├── authority-vault-anabella.spec.ts
│   ├── ladder-build-anabella.spec.ts
│   ├── ladder-build-pablo.spec.ts
│   ├── cohort-create-anabella.spec.ts
│   ├── cohort-broadcast-anabella.spec.ts
│   ├── cohort-broadcast-rate-limit.spec.ts
│   ├── community-moderation-pass.spec.ts
│   ├── community-moderation-spam.spec.ts
│   ├── community-moderation-doxxing.spec.ts
│   ├── subscription-create-pablo.spec.ts
│   ├── subscription-dunning-anabella.spec.ts
│   ├── subscription-cancel-trini.spec.ts
│   ├── discovery-call-booking-anabella.spec.ts
│   ├── cross-tenant-isolation.spec.ts
│   └── public-landing-authority.spec.ts
└── auth.fixture.ts
```

### 10.3 E2E Native WSL (NEVER Docker — playwright-expert SSoT)

```bash
cd /home/chris/luana-platform && bash scripts/e2e-preflight.sh
cd comunify/frontend && E2E_BASE_URL=http://localhost:3000 npx playwright test --project=smoke
```

---

## § 11. Spanish neutro chrome UI enforcement

Per `.claude/rules/spanish-text.md` R2 + Q1=B ratified spec § 17:

### 11.1 Arch fitness test

```typescript
// comunify/frontend/src/__tests__/architecture/test-comunify-ui-strings-no-voseo.test.ts
const VOSEO_VERBS = [
  /\bvos\b/, /\bsos\b/, /\btenés\b/, /\bquerés\b/, /\bpodés\b/,
  /\bhacés\b/, /\bvenís\b/, /\bdecís\b/, /\bmirá\b/, /\bdejá\b/,
  /\bagregá\b/, /\bconfigurá\b/, /\bguardá\b/, /\bcambiá\b/, /\bprobá\b/,
];

describe("Comunify chrome UI Spanish neutro (Q1=B ratified)", () => {
  it("NO voseo verbs in src/features/comunify/ user-facing strings", () => {
    // Walk + extract user-facing strings + check no voseo
    // Skip files with magic comment "voseo-allowed"
    // sales_agent voice cloning preview block "Dialecto" exception
  });
});
```

### 11.2 SSoT spec § 8 microcopy (immutable)

All comunify chrome UI strings sourced from spec § 8.1–§ 8.8.

---

## § 12. Cross-cutting concerns (FE)

| Concern | Pattern |
|---|---|
| Tenant isolation | `fetchClient` auto-injects `X-Tenant-ID` from Clerk session_claims. NEVER hardcoded. |
| Master data | `useTenantLocale()` hook returns `{ currency, timezone }`. `formatMoney(amount, currency)` consumes data source currency or fallback. |
| PII | Member phone/email already masked at BE response. NO patient/subscriber PII in localStorage / sessionStorage / URL params. |
| Spanish neutro | Microcopy SSoT spec § 8. Arch fitness gate. Magic comment honored. Voice cloning preview block "Dialecto" exception. |
| Error boundaries | All routes wrapped in `@luana/shared/error-boundary`. Toast on API errors. |
| Loading/empty states | All async data uses Skeleton + EmptyState pattern. NO blank screens. |
| Form runtime autosave | Brand Studio sections only (per `form-runtime-array.md`). |
| Voice cloning UX | Sample counter visual (N/50 bar) + polling status (5s interval) + ratify gate. |
| Accessibility | All inputs aria-label/required/invalid. Focus rings. Keyboard navigation. Color-blind mode for engagement/severity badges. |
| Responsive | Breakpoints per spec § 9: mobile <768 / tablet 768-1024 / desktop >1024. |

---

## § 13. Risks + mitigations (FE-specific)

| Risk | Severity | Mitigation |
|---|---|---|
| Voseo leak in microcopy | medium | Arch fitness gate + magic comment + microcopy SSoT |
| Cross-feature import (Vitalia code reaches Comunify) | medium | FSD-Lite boundary plugin error level + per-brand workspace isolation |
| Subscribe widget XSS via creator-handle | high | Server-side render via Next.js SC + sanitize subscriber input + audit log XSS |
| iframe widget origin spoofing | medium | postMessage origin validation + signed subscriber token + HMAC |
| Voice samples upload large file (>500MB ZIP) | medium | Client-side validation pre-upload + chunked upload + progress indicator |
| Cohort capacity race UX double-enrollment | medium | BE advisory lock authoritative + FE optimistic UI rollback on 409 |
| Ladder drag-drop accessibility (keyboard) | medium | @dnd-kit/core keyboard reorder via arrow keys + Enter swap |
| Member PII in URL params | medium | All member data via POST body + signed JWT tokens for public flows |
| Date timezone confusion (creator UTC-3 viewing subscriber UTC-6) | medium | UTC storage + `useTenantLocale()` display |
| Vitest coverage <20% threshold | medium | Per-ticket coverage gate enforced via validators YAML |
| Playwright E2E flakiness with Clerk auth (3 fixtures × 8 flows) | medium | playwright-expert SSoT freshness gate + retry + sanity check |

---

## § 14. Próximo paso

`architect-fe` returns: `done -> 03-arch-fe.md`. /architect orchestrator consolidates.

done -> docs/product/stories/luana-comunify-bootstrap/03-arch-fe.md
