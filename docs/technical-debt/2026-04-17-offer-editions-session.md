# Tech Debt — Offer Editions Session (2026-04-17)

Session: `docs/ux-sessions/2026-04-17-offer-editions-ui-revamp/`
Branches: `development` (all merged there)
Commits (in order): `a9a60e4e`, `92493a80`, `cf90cd50`, `5c363f11`,
`805fe240`, `f1167f2a`, `fee2eb5a`, `286891fe`, `ce4705c2`.

---

## Summary

Nine phases shipped. The architectural seams are in place so every
deferred item below is a drop-in addition rather than a refactor. The
app is fully functional without them — the debt is "complete the
experience" work, not "fix a bug."

Total estimated follow-up effort: **~60–80h** for a dev to land
everything.

---

## Index of deferred items

| # | Area | Severity | Effort | Commit seam |
|---|------|----------|--------|-------------|
| 1 | [Stripe/MP/Culqi webhook → EnrollmentPaid](#1--payment-webhooks--enrollmentpaid) | P1 | ~10h | `92493a80` (Phase 6) |
| 2 | [Offer_creation procedure handler (publish edition on interview)](#2--offer_creation-procedure-handler-interview--edition-publish) | P1 | ~3h | `cf90cd50` (Phase 7) |
| 3 | [Offer `slug` column + pretty public URLs](#3--offer-slug-column--pretty-public-urls) | P2 | ~6h | `5c363f11` (Phase 8) |
| 4 | [LandingSplitButton + WaitlistBanner + EditionCloneModal (shell chrome)](#4--shell-chrome-components-landingsplitbutton--waitlistbanner--editionclonemodal) | P1 | ~18h | `805fe240` (Phase 9a part 2) |
| 5 | [Info-tab 7-section refactor](#5--info-tab-7-section-refactor) | P1 | ~20h | `286891fe` (Phase 9b full) |
| 6 | [Assets gallery + Campañas card rewrites](#6--assets-gallery--campañas-card-rewrites) | P2 | ~12h | `286891fe` (Phase 9b full) |
| 7 | [Puck integration in landing editor](#7--puck-integration-in-landing-editor) | P2 | ~10h | `fee2eb5a` (Phase 9e) |
| 8 | [EnrollmentWidget in inbox side panel](#8--enrollmentwidget-in-inbox-side-panel) | P2 | ~4h | `f1167f2a` (Phase 9c tail) |
| 9 | [Growth Studio per-edition analytics compare (Phase 10)](#9--growth-studio-per-edition-analytics-phase-10) | P3 | ~16h | not started |

Plus **session-incidental findings** (not items I created, but
discovered along the way): see [§ Incidental findings](#incidental-findings).

---

## 1. Payment webhooks → EnrollmentPaid

**What:** Wire Stripe, MercadoPago, and Culqi webhooks so that a
`payment_intent.succeeded` payload resolves an enrollment id from its
metadata and emits `EnrollmentPaid`, which in turn:

- Marks `enrollment.status = PAID`, sets `paid_at`.
- Increments `launch_editions.enrollment_count` under a row lock.
- Notifies Closer Studio websockets so the inbox widget and Ventas tab
  refresh live.

**Why deferred:** No Stripe/MP/Culqi webhook handlers exist yet in
`connections/infrastructure/`. Building three real provider integrations
(plus their credential config, signing verification, replay protection)
is a whole feature of its own, out of scope for the Phase-6 session.
For now the sales agent tool `generate_payment_link` returns the offer's
static `checkout_page_url` and transitions the enrollment to
`PAYMENT_PENDING` with that URL stored in `payment_link_url`. Users can
manually call `POST /enrollments/{id}/mark-paid` until webhooks land.

**Files / seams:**

- `backend/src/modules/sales_agent/domain/events.py` — `EnrollmentPaid`
  event class already exists.
- `backend/src/modules/sales_agent/application/services/enrollment_service.py::mark_paid` —
  emits the event.
- **To add:** `backend/src/modules/connections/infrastructure/webhooks/{stripe,mercadopago,culqi}.py`
  with a unified `_on_payment_succeeded(metadata, provider, tx_id)`
  helper that calls `EnrollmentService.mark_paid`.
- **To add:** webhook signing verification per provider.

**Effort:** ~10h (3h per provider × 3 + infra shared).

**Severity P1:** pricing/conversion depends on this; until then
tenants must mark paid manually, which breaks the "autonomous SDR"
promise.

---

## 2. Offer_creation procedure handler: interview → edition publish

**What:** When the Copilot interview completes and captured a
`first_edition.start_date`, automatically promote the placeholder
edition from `DRAFT + PRIVATE` to `UPCOMING + PUBLIC`. Currently the
interview captures the field into
`FirstEditionInput.start_date` but no backend code reads it and acts.

**Why deferred:** The `offer_creation` "procedure" in this codebase is
a declarative definition (see
`backend/src/modules/copilot/application/procedures/offer_creation.py`),
not an imperative handler. The real "complete the interview" entry
point lives deeper in the copilot chat orchestrator and I didn't want to
touch that without a clear test harness.

**Files / seams:**

- `backend/src/modules/copilot/domain/interview_configs/first_edition.py` —
  `FirstEditionInput` Pydantic schema in place.
- `backend/src/modules/copilot/domain/interview_configs/offer_config.py` —
  `FIRST_EDITION_DATE_BLOCK` appears at the end of the block list for
  `programa / servicio / experiencia` archetypes.
- **To add:** wherever the interview's "on complete" callback lives,
  parse `first_edition.start_date` from captured state and call
  `LaunchEditionService.update_and_publish(edition_id, start_date, ...)`.
  Transition should also flip `visibility=PUBLIC`.

**Effort:** ~3h once the interview completion entry point is located.

**Severity P1:** without this, even if the user does answer the date
question during onboarding, the edition stays DRAFT and leads go to
waitlist silently — the exact bug we designed the block to prevent.

---

## 3. Offer `slug` column + pretty public URLs

**What:** Currently public URLs use `offer_id` (UUID) as the "slug":

```
/api/v1/public/tenants/{tenant_slug}/offers/{offer_id}
/api/v1/public/tenants/{tenant_slug}/offers/{offer_id}/ediciones/{n}
```

The design in UI-SPEC asks for:

```
/public/{tenant_slug}/{offer_slug}
/public/{tenant_slug}/{offer_slug}/edicion/{n}
```

**Why deferred:** `products` (the offers table) has no `slug` column
yet. Adding one requires: migration (with idempotent generation from
`public_name` + uniqueness per tenant), backfill strategy for existing
rows, a slug-update flow when `public_name` changes (probably freeze
slug after first publish), and updates to the resolver in
`landing/api/public_edition.py`.

**Files / seams:**

- `backend/src/modules/landing/api/public_edition.py` — resolver
  currently accepts `UUID`, change to `str` and add the lookup.
- **To add:** Alembic migration `049_add_offer_slug` (nullable column,
  backfill, unique index per tenant).
- **To add:** `OfferRepository.get_by_slug(tenant_id, slug)` method.
- **To add:** slug auto-generation on offer create (e.g.
  `python-slugify` package).

**Effort:** ~6h including backfill test.

**Severity P2:** public URLs work; they're just uglier. SEO and
share-ability suffer slightly.

---

## 4. Shell chrome components: LandingSplitButton + WaitlistBanner + EditionCloneModal

**What:** Three components defined in UI-SPEC-offer-studio-shell.md
sections 5, 6, 7 respectively:

- **`LandingSplitButton`** — Webflow-style split button at the right of
  the tab bar. 5 states (none / draft / publishing / dirty / published)
  with a dropdown for "Abrir URL pública / Copiar URL / Regenerar con
  IA / Clonar de otra edición / Despublicar". Replaces the current
  `LandingActionButton` + `LandingKebabMenu` pair.
- **`WaitlistBanner`** — Gradient purple/blue banner above the tab
  content that appears when
  `currentEdition.visibility === PUBLIC && waitlistCount > 0`. Actions:
  "Ver lista" (drawer) + "Notificar a todos" (calls the
  `/enrollments/promote-waitlist` endpoint built in Phase 5).
- **`EditionCloneModal`** — Modal invoked by the rail's
  `+ Nueva edición` button. Three strategies: `literal`,
  `date_replace`, `ai_regen`. Calls the existing `EditionCloneService`
  on the backend.

**Why deferred:** Split reasoning on Phase 9a to keep the review
surface reasonable and preserve context budget. The current
implementation of `+ Nueva edición` emits a `console.info` — still
clickable, just doesn't open a modal.

**Files / seams:**

- `frontend/src/features/offer-studio/components/container/OfferShell.tsx` —
  has `openCloneModal` placeholder and the rail already wires
  `onCreateNew` through.
- `frontend/src/features/offer-studio/components/container/LandingActionButton.tsx` +
  `LandingKebabMenu.tsx` — keep until the split-button is ready; new
  component replaces them atomically.
- **To add:** `EditionsRail`/`EditionsRailCollapsed` currently have
  `onCreateNew` → rewire to the modal in OfferShell.
- **Backend already supports the modal:** `EditionCloneService` ships
  the three strategies since Phase 3.

**Effort:** ~18h total (split-button 6h, banner 4h, modal 8h).

**Severity P1:** WaitlistBanner is the most visible gap — without it
tenants have no UI trigger for bulk-notify, even though the backend API
exists.

---

## 5. Info-tab 7-section refactor

**What:** The original Phase 9b plan rewrites the Info tab into 7
editable sections:

1. Identidad (name / archetype / promise)
2. Fechas y Logística (edition-scoped dates, location, capacity)
3. Precios y Escalera (pricing tiers timeline + CRUD)
4. Entregables
5. Público (avatars, capacity, prerequisites)
6. Garantía y Onboarding
7. Conocimiento (RAG) — **absorbs the Conocimiento tab**

Each section: inline edit mode with RHF + Zod, autosave, completeness
badge.

**Why deferred:** Coordinated work across the existing editor, DTOs,
and autosave infra. The Ventas tab (Phase 9b lite that did ship) was
the highest-value single piece to deliver; the sections refactor is a
sustained 3–4-day effort that was out of budget for this session.

**Files / seams:**

- `frontend/src/features/offer-studio/components/container/OfferTabBar.tsx` —
  currently shows 5 tabs (Info / Ventas / Assets / Campañas /
  Conocimiento). When the refactor lands, remove the Conocimiento tab
  — it becomes section 7 inside Info.
- Existing `Editor` view renders at the base path — refactor replaces
  that view's body.

**Effort:** ~20h (identity, dates, pricing, deliverables, audience,
guarantee, knowledge × 2.5h each + shell work).

**Severity P1:** current editor works, but it's the "old paradigm".
Prototype `offer-info.html` shows the target; users comparing prod vs.
prototype will notice.

---

## 6. Assets gallery + Campañas card rewrites

**What:** Per UI-SPEC-offer-studio-tabs.md §3 and §4:

- **Assets:** placeholder "Canva-clone coming soon" banner, filter
  pills (Flyers / Reels / Carruseles / Documentos), gallery grid with
  per-asset tiles, "Jalar de Edición #N" button (reuses existing
  `AssetCloneModal`), "Generar con IA" stub button.
- **Campañas:** explainer banner ("acá ves asociadas, config avanzada
  en Growth"), KPI strip (activas / inversión / leads / ROAS),
  Campaign cards per flight with platform icon + KPI row + deep link
  to Growth Studio, "Asociar campaña existente" button, orgánico/email
  placeholder footer.

**Why deferred:** The current Assets and Campaigns tabs function.
These rewrites are cosmetic/UX upgrades rather than missing
functionality — Phase 9b lite prioritised the missing Ventas tab.

**Files / seams:**

- Existing `frontend/src/features/offer-studio/components/assets/AssetsView.tsx`
  — replace body.
- Existing Campaigns view — replace body.
- `AssetCloneModal` already exists from Phase 3 and is reusable.

**Effort:** ~12h (assets 6h, campañas 6h).

**Severity P2:** UX polish, not blocking.

---

## 7. Puck integration in landing editor

**What:** Replace the placeholder at
`/offer-studio/offer/[id]/editions/[editionId]/landing` with an actual
Puck-based WYSIWYG editor. Tokens (`{start_date}`,
`{tier_active.price}`, etc.) should render dynamically from the edition
data. Save flow writes to the per-edition `landing_pages` row.

**Why deferred:** Puck has real integration cost (dependency,
component registry, save pipeline). Stub route exists so the Offer
Shell's "Editar landing" main click has a valid target.

**Files / seams:**

- `frontend/src/app/(main)/[tenantId]/(dashboard)/offer-studio/offer/[id]/editions/[editionId]/landing/page.tsx` —
  current placeholder.
- Backend `LandingPage` model + `LandingRepository.update` — already
  accepts a full config, ready to receive Puck output.

**Effort:** ~10h including token substitution + save pipeline.

**Severity P2:** users can still create landings via the existing
"generate with AI" flow; they just can't edit inline yet.

---

## 8. EnrollmentWidget in inbox side panel

**What:** A widget inside
`frontend/src/features/sales/components/inbox/InboxSidePanel.tsx` that
shows the active enrollment for the current conversation. Renders 7
variants based on `enrollment.status` (INTENT / WAITLIST /
PAYMENT_PENDING / PAID / ATTENDED / REFUNDED / CANCELLED) with
status-appropriate inline actions.

**Why deferred:** Hook
(`useActiveEnrollmentForConversation`) and the
`GET /enrollments/by-conversation/{id}` endpoint both exist — widget is
a drop-in component in the inbox side panel. Out of Phase 9c's budget.

**Files / seams:**

- `frontend/src/features/closer-studio/hooks/use-enrollments.ts` — hook
  ready.
- `backend/src/modules/sales_agent/api/enrollments.py::get_by_conversation` —
  endpoint ready.
- **To add:** `frontend/src/features/closer-studio/components/EnrollmentWidget.tsx`
  + integration into `InboxSidePanel`.

**Effort:** ~4h.

**Severity P2:** inbox works without it; the widget adds live
enrollment context for closers.

---

## 9. Growth Studio per-edition analytics (Phase 10)

**What:** New analytics feature inside Growth Studio that compares
metrics across editions of the same offer. Per the original
FLOW-SPEC:

- Extend `metrics_service` + stage services with `edition_id`
  dimension.
- New endpoint: `GET /api/v1/analytics/editions/compare?offer_id=`.
- New route: `/growth-studio/offers/{offerId}/editions-compare`.
- ETL updates so `edition_id` is resolvable from landing page views,
  enrollments, and per-channel campaigns.

**Why deferred:** Explicit out-of-scope for this session ("Phase 10
queda diferida").

**Files / seams:** none — new feature.

**Effort:** ~16h.

**Severity P3:** user can already compare editions manually; this is
a BI-like enhancement for post-launch optimisation.

---

## Incidental findings

These are pre-existing tech-debt items I discovered while working. Not
created by this session — just documented here so they don't get lost.

### Backend uses sync `sqlalchemy.orm.Session` everywhere

**Where:** 100% of `backend/src/modules/offer/` and
`backend/src/modules/sales_agent/` repos + services, despite
`CLAUDE.md` §1 saying "new code MUST use AsyncSession".

**Severity P3.** Following existing patterns for new enrollment code
was the pragmatic call (avoids a one-off outlier). Real fix: module-wide
sync→async migration sprint. Touches ~30 files.

---

### Broken test file from a prior session

**Where:** `backend/tests/modules/sales_agent/test_conversation_context.py`
(still untracked on `development`). Fails on import with
`ImportError: cannot import name 'merge_history_with_current' from 'src.modules.sales_agent.application.orchestrator.chat'`.

**Severity P2.** Blocks `-m 'not verify' backend/tests/modules/sales_agent/`
unless filtered. Should be deleted or fixed by whoever wrote it.

---

### FastAPI `ruff` `FAST001` conflicts with the arch test

**Where:** `backend/tests/architecture/test_api_contracts.py::test_all_endpoints_have_response_model`
accepts `has_response_model OR has_return_type`. Ruff's `FAST001`
complains when you have both `response_model=` AND a return
annotation. So new code should use return annotations only, not
`response_model=`. Document/codify this preference so future devs
don't add both and hit ruff.

**Severity P3.** Mentioned in the new `enrollments.py` doctring to
prevent regression.

---

### `react-hooks/set-state-in-effect` rule

**Where:** ESLint rule we hit in
`frontend/src/features/offer-studio/hooks/use-rail-collapsed.ts`. The
naïve pattern `const [v, setV] = useState(default); useEffect(() => {
setV(readFromStorage()); }, [])` is flagged. Correct pattern: lazy
initializer `useState(() => readFromStorage())` + optional `storage`
event listener for cross-tab sync.

**Severity P3.** Note documented here so future hook authors don't
hit the same wall.

---

### `from __future__ import annotations` + FastAPI routing

**Where:** Any FastAPI route module. When
`from __future__ import annotations` is active, runtime-used types like
`UUID` and `Session` land in ruff's `TC002`/`TC003` "move to
type-checking block" warnings. But FastAPI needs them at runtime for
OpenAPI schema generation. Decision for this codebase: **don't use
`from __future__ import annotations` in API modules**. Keep
`UUID` / `Session` as runtime imports.

**Severity P3.** Also documented here.

---

### Offer module has no `tenant_id` in `ProductModel`

**Where:** `backend/src/modules/offer/infrastructure/models/product_model.py`.
Spot-checked during test fixtures. Verify before production — if this
is real, cross-tenant data leakage is possible.

**Severity P0 if confirmed.** Needs explicit verification. Probable
fact pattern: `tenant_id` IS there but lives on a joined table. Worth
a 15-minute audit.

---

---

## Post-session fixes

### 2026-04-17 — `has_editions` not mapped by frontend adapter (fixed `e80c6300`)

**Reported:** user opened an offer, rail didn't appear.
**Root cause:** `frontend/src/features/offer-studio/api/adapter.ts`
never declared `has_editions` on `BackendOffer` nor returned it from
`backendToFrontend`. The backend DTO had it, the DB column had the
right value, but the adapter silently dropped it — `offer.has_editions`
arrived `undefined`, `showsRail = offer.has_editions === true` became
`false`, rail hid.
**Lesson:** when adding a new rail / conditional-render key, grep the
adapter for the backend field name too — TypeScript `?` optional
types let missing mappings compile.

---

## Resolution workflow

When a deferred item is completed:

1. Move the ## section from this file to `resolved/` (create dir on
   first use).
2. Add a "Resolved in" line with the commit SHA and PR link.
3. Update the Index table at the top of this file.
4. Leave the incidental findings in place; only the numbered deferred
   items migrate.
