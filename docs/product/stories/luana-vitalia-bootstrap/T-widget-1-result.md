# T-widget-1 Result — Vitalia Booking Widget (Vite UMD + postMessage)

**Ticket:** T-widget-1  
**Story:** luana-vitalia-bootstrap  
**Date:** 2026-05-14  
**Verdict:** PASS — A1 + A2 GREEN

---

## Validator Summary

| Validator | Criterion | Result |
|---|---|---|
| A1 | `dist/widget.umd.js` + `dist/widget.css` emitted by `vite build` | PASS — 594.84 kB UMD + 0.52 kB CSS |
| A2 | `createOriginValidator` blocks spoofed origins (8 edge cases) | PASS — 25/25 tests |

---

## Artifacts Produced

**luana-platform repo** (`vitalia/frontend/widget/`):

- `package.json` — `@luana/vitalia-booking-widget` workspace
- `tsconfig.json` — strict TS
- `vite.config.ts` — UMD lib build + Vitest/happy-dom
- `src/postmessage-protocol.ts` — typed WidgetMessage + protocol functions
- `src/lib/cn.ts` — lightweight cn() utility
- `src/styles.css` — scoped reset + brand tokens
- `src/components/BookingWidgetRoot.tsx` — 4-step state machine
- `src/components/CalendarSlotPicker.tsx` — slot grid
- `src/components/ConsentStep.tsx` — consent capture
- `src/components/PaymentStep.tsx` — payment redirect
- `src/components/SuccessStep.tsx` — booking confirmation
- `src/widget-entry.tsx` — UMD entry + autoMount
- `tests/setup.ts` — jest-dom matchers
- `tests/integration/booking-widget-flow.test.tsx` — 25 tests

**pnpm-workspace.yaml** — added `vitalia/frontend/widget` entry

---

## Notes for Next Ticket

T-widget-1 is the UMD bundle + postMessage protocol foundation. Downstream tickets that extend the widget (slot fetching with real backend, payment integration, consent API) can import from `@luana/vitalia-booking-widget` within the monorepo, or serve `dist/widget.umd.js` from CDN/static hosting.

Public API entry points:
- `window.VitaliaBookingWidget.mount(containerId?)` — manual mount
- Auto-mount on `DOMContentLoaded` if `#vitalia-booking-widget` present
- Named exports: `BookingWidgetRoot`, `CalendarSlotPicker`, `ConsentStep`, `PaymentStep`, `SuccessStep`, `postMessageToParent`, `createOriginValidator`, `isWidgetMessage`
