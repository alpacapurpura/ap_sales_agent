/**
 * Copilot sidebar width SSoT.
 *
 * All consumers (CopilotSidebar grid, useCopilotOffset, DashboardShell chrome
 * computation) MUST import widths from this module. No hardcoded numeric
 * literals (380/400/460/60/280/680) outside this file.
 *
 * AD6: drift fix — hook previously returned 380/60/0 while grid rendered
 * 460/680/60. This module resolves the drift.
 *
 * NOTE: T-2 will migrate existing consumers to these constants. T-1 only
 * creates the module (no consumers yet).
 */
export const COPILOT_WIDTHS = Object.freeze({
  /** Width when collapsed (rail only) — no chat panel */
  collapsed: 60,
  /** Rail column width in px */
  rail: 280,
  /** Chat panel width in px */
  chat: 400,
  /** Expanded full width: chat(400) + rail(60) */
  expanded: 460,
  /** Full history width: chat(400) + history(280) */
  max: 680,
} as const);

export type CopilotWidthKey = keyof typeof COPILOT_WIDTHS;
