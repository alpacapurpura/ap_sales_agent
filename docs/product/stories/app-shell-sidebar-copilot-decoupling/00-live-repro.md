# Live Repro — App Shell sidebar + copilot overlap (2026-05-07)

> Read-only verification with Chrome DevTools MCP. No source code modified.

## Environment

- URL: `https://dev-app.nicolify.com/6347e21e-8112-4aa1-80d3-6adaa73bf6f9/...` (NOT `localhost:3000` — the existing MCP browser session was already authenticated against the dev cloud preview environment, which renders the same app shell as local dev. Findings apply 1:1 because the shell components — `AppSidebar`, `CopilotSidebar`, `DashboardLayoutClient` — are the same code paths.)
- Browser: Chrome (DevTools MCP). Min enforced viewport width = 500px.
- Clerk: signed-in as `christian.revilla.m@gmail.com`, tenant `Visionarias` (`6347e21e-...`).
- Date: 2026-05-07.
- Console: zero errors, zero warnings during the entire sweep.

## Methodology

Coverage matrix swept in the live tab (resize → navigate → DOM probe → screenshot):

- Viewports tested: 1920×945 (desktop XL), 1440×900 (laptop), 1024×800 (md/tablet large), 768×800 (sm/tablet), 500×800 (mobile — MCP browser min-width).
- Studios visited: `offer-studio`, `brand-studio/identity`, `growth-studio/atraccion-captura`, `sales/studio/inbox`, `settings/general`.
- Copilot states observed: `full` (chat 400 + history 280), `rail` (chat 400 + rail 60 = the default "open" state we observed), `collapsed` (rail 60 only; mobile = translated off-screen).
- AppSidebar states observed: expanded `w-64` (256px), collapsed `w-20` (80px), hidden (`md:flex` breakpoint, viewport < 768px).

For each combination: bounding rectangles via `getBoundingClientRect()`, computed style for `position`/`zIndex`/`width`/`marginLeft`, viewport `innerWidth`, document `scrollWidth`, programmatic overlap detection, screenshot, snapshot of accessibility tree.

## Findings table (overlap and content squeeze per cell)

Overlap = horizontal pixel overlap between AppSidebar rect and CopilotSidebar rect (or copilot vs main). "Squeeze" = main content column width when copilot is open.

| Viewport | Studio | Sidebar | Copilot | Overlap (px) | Main width | z AppSidebar | z Copilot | Verdict | Screenshot |
|---|---|---|---|---|---|---|---|---|---|
| 1920×945 | offer-studio | expanded 256 | open 460 | 0 | 1204 | 50 (fixed) | auto (static) | OK | `1920-offer-studio-copilot-open.png` |
| 1920×945 | sales/inbox | expanded 256 | open 460 | 0 | 1204 | 50 | auto | OK | `1920-sales-inbox-copilot-open.png` |
| 1440×900 | offer-studio | auto-collapsed 80 | open 460 | 0 | 900 | 50 | auto | OK | `1440-offer-studio-copilot-open.png` |
| 1024×800 | offer-studio | collapsed 80 | open 460 | 0 | 484 | 50 | auto | DEGRADED — content cramped, "Nueva Oferta" CTA truncated | `1024-offer-studio-copilot-open.png` |
| 1024×800 | offer-studio | EXPANDED 256 | open 460 | 0 | 308 | 50 | auto | BROKEN — "+ Nue..." button cut, ladder cards wrap to 5 chars/line, horizontal scroll inside cards | `1024-offer-studio-sidebar-expanded-copilot-open.png` |
| 1024×800 | sales/inbox | collapsed 80 | open 460 | 0 | 484 | 50 | auto | BROKEN — filters truncated ("Manua..."), lead detail truncated ("Brenda Pasto...", "creaci..."), conversation pane invisible | `1024-sales-inbox-copilot-open.png` |
| 1024×800 | settings | collapsed 80 | open 460 | 0 | 484 | 50 | auto | DEGRADED — settings sub-nav + form competing for 484px | `1024-settings-copilot-open.png` |
| 768×800 | offer-studio | EXPANDED 256 | open 460 | 0 | **52** | 50 | auto | CATASTROPHIC — main is a 52px sliver showing only "O" of "Offer Studio" + vertical scrollbar | `768-offer-studio-copilot-open.png` |
| 768×800 | offer-studio | EXPANDED 256 | rail 60 | 0 | 452 | 50 | auto | OK with copilot rail | `768-offer-studio-copilot-rail.png` |
| 768×800 | brand-studio | collapsed 80 | open 460 | 0 | 228 | 50 | auto | BROKEN — form inputs truncated, sub-nav unusable | `768-brand-studio-copilot-open.png` |
| 768×800 | growth-studio | collapsed 80 | open 460 | 0 | 228 | 50 | auto | BROKEN — chart and KPIs crushed | `768-growth-studio-copilot-open.png` |
| 500×800 | settings | hidden (md:flex) | open 460 (mobile drawer) | n/a | 500 covered by drawer | n/a | 50 | OK — backdrop + translate-x correct mobile drawer pattern | `500-settings-copilot-open-mobile.png` |
| 500×800 | offer-studio | hidden | open 460 | n/a | 500 covered | n/a | 50 | OK — same drawer pattern | `500-offer-studio-copilot-open.png` |
| 500×800 | settings | hidden | closed (translate-x-full) | n/a | 500 free | n/a | 50 (off-screen) | OK — but no FAB to reopen copilot from main view | `500-settings-copilot-closed-mobile.png` |

Key numerical evidence (from `evaluate_script`):

- `appSidebar.computed`: `position: fixed`, `zIndex: 50`, `width: 80px|256px` (toggled via `isCollapsed`), `inset-y-0 left-0`.
- `copilot.computed` (desktop ≥768): `position: static`, `zIndex: auto`, in flex flow.
- `copilot.computed` (mobile <768): `position: fixed`, `zIndex: 50`, `right: 0`, with `translate-x-0|translate-x-full`.
- `copilot.gridTemplateColumns` (rail open default): `0px 60px` collapsed | `400px 60px` rail | `400px 280px` full.
- `main.marginLeft`: `80px` (collapsed sidebar) | `256px` (expanded) — manually compensated; main does NOT compensate copilot width.
- `appSidebar_vs_copilot_overlap`: 0 across every cell (they never collide horizontally).
- `appSidebar_vs_main_overlap`: 0 (main margin-left compensates).

## Root cause analysis

**Hypothesis from task: confirmed.** AppSidebar does NOT consume `useCopilotOffset`. Verified by `grep -n "useCopilotOffset" frontend/src/components/shared/layout/AppSidebar.tsx` → 0 matches. The hook IS imported and used in `components/ui/{dialog,sheet,alert-dialog,detail-panel}.tsx`, but the shell sidebar itself is offset-blind. There is even an arch fitness test (`frontend/src/__tests__/architecture/test-growth-studio-copilot-offset.test.ts`) enforcing the contract for growth-studio fixed/portal elements — but the contract was never extended to the global shell.

**The actual visual bug is NOT a Z-index overlap.** AppSidebar (`fixed inset-y-0 z-50`) and CopilotSidebar (desktop: `position: static` in flex flow; mobile: `fixed z-50 right-0 translate-x-0`) never share horizontal pixels — overlap area is 0 px in every measured cell. The bug is **content area starvation** caused by the layout in `frontend/src/app/(main)/[tenantId]/(dashboard)/DashboardLayoutClient.tsx`:

```tsx
<div className="flex h-screen overflow-hidden">
  <AppSidebar />                                    // fixed, 80 or 256 px
  <main className="flex-1 min-w-0 ... md:ml-20 | md:ml-64">  // manually compensates AppSidebar
    {children}
  </main>
  <CopilotSidebar />                                // 60 or 460 or 680 px in flex flow
</div>
```

Three load-bearing issues:

1. **`main` is `flex-1 min-w-0`** so it absorbs every pixel `CopilotSidebar` consumes from the row — there is no minimum-width floor and no breakpoint that automatically collapses copilot to rail when the studio cannot afford 460px. Result: at 768×800 with sidebar expanded + copilot open, main is reduced to **52px** wide.
2. **`AppSidebar.isCollapsed` and `CopilotStore.isOpen` are independent** — the shell does not know that opening copilot at small viewports should auto-collapse the nav, or vice versa. There is no mutex policy.
3. **`useCopilotOffset` hook returns 380/60/0**, but the actual rendered copilot grid is 460 (rail) / 680 (full) / 60 (collapsed). The hook is **80–220px out of date** with `CopilotSidebar.tsx` lines 86–87 (`chatW = "400px"`, `railOrHistoryW = "60px"|"280px"`). Every modal/sheet that consumes the hook centers itself with the wrong offset.

**Z-index strategy:** AppSidebar `z-50`, copilot mobile drawer `z-50`, copilot mobile backdrop `z-40`, modals `z-50+`. They tie at the same layer with no documented ordering. Visible side effect: on mobile, the copilot drawer (z-50) covers the full viewport without being above any other shell element (AppSidebar is `display:none` at this breakpoint), so it renders correctly — but the policy is implicit, not enforced.

**Mobile behavior (≤640):** AppSidebar uses `md:flex` so it is `display:none` below 768px breakpoint. A separate mobile topbar (64px tall, `md:hidden fixed`) provides the hamburger. CopilotSidebar at the same breakpoint uses `max-md:fixed inset-y-0 right-0 z-50 translate-x-0|full` — proper drawer pattern with backdrop scrim (`bg-black/40 backdrop-blur-sm md:hidden`). Drawer pattern is sound. **However:**
- AppSidebar mobile drawer (off-canvas from the left) is missing — only the topbar hamburger exists (40px button, no `aria-label` — observed empty label in `take_snapshot`).
- When copilot is mobile-open, AppSidebar is completely inaccessible (the topbar hamburger is z-50 sits behind the copilot drawer at z-50). Tested by stacking order via document order: copilot is rendered AFTER topbar in `DashboardLayoutClient`, so it wins.
- There is no FAB / persistent affordance to re-open copilot once dismissed at mobile (only path: scroll in some studio views to find the rail trigger, or rely on routes that auto-rail).

## Specs primer (raw evidence for /po-ux)

**Critical scenarios visible during the sweep:**

1. **Tablet 768 × sidebar expanded + copilot open**: main = 52px. App is unusable. (Sales studio at 1024 hits the same class of issue at 484px main: filters/lead detail/conversation pane all truncated; conversation thread is invisible.)
2. **Laptop 1024 × sidebar expanded + copilot open**: ladder cards in offer-studio collapse to 5 chars/line, primary CTA cut to "+ Nue".
3. **Cross-studio**: offer / brand / growth / sales / settings all degrade at the same viewport thresholds → not a per-studio bug, it's a shell bug.
4. **`useCopilotOffset` is wrong by 80–220px**: every dialog / sheet / detail-panel positioned with the hook is mis-centered. (No screenshot — would require opening a modal in a mid-viewport. Source-confirmed by reading `use-copilot-offset.ts:7,28-29` vs `CopilotSidebar.tsx:86-87`.)
5. **Mobile**: no left-side drawer for AppSidebar (only the unlabeled 40px topbar trigger), no FAB to summon copilot, no mutex between the two.
6. **Sales studio inbox at 1024**: lead-detail right pane shows lifecycle ("subscriber") but the conversation thread itself is gone — the inbox is a 3-column inner layout (list / detail / chat) on top of the global shell; effectively 5 columns competing for 484px = 96px each. (Not a copilot-only bug, but copilot makes it acute.)

**Acceptance criteria suggested:**

- Given any studio route, when viewport ≥ 1024 and copilot is `open` (rail+chat), then main content width MUST be ≥ 720px (read-comfort floor). Achieved via either (a) auto-collapse AppSidebar to rail, (b) auto-collapse copilot to rail, or (c) refuse to allow both expanded.
- Given any studio route, when viewport < 1024 and copilot is opened, then AppSidebar MUST collapse to its rail (80px) automatically; reopening AppSidebar to expanded SHOULD auto-collapse copilot (mutex pattern).
- Given any studio route, when viewport < 768, then copilot MUST be a fixed drawer (already correct), AppSidebar MUST be a fixed drawer (currently missing — only topbar exists), backdrop MUST appear when either drawer is open, and the two drawers MUST be mutually exclusive (cannot both be open).
- `useCopilotOffset` MUST agree with `CopilotSidebar` width constants. SSoT one of them; ratchet the other. (Sub-acceptance: arch fitness test extended from growth-studio scope to `components/shared/layout/**` so AppSidebar enforcement is mechanical.)
- Z-index ladder MUST be documented and tested: shell drawers (50) > shell topbar (40) > floating modals (60) > toasts (70). One ratchet test enforces the constants.
- Sales studio inbox columns MUST collapse responsively independent of the global shell (currently fixed-width inner cols).
- No horizontal page scroll at any viewport ≥ 500px in any studio with default state (sidebar collapsed, copilot rail).

**Out-of-scope spike candidates** (worth flagging to /pm but not this story):

- Sales studio inner 3-col responsive behavior (separate story).
- Growth Studio drawer/bowtie pattern already has `useCopilotOffset` arch test — extend the same enforcement upward to the shell.
- Mobile FAB for copilot (UX gap, not a regression — pre-existing).

## Screenshots saved at

`/tmp/live-repro/sidebar-copilot/` (14 PNG files):

- `1920-offer-studio-copilot-open.png`
- `1920-sales-inbox-copilot-open.png`
- `1440-offer-studio-copilot-open.png`
- `1024-offer-studio-copilot-open.png`
- `1024-offer-studio-sidebar-expanded-copilot-open.png` ← worst-case 1024
- `1024-sales-inbox-copilot-open.png` ← sales unusable
- `1024-settings-copilot-open.png`
- `768-offer-studio-copilot-open.png` ← catastrophic 52px main
- `768-offer-studio-copilot-rail.png` ← compare with rail
- `768-brand-studio-copilot-open.png`
- `768-growth-studio-copilot-open.png`
- `500-offer-studio-copilot-open.png`
- `500-settings-copilot-open-mobile.png` ← drawer + backdrop
- `500-settings-copilot-closed-mobile.png` ← topbar hamburger visible

## Source citations (for /po-ux + /architect)

- AppSidebar (no `useCopilotOffset` consumption): `/home/chris/AISALESHT/frontend/src/components/shared/layout/AppSidebar.tsx:650-664`
- CopilotSidebar (grid widths): `/home/chris/AISALESHT/frontend/src/features/copilot/components/CopilotSidebar.tsx:86-87,117-148`
- DashboardLayoutClient (root layout): `/home/chris/AISALESHT/frontend/src/app/(main)/[tenantId]/(dashboard)/DashboardLayoutClient.tsx:19-38`
- useCopilotOffset hook (drift vs reality): `/home/chris/AISALESHT/frontend/src/hooks/use-copilot-offset.ts:7-30`
- Existing arch test (growth-studio scope only — extend to shell): `/home/chris/AISALESHT/frontend/src/__tests__/architecture/test-growth-studio-copilot-offset.test.ts:1-110`

## Blockers encountered

- MCP browser enforces a minimum viewport width of ~500px; could not test true 375px iPhone-class viewport. The 500px findings still validate the mobile drawer behavior because the relevant breakpoint (`md` = 768px) is well above 500.
- Localhost:3000 was unreachable from the MCP browser session (it was already attached to the cloud dev preview); since the rendered code is identical (same Next build output, same `DashboardLayoutClient`, same `AppSidebar` and `CopilotSidebar` source), this is not a fidelity issue.
- The "Expandir/Ocultar menú" button has the magic comment-free label "Expandir menú" / "Ocultar menú" but the mobile topbar hamburger has no `aria-label` (`take_snapshot` showed empty label, `evaluate_script` confirmed `aria-label` null). Worth flagging in spec but not the focus of this repro.
