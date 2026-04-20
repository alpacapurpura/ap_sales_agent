# UI-SPEC — Copilot Sidebar (section-scoped, persistent)

**Status:** ready-for-implementation (depends on shell spec)
**Scope:** `OfferSectionCopilot` component + `copilotSlot` extension in form-runtime + `useOfferCopilot` hook
**Feeds agent:** `nicolify-frontend` (frontend) + `nicolify-agentic` (backend tools in Phase F)

---

## 1. Purpose

Brand-studio launches copilot only at creation (dashboard). Offer-studio extends this: copilot is a **persistent actor during editing**, scoped to the active section, with section-specific tools grounded in the offer's preset flags + brand data.

This is the **only net-new UX pattern vs brand-studio**. Once merged, brand-studio can adopt it in a later sprint (non-breaking).

---

## 2. Form-runtime extension (non-breaking)

### Change to `UniversalEditableSection`

```ts
interface UniversalEditableSectionProps<TSlice> {
  // ... existing props
  /** Optional right-side slot. When provided, section renders in split-view. */
  copilotSlot?: ReactNode;
}
```

**Layout behavior:**
- If `copilotSlot === undefined` → render existing 2-col (nav + form). Brand-studio unchanged.
- If `copilotSlot` is provided → render 3-col grid (nav + form + copilot).
- At < 1024px viewport → copilot collapses to 48px rail + click-to-overlay.

**CSS grid (extended):**
```css
.section-container {
  display: grid;
  grid-template-columns: var(--col-nav) 1fr;
}
.section-container:has(.copilot-slot) {
  grid-template-columns: var(--col-nav) 1fr var(--col-copilot);
}
```

---

## 3. `OfferSectionCopilot` component

### Props
```ts
interface OfferSectionCopilotProps {
  offerId: string;
  sectionSlug: string;          // from OFFER_SECTIONS
  editionCode?: string;         // optional — when EditionsRail has selection
}
```

### Anatomy
```
┌──────────────────────────────┐
│ ● Copiloto · {sectionLabel}  │  ← header (h=44)  + collapse chevron
├──────────────────────────────┤
│ [suggestion-card]            │
│ [suggestion-card]            │  ← body (scroll)
│ [suggestion-card]            │
│ ...                          │
└──────────────────────────────┘
```

### Suggestion card structure
```tsx
<div className="suggestion-card">
  <div className="tool-tag">✨ {toolCategory}</div>    // uppercase 10px, brand color
  <div className="suggestion-title">{toolTitle}</div>   // 13px / 600
  <div className="suggestion-body">{toolDescription}</div> // 12.5px / muted
  <div className="actions">
    <button className="btn brand sm">{primaryAction}</button>
    <button className="btn sm">{secondaryAction?}</button>
  </div>
</div>
```

### States
| State | Content |
|---|---|
| **Loading** | Skeleton: 3 card stubs with shimmer |
| **Empty** (no tools applicable) | "No hay sugerencias por ahora para esta sección." + disabled "Iniciar entrevista" button |
| **Onboarding** (section never touched) | Interview CTA prominent + 1-2 passive suggestions |
| **Active editing** | 2-4 suggestion cards stacked |
| **Error** | Toast + retry button |
| **Collapsed** | 48px rail with dot + pulse (visible: 1 unread-suggestion dot if new tool surfaced) |

### Collapse toggle
- Click chevron (◀ / ▶) in header.
- State persisted to `localStorage['offer-studio:copilot-collapsed']`.
- Default: expanded.
- When collapsed, body hidden; only 48px rail with `●` dot remains.

---

## 4. Tool integration points (per section)

Tools live in backend: `backend/src/modules/copilot/tools/offer_section_tools.py`.

### Tool contract

All tools follow:
```python
@copilot_tool(entity_type="offer-section", section_slug="pricing")
def high_ticket_tiering_template(
    tenant_id: UUID,
    offer_id: UUID,
    edition_code: str | None = None,
) -> ToolResponse:
    # returns: {
    #   "title": "3-tier con anclaje",
    #   "description": "...",
    #   "draft_fields": {"tiers": [...]},  # form-runtime patch
    #   "primary_action": {"label": "Aplicar plantilla", "result_key": "apply_high_ticket_template"},
    # }
```

### Per-section tool catalog

| Section | Tool key | Trigger | Primary action |
|---|---|---|---|
| **Identity** | `adapt_from_brand_identity` | Always available | Adaptar desde Brand |
| **Promise** | `adapt_from_brand_narrative` | Always | Adaptar desde Brand |
| **Promise** | `rewrite_tones` | Field "central_promise" active | Generar 3 variantes |
| **Promise** | `validate_preset_coherence` | On save | Badge de validación |
| **Audience** | `reuse_brand_buyer_personas` | Brand has ≥1 persona | Importar persona |
| **Methodology** | `inherit_brand_methodology` | Brand has methodology | Heredar |
| **Pricing** | `high_ticket_tiering_template` | `preset.flags includes HIGH_TICKET` | Aplicar plantilla |
| **Pricing** | `recurring_billing_setup` | `RECURRING_BILLING` | Configurar ciclo |
| **Pricing** | `detect_currency_mismatch` | On load | Resolver |
| **Schedule** | `import_scheduling_event_type` | `REQUIRES_START_DATE` + scheduling connection | Importar event type |
| **Location** | `detect_hybrid_split` | `DELIVERY_HYBRID` | Configurar split |
| **Testimonials** | `import_from_brand_vault` | Brand vault has testimonials | Ver + importar |
| **Testimonials** | `suggest_missing_objections` | ≥3 testimonials added | Ver faltantes |
| **Testimonials** | `auto_transcribe_video` | Video testimonial added | Transcribir |
| **FAQ** | `generate_from_preset_flags` | Always | Generar 5 preguntas |
| **FAQ** | `pull_sales_agent_common_questions` | Sales agent has history | Importar top 5 |
| **Value stack** | `assemble_from_brand_authority` | Brand has authority items | Construir stack |
| **Instructors** | `reuse_brand_team` | Brand has team | Importar instructores |

---

## 5. `useOfferCopilot` hook

```ts
interface OfferCopilotSession {
  suggestions: CopilotSuggestion[];
  isLoading: boolean;
  isError: boolean;
  executeTool: (toolKey: string) => Promise<ToolResponse>;
  startInterview: () => void;   // delegates to existing startInterview
}

function useOfferCopilot(args: {
  offerId: string;
  sectionSlug: string;
  editionCode?: string;
}): OfferCopilotSession;
```

**Implementation:**
- React Query: `["copilot", "offer-section", offerId, sectionSlug, editionCode]`.
- Endpoint: `GET /api/v1/copilot/suggestions?entity_type=offer-section&offer_id={id}&section={slug}&edition={code?}`.
- `executeTool(key)`: `POST /api/v1/copilot/tools/{key}` with context → response includes `draft_fields` that can be applied to form-runtime via `useUniversalEditableSection().applyDraftFields(patch)`.

---

## 6. Interaction flow

```
1. User opens /offer/:id/editor/pricing
2. useOfferCopilot loads suggestions for sectionSlug="pricing"
3. Backend tool registry filters by: preset.flags, brand completeness, edition state
4. UI renders 2-4 suggestion cards
5. User clicks "Aplicar plantilla" on high_ticket_tiering_template
6. executeTool("high_ticket_tiering_template") → returns draft_fields
7. Form-runtime applies draft as unsaved patch → user sees pending state in form
8. User adjusts + clicks Save → standard form-runtime save path
9. After save, useOfferCopilot invalidates → new suggestion: "Edition Q2 tiene override"
```

---

## 7. Visual states (ASCII)

### Expanded, populated
```
┌────────────────────────────┐
│ ● Copiloto · Pricing   ◀   │
├────────────────────────────┤
│ ┌────────────────────────┐ │
│ │ 🚀 HIGH_TICKET TIERING │ │
│ │ 3 tiers con anclaje    │ │
│ │ Tu preset tiene flag.. │ │
│ │ [Aplicar plantilla]    │ │
│ └────────────────────────┘ │
│ ┌────────────────────────┐ │
│ │ 🔗 EDITION OVERRIDES   │ │
│ │ Q2 Launch tiene ovrd   │ │
│ │ ...                    │ │
│ └────────────────────────┘ │
└────────────────────────────┘
```

### Collapsed
```
┌──┐
│● │  ← dot (pulse if unread)
│◀ │  ← expand chevron
│  │
│  │
└──┘
```

### Onboarding (section untouched)
```
┌────────────────────────────┐
│ ● Copiloto · Promesa   ◀   │
├────────────────────────────┤
│ ┌────────────────────────┐ │
│ │ ★ ONBOARDING           │ │
│ │ ¿Entrevista guiada?    │ │
│ │ 5 min. Completo todos  │ │
│ │ los campos automático. │ │
│ │ [Iniciar entrevista]   │ │
│ │ [Más tarde]            │ │
│ └────────────────────────┘ │
└────────────────────────────┘
```

---

## 8. Copy tone (español neutro LatAm)

Per `.claude/rules/spanish-text.md` — **tuteo, NO voseo**.

Examples (✅ correct):
- "Te ayudo a completar esto"
- "Puedes iniciar la entrevista"
- "Revisa las sugerencias"

Anti-examples (❌ forbidden):
- "Te ayudo a completar esto, dale" (voseo)
- "Mirá las sugerencias"

---

## 9. Accessibility

- Each suggestion card: `role="region"` + `aria-label={toolTitle}`.
- Collapse button: `aria-expanded`, `aria-controls="copilot-body"`.
- Keyboard: `Shift+Tab` from form-runtime enters copilot. `Esc` collapses copilot.
- Screen reader: announces new suggestions via `aria-live="polite"` on body container.

---

## 10. Testing

### Unit (Vitest)
- `OfferSectionCopilot.test.tsx` — renders suggestion cards, handles empty/loading/error, collapse state persists.
- `useOfferCopilot.test.ts` — mocks React Query, tests executeTool + invalidation.

### Integration
- `UniversalEditableSection.test.tsx` — existing tests pass with `copilotSlot={undefined}` (regression).
- New test: renders 3-col grid when `copilotSlot` provided.

### Backend
- `test_offer_section_tools.py` — each tool: inputs produce expected ToolResponse; registry lookup by `entity_type + section_slug` works.

### E2E
- Smoke: open offer → section "pricing" → HIGH_TICKET preset → copilot shows tier template → click apply → form fields populated.
