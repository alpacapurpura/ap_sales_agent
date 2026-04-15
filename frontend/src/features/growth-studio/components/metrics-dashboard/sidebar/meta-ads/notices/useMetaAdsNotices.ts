"use client";

import { useMemo } from "react";

import {
  categoryToTab,
  maxSeverity,
  severityRank,
  type ImprovementNotice,
  type NoticeCategory,
  type NoticeSeverity,
  type NoticeTab,
  type NoticesSummary,
  type SeverityBreakdown,
} from "./types";
import { useIgnoredNotices } from "./useIgnoredNotices";

import type { CampaignPerformanceData, CampaignRecommendation } from "../../../../../types/metrics";
import type { MetaHealthCheck, Recommendation } from "../../../../../types/offer-association";

// ---------------------------------------------------------------------------
// Categorization
// ---------------------------------------------------------------------------

/**
 * Map Meta's native `recommendationType` to a Nicolify category.
 *
 * Matching is substring-based on an uppercased version so new Meta codes are
 * absorbed by intent (e.g. `CREATIVE_FATIGUE_TOP_PERFORMER` still lands under
 * creative). Unknown types fall back to `campaign` which is the safest default.
 */
export function categorizeMetaRec(recType: string): NoticeCategory {
  const t = (recType ?? "").toUpperCase();

  // Audience: overlap, saturation, frequency, reach expansion, detailed targeting.
  if (
    t.includes("AUDIENCE") ||
    t.includes("OVERLAP") ||
    t.includes("SATURATION") ||
    t.includes("FREQUENCY") ||
    t.includes("REACH_EXPANSION") ||
    t.includes("DETAILED_TARGETING")
  ) {
    return "audience";
  }

  // Creative: fatigue, CTR decline, creative diversity, ad creative issues.
  if (
    t.includes("CREATIVE") ||
    t.includes("AD_CREATIVE") ||
    t.includes("CTR_DROP") ||
    t.includes("FATIGUE")
  ) {
    return "creative";
  }

  // Cost: bid strategy, CPA/CPC/CPM guidance.
  if (
    t.includes("BID") ||
    t.includes("CPA") ||
    t.includes("CPC") ||
    t.includes("CPM") ||
    t.includes("COST_CAP")
  ) {
    return "cost";
  }

  // Default: campaign state, budget, delivery, learning, status issues.
  return "campaign";
}

/**
 * Structural Nicolify recommendations are all about campaign setup
 * (assign_offer, fix_objective, create_campaign, configure_pixel). They
 * belong to the Campañas tab.
 */
function categorizeStructuralRec(_rec: Recommendation): NoticeCategory {
  return "campaign";
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function importanceToSeverity(importance: string | null): NoticeSeverity {
  const upper = (importance ?? "").toUpperCase();
  if (upper === "CRITICAL") return "critical";
  if (upper === "HIGH") return "warning";
  return "info";
}

function makeEmptyBreakdown(): SeverityBreakdown {
  return { critical: 0, warning: 0, info: 0 };
}

function makeEmptyByTab<T>(factory: () => T): Record<NoticeTab, T> {
  return {
    campanas: factory(),
    creativos: factory(),
    audiencia: factory(),
    costos: factory(),
  };
}

function buildMetaNotice(
  rec: CampaignRecommendation,
  activeCampaignIds: Set<string>,
  nameById: Map<string, string>,
): ImprovementNotice | null {
  // Accept the rec if at least one of its object ids is an active campaign,
  // OR if the rec has no object ids at all (global recommendation).
  const activeIds = rec.objectIds.filter((id) => activeCampaignIds.has(id));
  if (rec.objectIds.length > 0 && activeIds.length === 0) return null;

  const targetId = activeIds[0] ?? null;
  const contextLabel = (() => {
    if (activeIds.length === 0) return null;
    if (activeIds.length === 1) {
      const name = nameById.get(activeIds[0]);
      return name ? `Campaña: ${name}` : `Campaña: ${activeIds[0]}`;
    }
    return `${activeIds.length} campañas`;
  })();

  // Stable id: source + type + sorted active ids. Keeps the same id across
  // refetches so ignore-state persists correctly.
  const id = `meta:${rec.recommendationType}:${[...activeIds].sort().join(",")}`;

  return {
    id,
    category: categorizeMetaRec(rec.recommendationType),
    severity: importanceToSeverity(rec.importance),
    title: rec.title ?? "Recomendación",
    body: rec.body,
    contextLabel,
    targetExternalId: targetId,
  };
}

function buildStructuralNotice(
  rec: Recommendation,
  health: MetaHealthCheck,
  activeCampaignIds: Set<string>,
  nameById: Map<string, string>,
): ImprovementNotice | null {
  // If the rec points to a specific target, that target must be active.
  if (rec.relatedTargetId) {
    const isActive = activeCampaignIds.has(rec.relatedTargetId);
    if (!isActive) {
      // Second chance: unassigned targets whose raw status is ACTIVE.
      const unassigned = health.unassignedTargets.find((t) => t.externalId === rec.relatedTargetId);
      const unassignedActive = unassigned && (unassigned.status ?? "").toUpperCase() === "ACTIVE";
      if (!unassignedActive) return null;
    }
  }

  // Context label: prefer campaign name, fall back to offer name.
  const contextLabel = (() => {
    if (rec.relatedTargetId) {
      const name =
        nameById.get(rec.relatedTargetId) ??
        health.activeCampaigns.find((c) => c.externalId === rec.relatedTargetId)?.name ??
        health.unassignedTargets.find((t) => t.externalId === rec.relatedTargetId)?.name;
      if (name) return `Campaña: ${name}`;
    }
    if (rec.relatedOfferId) {
      const offer = health.offersCoverage.find((o) => o.offerId === rec.relatedOfferId);
      if (offer) return `Offer: ${offer.offerName}`;
    }
    return null;
  })();

  const targetKey = rec.relatedTargetId ?? rec.relatedOfferId ?? "global";
  const id = `struct:${rec.type}:${targetKey}`;

  return {
    id,
    category: categorizeStructuralRec(rec),
    severity: rec.severity,
    title: rec.title,
    body: rec.body || null,
    contextLabel,
    targetExternalId: rec.relatedTargetId,
  };
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

interface UseMetaAdsNoticesArgs {
  campaignData: CampaignPerformanceData | undefined;
  healthCheck: MetaHealthCheck | undefined;
}

/**
 * Produce the unified improvement-notices view for the Meta Ads dashboard.
 *
 * Responsibilities:
 *   1. Filter to active campaigns only (paused/archived are noise).
 *   2. Categorize each rec into one tab (campanas / creativos / audiencia / costos).
 *   3. Merge structural + Meta recommendations.
 *   4. Deduplicate by stable id, keeping the highest severity.
 *   5. Apply the user's locally-ignored set (24h TTL).
 *   6. Return a per-tab breakdown + severity counts for the Resumen overview
 *      and the tab badges.
 */
export function useMetaAdsNotices({
  campaignData,
  healthCheck,
}: UseMetaAdsNoticesArgs): NoticesSummary {
  const { ignored } = useIgnoredNotices();

  return useMemo(() => {
    const activeCampaignIds = new Set(
      (campaignData?.campaigns ?? [])
        .filter((c) => (c.effectiveStatus ?? "").toUpperCase() === "ACTIVE")
        .map((c) => c.externalId),
    );

    const nameById = new Map<string, string>();
    for (const c of campaignData?.campaigns ?? []) {
      nameById.set(c.externalId, c.name);
    }

    const raw: ImprovementNotice[] = [];

    // Meta native recommendations.
    for (const rec of campaignData?.recommendations ?? []) {
      const notice = buildMetaNotice(rec, activeCampaignIds, nameById);
      if (notice) raw.push(notice);
    }

    // Nicolify structural recommendations.
    if (healthCheck) {
      for (const rec of healthCheck.recommendations) {
        const notice = buildStructuralNotice(rec, healthCheck, activeCampaignIds, nameById);
        if (notice) raw.push(notice);
      }
    }

    // Dedupe: on conflict, keep the more severe notice.
    const byId = new Map<string, ImprovementNotice>();
    for (const n of raw) {
      const existing = byId.get(n.id);
      if (!existing) {
        byId.set(n.id, n);
        continue;
      }
      if (severityRank(n.severity) < severityRank(existing.severity)) {
        byId.set(n.id, n);
      }
    }

    // Apply ignore filter.
    const visible = Array.from(byId.values()).filter((n) => !ignored.has(n.id));

    // Group by tab + sort by severity.
    const byTab = makeEmptyByTab<ImprovementNotice[]>(() => []);
    for (const notice of visible) {
      byTab[categoryToTab(notice.category)].push(notice);
    }
    for (const tab of Object.keys(byTab) as NoticeTab[]) {
      byTab[tab].sort((a, b) => severityRank(a.severity) - severityRank(b.severity));
    }

    // Severity breakdowns.
    const severity = makeEmptyBreakdown();
    const severityPerTab = makeEmptyByTab<SeverityBreakdown>(makeEmptyBreakdown);
    const maxSeverityPerTab: Record<NoticeTab, NoticeSeverity | null> = {
      campanas: null,
      creativos: null,
      audiencia: null,
      costos: null,
    };
    const perTabCounts: Record<NoticeTab, number> = {
      campanas: 0,
      creativos: 0,
      audiencia: 0,
      costos: 0,
    };

    for (const tab of Object.keys(byTab) as NoticeTab[]) {
      const items = byTab[tab];
      perTabCounts[tab] = items.length;
      for (const notice of items) {
        severity[notice.severity] += 1;
        severityPerTab[tab][notice.severity] += 1;
        maxSeverityPerTab[tab] = maxSeverity(maxSeverityPerTab[tab], notice.severity);
      }
    }

    return {
      byTab,
      total: visible.length,
      perTabCounts,
      severity,
      severityPerTab,
      maxSeverityPerTab,
    };
  }, [campaignData, healthCheck, ignored]);
}
