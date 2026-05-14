# T-widget-1 Impl Log — Vitalia Booking Widget (Vite UMD + postMessage)

**Ticket:** T-widget-1  
**Story:** luana-vitalia-bootstrap  
**Date:** 2026-05-14  
**Status:** GREEN — both validators pass

---

## Skills Consulted

| Skill | Reason | Decision |
|---|---|---|
| `frontend-expert` | Widget is a standalone FE bundle; FSD-Lite + Vite UMD patterns needed | Vite `lib` mode, `format: "umd"`, React bundled (not external), `widget.umd.js` + `widget.css` output |
| `tessl__react-patterns` | All components need error/loading/empty states, accessible markup, stable keys | `aria-busy` on loading skeleton, `role="status"` on empty state, `aria-pressed` on slot buttons |
| `tessl__graceful-degradation` | API calls over public network (unauthenticated patient flow) | `AbortSignal.timeout(10_000)` on all fetch calls, error step on any API failure |
| `tessl__vitest` | Widget test environment setup (not Next.js) | `happy-dom`, `globals: true`, `@testing-library/jest-dom/matchers` via `expect.extend()` |

---

## Scope

Files created under `vitalia/frontend/widget/` in `luana-platform` repo:

| File | Purpose |
|---|---|
| `package.json` | `@luana/vitalia-booking-widget` workspace package |
| `tsconfig.json` | Strict TS, `jsx: react-jsx`, `types: ["vitest/globals"]` |
| `vite.config.ts` | UMD build + Vitest config (happy-dom) |
| `src/postmessage-protocol.ts` | Typed WidgetMessage union + `postMessageToParent()` + `createOriginValidator()` |
| `src/lib/cn.ts` | Lightweight class merger (no clsx — keeps bundle small) |
| `src/styles.css` | Scoped reset under `#vitalia-booking-widget` + brand CSS custom properties |
| `src/components/CalendarSlotPicker.tsx` | Slot grid with loading skeleton + empty state |
| `src/components/ConsentStep.tsx` | Scroll-to-end gate + accept checkbox + typed name input |
| `src/components/PaymentStep.tsx` | Payment redirect step (pre-generated Stripe checkout URL) |
| `src/components/SuccessStep.tsx` | Booking confirmation display |
| `src/components/BookingWidgetRoot.tsx` | State machine orchestrator + API calls + postMessage bridge |
| `src/widget-entry.tsx` | UMD entry: autoMount + manual `VitaliaBookingWidget.mount()` + named exports |
| `tests/setup.ts` | Vitest setup (jest-dom matchers) |
| `tests/integration/booking-widget-flow.test.tsx` | 25 integration tests (protocol + origin validator + component smokes) |

Also modified:
- `pnpm-workspace.yaml`: added `vitalia/frontend/widget` so pnpm resolves devDeps via workspace virtual store

---

## Validator Results

### A1 — Vite UMD build outputs widget.umd.js + widget.css

```
dist/widget.css              0.52 kB │ gzip:  0.32 kB
dist/widget.umd.js         594.84 kB │ gzip: 183.53 kB
built in 6.58s ✓
```

Status: **PASS**

### A2 — postMessage origin spoofing prevention

```
Test Files  1 passed (1)
Tests       25 passed (25)
Duration    ~870ms ✓
```

Key test groups:
- `createOriginValidator` — 8 tests covering: exact match allow, wildcard, block wrong origin, block trailing slash variant, block "null", block "", allow multiple listed origins, block http vs https
- `postMessageToParent` — 5 tests covering all 5 WidgetMessage types
- Component export smokes — 5 named export checks
- `CalendarSlotPicker` — 4 tests: renders slots, loading skeleton (`aria-busy`), `onSelectSlot` callback, empty state (`role="status"`)
- `ConsentStep` — 2 tests: renders consent text, `onBack` callback
- `SuccessStep` — 1 test: confirmation heading + bookingId rendered

---

## Key Design Decisions

### Standalone bundle (no Next.js, no Clerk)
Widget embeds in arbitrary clinic landing pages — cannot assume host app uses Next.js or has Clerk session. Patient is unauthenticated; API calls use short-lived signed patient JWT from URL param.

### React bundled into UMD (not external)
`rollupOptions.external` is empty — React is bundled. Clinic sites likely don't have React on page. Bundle weight (~595 kB pre-gzip / ~184 kB gzip) acceptable for an iframe load.

### postMessage typed union (D11)
`WidgetMessage` discriminated union forces type-safe event emission. `isWidgetMessage()` type guard used in parent-listening code. `createOriginValidator()` factory pattern: returns closure with O(1) origin lookup; supports literal `"*"` wildcard for dev/agnostic embeds.

### Origin validation logic
- `""` (empty string) → blocked (defensive)
- `"null"` (sandboxed frame) → blocked (cross-origin sandbox cannot be verified)
- Trailing slash variant → blocked (exact string match, not prefix)
- `http://` when only `https://` listed → blocked

### Consent scroll-to-end gate
Pattern mirrors `consent-signature-modal.tsx` from T-fe-3. `onScroll` on the markdown container: when `scrollHeight - scrollTop - clientHeight < 10` → `hasScrolledToEnd = true`. Accept checkbox and sign button stay disabled until gate is open.

### AbortSignal.timeout()
All API calls in `BookingWidgetRoot` use `AbortSignal.timeout(10_000)`. Timeout → moves to `error` step with Spanish neutro copy. No retry (single-attempt for booking creation — idempotency concern).

### Config resolution
1. URL params (iframe `src` query string): `offerId`, `clinicSlug`, `patientToken`, `parentOrigin`
2. DOM data attributes on mount container: `data-offer-id`, `data-clinic-slug`, etc.
URL params take precedence (set by embed snippet's iframe `src`).

---

## Parallel Safety

T-widget-1 scope: `vitalia/frontend/widget/` (new directory, disjoint from T-fe-4 scope at `vitalia/frontend/src/features/vitalia/components/`). No file overlap with parallel sessions.

---

## Issues Encountered

### pnpm workspace resolution
`@testing-library/jest-dom` subpath `@testing-library/jest-dom/matchers` failed to resolve in Vitest. Root cause: `vitalia/frontend/widget` not listed in `pnpm-workspace.yaml` → pnpm hadn't created symlinks in workspace virtual store. Fix: added entry to workspace, ran `pnpm install`.

### `/consentimiento/i` matcher ambiguity
`ConsentStep` renders "Consentimiento informado" (heading) AND "Acepto los términos del consentimiento" (checkbox label) — both match regex. Test changed to use unique `consentMarkdown="Texto legal exclusivo para la prueba."` → `screen.getByText(/texto legal exclusivo/i)`.
