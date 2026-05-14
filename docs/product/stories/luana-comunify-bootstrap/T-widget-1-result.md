# T-widget-1 result.md

**State:** tests-passing
**Files modified:** 6 in `comunify/frontend/widget/`
**Tests:** Vitest 26/26 pass (widget unit tests in main suite)
**Validators:** V-NF-8 (widget UMD bundle), V-F-7 (postmessage protocol)

## What was built

Vite UMD bundle in `comunify/frontend/widget/`: `widget-entry.tsx` (React root mount/unmount via `window.ComunifyWidget.init()`), `SubscribeWidgetRoot.tsx` (3-step wizard: plan tier selection -> payment form -> success), `PlanTierStep.tsx` (renders plan tiers from API with price display), `PaymentStep.tsx` (credit card form stub with Stripe Elements placeholder), `SuccessStep.tsx` (confirmation screen with creator handle). `postmessage-protocol.ts` defines the type-safe postMessage contract between widget iframe and parent page (`PLAN_SELECTED`, `SUBSCRIBE_SUCCESS`, `WIDGET_CLOSE`). `vite.config.ts` builds as UMD library targeting `window.ComunifyWidget`. Bundle output: `widget/dist/comunify-widget.umd.js` + `comunify-widget.css`.

## Coverage notes

- Polish deferred to post-merge: Stripe Elements integration is a placeholder stub; real payment processing wired in T-payment-1
- Lint warnings (non-blocking): 0

## Acceptance

- [x] Vite UMD build config present in `widget/vite.config.ts`
- [x] `window.ComunifyWidget.init({ creatorHandle, containerId })` API defined
- [x] postmessage-protocol.ts exports typed message union
- [x] 3-step subscriber flow: plan -> payment -> success
- [x] Widget entry is self-contained (no shared Next.js app dependencies)
