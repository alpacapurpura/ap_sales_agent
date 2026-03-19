---
phase: quick
plan: 260319-gnj
subsystem: frontend/brand
tags: [ux, loading-state, visual-identity, progress-feedback]
dependency_graph:
  requires: [brand-visuals-wizard, smart-fill-dialog-pattern]
  provides: [visual-scan-processing-state]
  affects: [brand-studio-visual-dna]
tech_stack:
  patterns: [asymptotic-progress-simulation, stage-message-timeline, dialog-dismissal-lock]
key_files:
  modified:
    - frontend/src/features/brand/sections/visuals/brand-visuals-wizard.tsx
decisions:
  - Palette icon used instead of Wand2 to match visual extraction theme
  - 1 minute time estimate (vs 3 minutes in SmartFill) since visual extraction is faster
  - Stage timeouts cleaned up on both success and error paths to prevent stale updates
metrics:
  duration: 2min
  completed: "2026-03-19T17:04:09Z"
---

# Quick Task 260319-gnj: Add Loading Spinner and Progress Feedback to Visual DNA Web Scan

Full-screen processing state with animated spinner, asymptotic progress bar, and visual-extraction-specific stage messages in BrandVisualsWizard, matching SmartFillDialog UX pattern.

## What Changed

### Task 1: Add processing state with spinner, progress bar, and stage messages

**Commit:** aa4fd41

Added comprehensive processing feedback to the Visual DNA web scan dialog:

1. **State variables:** Added `progress`, `stage`, and `errorState` alongside existing `analyzing` state
2. **Asymptotic progress simulation:** `setInterval` every 800ms with formula `Math.min(prev + Math.max(0.5, (90 - prev) / 50), 90)` -- identical to SmartFillDialog
3. **Stage messages** specific to visual extraction (2s-24s timeline): scanning web, analyzing colors, detecting fonts, extracting design style, generating usage rules
4. **Processing UI:** Centered full-screen state with animated circular spinner (border-spin), Palette icon pulsing, progress bar, and time estimate text
5. **Error state UI:** Alert component with timeout vs generic detection, retry button
6. **Dialog lock:** `onOpenChange` no-op when `analyzing` is true; `onInteractOutside` already prevented

## Deviations from Plan

None - plan executed exactly as written.

## Verification

- TypeScript compilation: PASSED (0 errors in brand-visuals-wizard.tsx; 2 pre-existing errors in brand-studio-layout.tsx unrelated)
- All done criteria met: spinner, progress bar, stage messages, error state with retry, dialog lock, preview transition preserved

## Self-Check

Verified below.
