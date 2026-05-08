"use client";

import { COPILOT_WIDTHS } from "@/features/copilot/lib/copilot-shell-widths";
import { useCopilotStore } from "@/features/copilot/store/copilot-store";

import { useViewport } from "./use-viewport";

/**
 * @deprecated Use COPILOT_WIDTHS.expanded directly. Kept for 1 migration cycle.
 * Previously 380 — now aligned with SSoT (chat=400 + rail=60 = 460).
 */
export const COPILOT_OPEN_WIDTH = COPILOT_WIDTHS.expanded;

/**
 * @deprecated Use COPILOT_WIDTHS.collapsed directly. Kept for 1 migration cycle.
 */
export const COPILOT_RAIL_WIDTH = COPILOT_WIDTHS.collapsed;

/**
 * Returns the current copilot sidebar offset in pixels.
 * Consumes COPILOT_WIDTHS SSoT — no hardcoded literals.
 *
 * - Mobile                 → 0 (copilot renders as overlay, no offset)
 * - Desktop + collapsed    → COPILOT_WIDTHS.collapsed (60 — rail-only)
 * - Desktop + rail         → COPILOT_WIDTHS.expanded  (460 — chat + rail)
 * - Desktop + full         → COPILOT_WIDTHS.max       (680 — chat + history)
 */
export function useCopilotOffset(): number {
  const sidebarState = useCopilotStore((s) => s.sidebarState);
  const { isMobile } = useViewport();

  if (isMobile) return 0;

  switch (sidebarState) {
    case "rail":
      return COPILOT_WIDTHS.expanded;
    case "full":
      return COPILOT_WIDTHS.max;
    case "collapsed":
    default:
      return COPILOT_WIDTHS.collapsed;
  }
}
