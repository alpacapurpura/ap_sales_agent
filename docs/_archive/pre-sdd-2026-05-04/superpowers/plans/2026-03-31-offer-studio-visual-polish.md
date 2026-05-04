# Plan: Offer Studio Visual Polish

**Status:** APPROVED - Ready to implement
**Preview:** `/tmp/offer-studio-preview.html` (approved by user)
**Date:** 2026-03-31

## Files to Modify

| File | Path |
|---|---|
| offer-studio-dashboard.tsx | `frontend/src/features/offer-studio/components/dashboard/offer-studio-dashboard.tsx` |
| offer-ladder-layout.tsx | `frontend/src/features/offer-studio/components/dashboard/offer-ladder-layout.tsx` |
| lead-magnet-stream-card.tsx | `frontend/src/features/offer-studio/components/dashboard/lead-magnet-stream-card.tsx` |
| ladder-progress-bar.tsx | `frontend/src/features/offer-studio/components/dashboard/ladder-progress-bar.tsx` |
| OfferStudioView.tsx | `frontend/src/features/offer-studio/components/dashboard/OfferStudioView.tsx` |

## Changes

### Change 1: Remove OfferLegend from render
**File:** `offer-studio-dashboard.tsx`
**What:** Remove `<OfferLegend />` from line 233 render. Keep the import and file (don't delete offer-legend.tsx).
**Why:** Delivery model is already encoded in each card (border-top color + DIY/DWY/DFY badge). Legend is redundant visual noise.

### Change 2: Remove duplicate header inside columns
**File:** `offer-ladder-layout.tsx`
**What:**
- `renderLevelGroup()` (lines 17-47) renders a header with `Icon + title + [+] button`. But the column wrapping it ALREADY has a header with `Icon + title + description` (lines 57-65).
- **Fix:** Remove the header from `renderLevelGroup` — it should only render the list of cards + AddOfferCard.
- Move the `[+]` button to the column header (next to the h3 title). Use a small bordered button style: `h-7 w-7 rounded-md border border-border`.
- Update column header divs to use `flex items-start justify-between` layout.
**Impact:** Eliminates triple repetition of "Activacion" / "Transformacion" / "Maximizacion".

### Change 3: Improve Lead Magnet section
**File:** `offer-studio-dashboard.tsx` (lines 270-326) + `lead-magnet-stream-card.tsx`

**In offer-studio-dashboard.tsx:**
- Replace `ScrollArea` + `grid-rows-2 grid-flow-col` horizontal scroll with responsive grid: `grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3`
- Remove `w-[280px]` wrappers around cards
- Add subtle gradient background to section: `style={{ background: 'linear-gradient(135deg, ...)' }}` or use Tailwind classes
- Change add-button slot height from 72px to 80px
- Remove `ScrollBar` component

**In lead-magnet-stream-card.tsx:**
- Change card height from `h-[72px]` to `h-[80px]`
- Remove fixed `w-[280px]` — let it be `w-full` (grid controls width now)
- Add price display below the name:
  ```tsx
  const priceDisplay = offer.pricing && offer.pricing.length > 0
    ? new Intl.NumberFormat('en-US', { style: 'currency', currency: offer.currency || 'USD' }).format(offer.pricing[0].total_amount)
    : "Gratis";

  // In render, after the h4 name:
  <span className={cn(
    "text-[11px] font-medium mt-0.5",
    priceDisplay === "Gratis" ? "text-emerald-400" : "text-amber-400"
  )}>
    {priceDisplay}
  </span>
  ```

### Change 4: Compact LadderProgressBar in header
**File:** `ladder-progress-bar.tsx` + `OfferStudioView.tsx` + `offer-studio-dashboard.tsx`

**In ladder-progress-bar.tsx:**
- Add a `compact?: boolean` prop
- When `compact=true`: render only the 5 circles + connecting lines + percentage in a single horizontal row. No labels, no "Escalera de Valor" text. Wrapped in `hidden lg:flex items-center gap-2 px-3 py-1.5 bg-muted/50 rounded-lg border border-border/50`.
- When `compact=false` (default): keep current render unchanged (backward compat).

**In OfferStudioView.tsx:**
- Import `LadderProgressBar` and `computeLadderCompleteness`
- Need access to offers data — either lift state up or pass ladderCompleteness as a prop.
- Simpler approach: Add a callback/render prop pattern OR move the progress bar rendering to OfferStudioView by accepting `ladderCompleteness` from the dashboard via a callback.
- **Recommended approach:** Add an `onLadderComputed` callback prop to `OfferStudioDashboard` that passes `ladderCompleteness` up. Then render `<LadderProgressBar compact />` in the header.

**In offer-studio-dashboard.tsx:**
- Remove the `<LadderProgressBar>` from the dashboard render (lines 236-242)
- Add `onLadderComputed?: (data: { filledGroups: Set<OfferValueLevel>; score: string; percentage: number }) => void` prop
- Call `onLadderComputed(ladderCompleteness)` via useEffect when ladderCompleteness changes

### Change 5: Small spacing and hierarchy adjustments
**File:** `offer-studio-dashboard.tsx` + `offer-card.tsx`

**In offer-studio-dashboard.tsx:**
- Change `space-y-10` to `space-y-8` (line 231)

**In offer-card.tsx:**
- Add `hover:scale-[1.01]` to the Card className (line 101, in the `cn()` call)

## Verification

```bash
docker exec -t visionarias_client_dev npx tsc --noEmit
```

Visual check in dev environment after implementation.
