/**
 * Improvement Notices — Meta Ads dashboard.
 *
 * A "notice" is an actionable item the user should look at. It replaces the
 * previous split between structural Nicolify recommendations and Meta's native
 * campaign recommendations: everything is normalized into a single list,
 * categorized by tab, filtered to active campaigns only, and deduped.
 *
 * Design goals:
 * - Non-technical user: one place per thing, no duplication.
 * - Only show items related to ACTIVE campaigns (paused/archived = noise).
 * - Dismissible for 24h via localStorage (see useIgnoredNotices).
 * - Each notice lives in exactly one tab; Resumen aggregates counts.
 */

export type NoticeCategory = 'campaign' | 'creative' | 'audience' | 'cost';

export type NoticeTab = 'campanas' | 'creativos' | 'audiencia' | 'costos';

export type NoticeSeverity = 'critical' | 'warning' | 'info';

export interface ImprovementNotice {
  /**
   * Stable id used for dedupe + ignore persistence.
   * Format: `{source}:{type}:{targetKey}`.
   */
  id: string;
  category: NoticeCategory;
  severity: NoticeSeverity;
  title: string;
  body: string | null;
  /** Short human-readable label identifying the object, e.g. "Campaña: Ventas PRO". */
  contextLabel: string | null;
  /** External id of the primary affected object (used for deep-link scroll). */
  targetExternalId: string | null;
}

export interface SeverityBreakdown {
  critical: number;
  warning: number;
  info: number;
}

export interface NoticesSummary {
  /** Notices grouped by destination tab. */
  byTab: Record<NoticeTab, ImprovementNotice[]>;
  /** Total visible notices (after ignore filter). */
  total: number;
  /** Total count per tab (same as byTab[tab].length, pre-computed for convenience). */
  perTabCounts: Record<NoticeTab, number>;
  /** Overall severity breakdown across all tabs. */
  severity: SeverityBreakdown;
  /** Severity breakdown per tab. */
  severityPerTab: Record<NoticeTab, SeverityBreakdown>;
  /** Highest severity found in each tab (null if no notices). */
  maxSeverityPerTab: Record<NoticeTab, NoticeSeverity | null>;
}

/** Map a notice category → its destination tab. */
export function categoryToTab(category: NoticeCategory): NoticeTab {
  switch (category) {
    case 'campaign':
      return 'campanas';
    case 'creative':
      return 'creativos';
    case 'audience':
      return 'audiencia';
    case 'cost':
      return 'costos';
  }
}

/** Ranking used to sort/compare severities. Lower number = more severe. */
export function severityRank(severity: NoticeSeverity): number {
  switch (severity) {
    case 'critical':
      return 0;
    case 'warning':
      return 1;
    case 'info':
      return 2;
  }
}

/** Return the most severe of two severity values. */
export function maxSeverity(
  a: NoticeSeverity | null,
  b: NoticeSeverity | null,
): NoticeSeverity | null {
  if (a == null) return b;
  if (b == null) return a;
  return severityRank(a) < severityRank(b) ? a : b;
}
