# UI-SPEC — Progressive Feedback for Generic Async Copilot Extractions

**Status:** proposal (awaiting final OK for implementation)
**Scope:** Behavioral layer for async copilot tools across Brand Studio, Offer Studio, Assets, Personas and future extractions.
**Preserves:** Chat rail layout, `AssistantMessageV2`, `ToolCallChip`, `ClarifyCard`, `NavigationCard`, `BrandStudioNavRail`, `OfferStudioNavRail`.

---

## Legend

Every proposal lists **Reuses** (existing files untouched), **Extends** (existing files modified) and **New** (files created).

---

## Proposal 0 — Enrich scope clarification (LLM prompt delta)

**Why:** `extract_from_url`'s docstring already instructs the LLM to call `clarify` before dispatching (see `extraction_tools.py:233-237`). The hint is minimal — it lists only mode options. We extend it to explicitly surface scope + mode as two-dimensional options, rendered by a new card kind that handles both axes in one shot.

**Content change (tool docstring + system prompt addendum):**

```
Antes de llamar extract_from_url/extract_from_doc:

1. Si el usuario NO especificó alcance:
   Emit clarify card con items:
     - fieldPath: "__scope__"
       issue:    "¿Qué querés extraer?"
       options:  [ "Solo {current_section_label} (esta página)" (if on section),
                   "Todo {module_label}",
                   "Solo una sección específica…" ]
     - fieldPath: "__mode__"
       issue:    "¿Cómo escribo los campos?"
       options:  [ "Solo llenar vacíos",
                   "Reemplazar todo",
                   "Sugerir (no escribir)" ]

2. Usa ClientContext.current_route para inferir {current_section_label}.
3. Si el usuario responde 'Solo …sección actual', setea scope="section" + section=<slug from route>.
4. mode="update" ≈ "solo llenar vacíos"; mode="initial" ≈ "reemplazar";
   mode="suggest" = nuevo (no escribe — genera proposals).
```

**Reuses:** `ClarifyCard.tsx` (multi-item support already in the code at `cards/ClarifyCard.tsx:65-88`).
**Extends:** `extraction_tools.py` docstring + system-prompt composer for extraction flows.
**New:** — (zero new components)

**Impact:** High — removes ambiguity before async starts. **Effort:** XS.

---

## Proposal 1 — `useAsyncToolJob` hook + `activeJobs` store slice (FOUNDATION)

**Why:** Every subsequent proposal reads job state from this slice. Build once, reuse across all async tools.

```ts
// frontend/src/features/copilot/hooks/use-async-tool-job.ts
export type AsyncJobState = {
  jobId: string;
  module: "brand" | "offer" | "asset" | "persona";
  scope: "full" | "section" | "field" | "visuals";
  mode: "initial" | "update" | "suggest";
  section: string | null;
  targetLabel: string;
  sourceKind: "url" | "doc" | "media";
  sourceRef: string;
  status: "queued" | "running" | "completed" | "failed";
  progress: number;                         // 0..100
  stage: string;
  filledFields: string[];
  filledFieldsBySection: Record<string, string[]>;
  sectionsTouched: string[];
  sectionsCompleted: string[];
  error?: string;
  startedAt: number;
  finishedAt?: number;
};

export function useAsyncToolJob(jobId: string): AsyncJobState;
export function useActiveJobs(): AsyncJobState[];
export function useActiveJobsForModule(module: string): AsyncJobState[];
```

Behavior:
- Polls `poll_endpoint` every 2s. Back-off to 5s after 60s.
- Writes to `copilot-store.activeJobs[jobId]`.
- On each poll, if `filled_fields` grew → dispatches one `CustomEvent("copilot:field-update", {fieldId, value})` per new field (reuses existing listener in `use-copilot-field-sync.ts:13-30`).
- On `newly_completed_section`: nothing — the backend already emitted the inline pill (Proposal 5). The hook just updates state.
- On `status = "completed"`: invalidates `JOB_INVALIDATION_MAP[module]` via React Query.
- On `status = "completed" | "failed"` + `document.hidden`: triggers tab-blur notification (Proposal 6).
- Auto-stops polling on terminal status.

**Reuses:** `ai-actions.ts:92-101` orphan helper `pollExtractionStatus` (promote to `pollJobStatus`, generalize); React Query client; existing `window.copilot:field-update` bridge.
**Extends:** `copilot-store.ts` — add `activeJobs: Record<string, AsyncJobState>`, actions `registerJob`, `updateJob`, `completeJob`.
**New:** `use-async-tool-job.ts`; `lib/job-invalidation-map.ts`.

**Impact:** Foundational (none user-facing alone). **Effort:** M (~1d).

---

## Proposal 2 — Live `ToolCallChip` with progress + counters

**Why:** The chip is already rendered per `toolCalls[]` entry in `AssistantMessageV2.tsx:55-61`. Today it's binary (spinner / check). Extending to show live state is a single-component change.

**Before** (`ToolCallChip.tsx:24-44` — pill, 1 row):
```
[⟳] [🔧] extract_from_url
```

**After** — pill expands to 3 rows when `jobId` is present and `status === "running"`:
```
┌───────────────────────────────────────────┐
│ ⟳  🔧  Analizando página web      42%    │  row 1: existing + right-aligned pct
│ ▓▓▓▓▓▓▓▓░░░░░░░░░░░                       │  row 2: progress bar (1px track)
│ Analizando sección 'Nosotros'             │  row 3: stage text
│ 12 campos · 3 secciones                   │  row 4: optional counters (mutes if 0)
└───────────────────────────────────────────┘
```

On `status = "completed"`:
```
┌───────────────────────────────────────────┐
│ ✓  🔧  Analizando página web · 38s       │  collapses back to pill
│ 27 campos sugeridos · 6 secciones         │  single-line counter
└───────────────────────────────────────────┘
```

Visual tokens: progress bar fill = `bg-brand`, success variant = `bg-success`. Same radii, fonts, border as current chip. No layout shift outside the chip.

**Reuses:** `humanizeToolName` (`utils/tool-labels.ts`) — already maps `extract_from_url` → "Analizando página web"; `Loader2`, `Check`, `Wrench` icons; `cn()`.
**Extends:** `ToolCallChip.tsx` — add optional `jobId?: string` prop. When present, subscribes to `useAsyncToolJob(jobId)` and renders extended layout.
**New:** —

**Impact:** High — visible progress where user already looks. **Effort:** S (~2h).

---

## Proposal 3 — `ExtractionSummaryCard` (new `CardKind`)

**Why:** Direct fix for the phantom "te aviso" promise. On completion, worker posts an assistant message containing a summary card.

**Layout** (mirrors `ClarifyCard.tsx:45-91` tokens — same `rounded-xl border border-border bg-card p-3.5 shadow-sm ring-1 ring-brand/10` shell):

```
┌──────────────────────────────────────────┐
│ ✓  Listo — analicé visionarias.pe    38s │
│ ──────────────────────────────────────   │
│ ┌──────────────┐  ┌──────────────┐      │
│ │ 27           │  │ 6            │      │
│ │ campos       │  │ secciones    │      │
│ └──────────────┘  └──────────────┘      │
│                                          │
│ COBERTURA POR SECCIÓN                    │
│ Identidad      ▓▓▓▓▓▓▓▓░░  14/18         │
│ Estrategia     ▓▓▓▓▓▓░░░░   8/15         │
│ Público        ▓▓▓▓░░░░░░   5/12         │
│                                          │
│ Supuestos: 4  ·  Preguntas: 6            │
│                                          │
│ [ Revisar Identidad → ]  [ Ver preguntas ]│
└──────────────────────────────────────────┘
```

**Backend card emission** (see §3.4 of FLOW-SPEC): at end of `run_brand_extraction` / `run_offer_extraction`, insert assistant message with:

```json
{
  "role": "assistant",
  "content": "",
  "blocks": [
    { "type": "card", "card_kind": "extraction_summary",
      "data": {
        "source_ref": "https://visionarias.pe",
        "duration_seconds": 38,
        "total_fields": 27,
        "total_sections": 6,
        "coverage_by_section": [
          {"slug": "identity", "label": "Identidad", "filled": 14, "total": 18},
          ...
        ],
        "strong_assumptions_count": 4,
        "open_questions_count": 6,
        "primary_cta_route": "/brand-studio/identity"
      }
    }
  ]
}
```

**Reuses:** `ClarifyCard.tsx` tokens (copy — don't import — since visual only); `humanizeToolName`; existing `blocks[]` + `BlockDispatcher` path.
**Extends:** `message-blocks.ts` — extend `CardKind` union with `"extraction_summary"`; `CardBlock.tsx` — add dispatch case.
**New:** `ExtractionSummaryCard.tsx` (~90 LOC).

**Impact:** High — closes the loop, becomes the artifact users mention when reviewing what happened. **Effort:** S (~4h).

---

## Proposal 4 — NavRail section badges (cross-section awareness) — PROMOTED TO P1

**Why:** Solves the "I'm on Identidad but extracting the whole brand" case. The left 260px column listing sections already exists (`BrandStudioNavRail.tsx` line 20; `OfferStudioNavRail.tsx` mirror) and its own comment anticipates the slot: *"optional completion preview (`3/9`, `2 ítems`) rendered mid-row"* (line 18). We fill that slot with live status.

**State machine per section** (derived from `activeJobs` slice):

| Section status | Derivation | Visual |
|---|---|---|
| `idle` | Not in any `sectionsTouched` | No badge |
| `queued` | In `sectionsTouched`, not in `sectionsCompleted`, and no `filled_fields_by_section[slug]` yet | `·` dim dot (same muted chevron color) |
| `running` | In `sectionsTouched`, `filled_fields_by_section[slug].length > 0`, not yet `sectionsCompleted` | `⟳` brand-colored spinner + `N entrando` in `bg-brand/10` pill |
| `completed` | In `sectionsCompleted` | `✓` success icon + `N sugeridos` in `bg-success/10` pill |

**Row (extended)** — same 36px height, chevron stays rightmost, badge sits between label and chevron:
```
[icon] Identidad            ⟳ 4    >     ← running
[icon] Metodología          ✓ 5    >     ← completed
[icon] Público              · 3    >     ← queued (touched, no fields yet)
[icon] Visuales                    >     ← idle
```

Hovering a completed/running row shows a small tooltip with the list of fields.

**Reuses:** `BRAND_SECTIONS` / `OFFER_SECTIONS` catalogs; `FinderColumn`; `cn`.
**Extends:** `BrandStudioNavRail.tsx` — `SectionRow` gets optional `status: SectionStatus` prop derived via `useActiveJobsForModule('brand')`; mirror for `OfferStudioNavRail.tsx`.
**New:** `frontend/src/features/copilot/hooks/use-section-status.ts` (tiny selector hook, ~25 LOC).

**Impact:** Very high — makes extraction feel alive across the whole studio, not just the current page. **Effort:** M (~4h including tests).

---

## Proposal 5 — Inline section-complete pills in chat (NEW P1)

**Why:** Even with sidebar badges, users scan the chat. As each section completes, post a compact pill in the conversation:
```
✓ Metodología lista · 5 campos sugeridos   [Revisar →]
```

Clickable — navigates to that section.

**Reuses:** `NavigationCard.tsx:20-61` **exactly as-is** — it already renders as a small CTA with `MapPin` icon, purple tint, `ArrowRight`. We emit it with `card_kind="navigation"` and enrich `UIAction.page_label` with the fields count.

Example emission (worker-side, each time a section transitions to `completed`):
```json
{
  "blocks": [{
    "type": "card",
    "card_kind": "navigation",
    "data": {
      "type": "navigate",
      "route": "/{tenantId}/brand-studio/methodology",
      "page_label": "✓ Metodología lista · 5 campos",
      "section_id": "methodology"
    }
  }]
}
```

**Reuses:** `NavigationCard.tsx` (zero changes); `useCopilotNavigator`; `reportCopilotEvent`; `CardBlock` dispatch.
**Extends:** Worker logic in `brand/workers/tasks.py` and `offer/workers/tasks.py` — emit one message per `newly_completed_section`.
**New:** —

**Impact:** High — per-section closure visible in chat history. **Effort:** S (~2h).

---

## Proposal 6 — Tab-blur notification

**Why:** 90s extractions overlap with tab switching. If user is away, they should get a ping.

Behavior in `useAsyncToolJob`:
- On `completed`/`failed` + `document.hidden`: fire `sonner` toast (persistent) + `new Notification(...)` (if permission granted — prompt on first job start).
- Title flash: set `document.title = "(1) Nicolify — Extracción lista"`, restore on `visibilitychange → visible`.

**Reuses:** `sonner` (already imported in `use-brand-settings.ts:3`); native `Notification`.
**Extends:** `useAsyncToolJob` (Proposal 1).
**New:** `use-tab-notification-permission.ts` (tiny — request + store permission state).

**Impact:** High for real async. **Effort:** S (~1h).

---

## Proposal 7 (P2) — Field shimmer + global counter in form header

**Why:** The most visceral "se está llenando" feedback. As each field arrives from the worker, its input plays a pulse.

**Reuses:** **`copilot-highlight` CSS class already defined** in `frontend/src/app/globals.css:262-267` (`copilotPulse` keyframe with 3 pulses + brand outline). Perfect fit, zero new CSS.

Integration:
- `use-copilot-field-sync.ts:22-25` currently calls `setValue(fieldId, value, {shouldDirty: true, shouldValidate: true})`. Extend to also toggle the class on the matching input ref for 3 seconds.
- Add `use-global-fill-counter.ts` returning `{filled, total}` per active job — rendered as a discreet pill in studio headers.

**Reuses:** existing animation class; existing field-sync bridge.
**Extends:** `use-copilot-field-sync.ts`; brand-studio and offer-studio studio-header components.
**New:** `use-global-fill-counter.ts`.

**Impact:** Very high. **Effort:** M (~1d). Deferred to v2 — not blocking the main "te aviso" fix.

---

## Proposal 8 (P3) — Ambient footer bar in chat rail

Sticky persistent progress above composer when user scrolls chat up.

**Reuses:** progress bar primitive from Proposal 2.
**Extends:** `CopilotChatPanel.tsx` — insert `<ActiveJobBar />` above `<ChatComposer />`.
**New:** `ActiveJobBar.tsx`.

**Impact:** Medium polish. **Effort:** S.

---

## Shipping order (v1 = 0+1+2+3+4+5+6)

Total ≈ 3 days. Addresses every issue raised:
- Phantom "te aviso" → Proposals 3 + 6
- No live progress signal → Proposals 2 + 4
- Ambiguous scope → Proposal 0
- Cross-section blind spot → Proposals 4 + 5
- No closure artifact → Proposal 3

v2 = 7 (shimmer + counter). v3 = 8 (ambient bar).

---

## Invariants (no regressions allowed)

1. **Backwards-compat on tool params:** existing calls with `offer_id` must work. Aliased to `entity_id` server-side.
2. **Existing `toolCalls[]` rendering** must keep working for tools without `jobId` (old behavior for non-async tools).
3. **`pollExtractionStatus`** remains importable if any external caller exists — generalized signature is strict superset.
4. **Conversation persistence:** both the summary card and the section-complete pills are written as real messages, so page reload shows them.
5. **Spanish LatAm neutro** (per `.claude/rules/spanish-text.md`): all user-visible strings tuteo, no voseo.
6. **`redirect_slashes=False`** unaffected (API routes unchanged).
7. **Backend DDD:** no cross-module imports. Worker emits cards via conversation repository (already used).
8. **Tenant isolation:** `tenant_id` filter preserved in every DB/Redis key.

## Out of scope (explicitly not in v1)

- WebSocket push (polling is fine at 2s resolution).
- Streaming LLM reasoning tokens inside the chip (Perplexity-style).
- Job queue UI (list all running/historical jobs) — deferred.
- Job cancellation (requires worker-side interrupt support).
- Per-field undo (today: conversation-level undo via `MutationUndoButton`).
