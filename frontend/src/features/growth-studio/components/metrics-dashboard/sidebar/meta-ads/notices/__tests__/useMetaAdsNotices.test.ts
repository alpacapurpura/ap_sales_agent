import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type {
  CampaignPerformanceData,
  CampaignRecommendation,
  CampaignWithMetrics,
} from "../../../../../../types/metrics";
import type { MetaHealthCheck, Recommendation } from "../../../../../../types/offer-association";
import { useMetaAdsNotices } from "../useMetaAdsNotices";

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

function makeCampaign(overrides: Partial<CampaignWithMetrics> = {}): CampaignWithMetrics {
  return {
    externalId: "c1",
    name: "Campaña Activa 1",
    objective: "OUTCOME_SALES",
    status: "ACTIVE",
    effectiveStatus: "ACTIVE",
    dailyBudget: 20,
    lifetimeBudget: null,
    budgetRemaining: 10,
    startTime: "2026-04-01T00:00:00Z",
    stopTime: null,
    adSetsCount: 1,
    adsCount: 2,
    metrics: {
      spend: 100,
      impressions: 1000,
      reach: 800,
      frequency: 1.25,
      clicks: 50,
      ctr: 5,
      cpc: 2,
      cpm: 100,
      conversions: 10,
      cpa: 10,
      roas: 2,
    },
    health: "good",
    ...overrides,
  };
}

function makeRec(overrides: Partial<CampaignRecommendation> = {}): CampaignRecommendation {
  return {
    recommendationType: "CAMPAIGN_BUDGET_LEARNINGS",
    source: "META",
    title: "Tu campaña está aprendiendo",
    body: "Evita cambios grandes en presupuesto.",
    importance: "HIGH",
    liftEstimate: null,
    opportunityScore: null,
    url: null,
    objectIds: ["c1"],
    ...overrides,
  };
}

function makeStructuralRec(overrides: Partial<Recommendation> = {}): Recommendation {
  return {
    type: "assign_offer",
    severity: "warning",
    title: "Asigna tu campaña a un offer",
    body: "Para poder medir el ROAS por offer.",
    actionLabel: "Asignar",
    actionUrl: null,
    relatedOfferId: null,
    relatedTargetId: "c1",
    ...overrides,
  };
}

function makeCampaignData(
  overrides: Partial<CampaignPerformanceData> = {},
): CampaignPerformanceData {
  return {
    campaigns: [makeCampaign()],
    recommendations: [],
    totalCampaigns: 1,
    activeCampaigns: 1,
    currency: "USD",
    lastSynced: "2026-04-10T15:00:00Z",
    ...overrides,
  };
}

function makeHealthCheck(overrides: Partial<MetaHealthCheck> = {}): MetaHealthCheck {
  return {
    overallStatus: "healthy",
    activeCampaigns: [],
    offersCoverage: [],
    unassignedTargets: [],
    recommendations: [],
    summaryText: "",
    ...overrides,
  };
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("useMetaAdsNotices", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it("returns an empty summary when there is no data at all", () => {
    const { result } = renderHook(() =>
      useMetaAdsNotices({ campaignData: undefined, healthCheck: undefined }),
    );

    expect(result.current.total).toBe(0);
    expect(result.current.byTab.campanas).toEqual([]);
    expect(result.current.byTab.creativos).toEqual([]);
    expect(result.current.byTab.audiencia).toEqual([]);
    expect(result.current.byTab.costos).toEqual([]);
  });

  it('maps a Meta campaign recommendation to the "campanas" tab', () => {
    const campaignData = makeCampaignData({
      recommendations: [
        makeRec({
          recommendationType: "CAMPAIGN_BUDGET_LEARNINGS",
          objectIds: ["c1"],
          importance: "HIGH",
        }),
      ],
    });

    const { result } = renderHook(() =>
      useMetaAdsNotices({ campaignData, healthCheck: undefined }),
    );

    expect(result.current.total).toBe(1);
    expect(result.current.byTab.campanas).toHaveLength(1);
    expect(result.current.byTab.campanas[0].severity).toBe("warning");
    expect(result.current.byTab.campanas[0].category).toBe("campaign");
    expect(result.current.byTab.campanas[0].contextLabel).toContain("Campaña Activa 1");
  });

  it('categorizes creative fatigue recommendations to "creativos"', () => {
    const campaignData = makeCampaignData({
      recommendations: [makeRec({ recommendationType: "CREATIVE_FATIGUE", objectIds: ["c1"] })],
    });

    const { result } = renderHook(() =>
      useMetaAdsNotices({ campaignData, healthCheck: undefined }),
    );

    expect(result.current.byTab.creativos).toHaveLength(1);
    expect(result.current.byTab.campanas).toHaveLength(0);
  });

  it('categorizes audience recommendations to "audiencia"', () => {
    const campaignData = makeCampaignData({
      recommendations: [makeRec({ recommendationType: "AUDIENCE_OVERLAP", objectIds: ["c1"] })],
    });

    const { result } = renderHook(() =>
      useMetaAdsNotices({ campaignData, healthCheck: undefined }),
    );

    expect(result.current.byTab.audiencia).toHaveLength(1);
  });

  it('categorizes bid/cost recommendations to "costos"', () => {
    const campaignData = makeCampaignData({
      recommendations: [makeRec({ recommendationType: "BID_STRATEGY", objectIds: ["c1"] })],
    });

    const { result } = renderHook(() =>
      useMetaAdsNotices({ campaignData, healthCheck: undefined }),
    );

    expect(result.current.byTab.costos).toHaveLength(1);
  });

  it("filters out recommendations whose campaigns are all paused/archived", () => {
    const campaignData = makeCampaignData({
      campaigns: [
        makeCampaign({ externalId: "c1", effectiveStatus: "PAUSED" }),
        makeCampaign({
          externalId: "c2",
          name: "Completada",
          effectiveStatus: "COMPLETED",
        }),
      ],
      recommendations: [
        makeRec({ recommendationType: "CREATIVE_FATIGUE", objectIds: ["c1"] }),
        makeRec({
          recommendationType: "CAMPAIGN_BUDGET_LEARNINGS",
          objectIds: ["c2"],
        }),
      ],
    });

    const { result } = renderHook(() =>
      useMetaAdsNotices({ campaignData, healthCheck: undefined }),
    );

    expect(result.current.total).toBe(0);
  });

  it("keeps a recommendation if at least one of its object ids is active", () => {
    const campaignData = makeCampaignData({
      campaigns: [
        makeCampaign({ externalId: "c1", effectiveStatus: "PAUSED" }),
        makeCampaign({
          externalId: "c2",
          name: "Activa",
          effectiveStatus: "ACTIVE",
        }),
      ],
      recommendations: [
        makeRec({
          recommendationType: "CAMPAIGN_BUDGET_LEARNINGS",
          objectIds: ["c1", "c2"],
        }),
      ],
    });

    const { result } = renderHook(() =>
      useMetaAdsNotices({ campaignData, healthCheck: undefined }),
    );

    expect(result.current.byTab.campanas).toHaveLength(1);
    // Context should point to the ACTIVE one.
    expect(result.current.byTab.campanas[0].contextLabel).toContain("Activa");
  });

  it("merges structural recommendations related to active campaigns", () => {
    const campaignData = makeCampaignData();
    const healthCheck = makeHealthCheck({
      recommendations: [makeStructuralRec({ severity: "critical", relatedTargetId: "c1" })],
    });

    const { result } = renderHook(() => useMetaAdsNotices({ campaignData, healthCheck }));

    expect(result.current.byTab.campanas).toHaveLength(1);
    expect(result.current.byTab.campanas[0].severity).toBe("critical");
  });

  it("drops structural recs whose target campaign is not active", () => {
    const campaignData = makeCampaignData({
      campaigns: [makeCampaign({ externalId: "c1", effectiveStatus: "PAUSED" })],
    });
    const healthCheck = makeHealthCheck({
      recommendations: [makeStructuralRec({ relatedTargetId: "c1" })],
    });

    const { result } = renderHook(() => useMetaAdsNotices({ campaignData, healthCheck }));

    expect(result.current.total).toBe(0);
  });

  it("keeps offer-level structural recs even without an active campaign target", () => {
    const healthCheck = makeHealthCheck({
      recommendations: [
        makeStructuralRec({
          type: "create_campaign",
          severity: "warning",
          relatedTargetId: null,
          relatedOfferId: "offer-1",
          title: "Crea una campaña para tu offer",
        }),
      ],
    });

    const { result } = renderHook(() =>
      useMetaAdsNotices({ campaignData: undefined, healthCheck }),
    );

    expect(result.current.byTab.campanas).toHaveLength(1);
  });

  it("sorts notices by severity within each tab (critical first)", () => {
    const campaignData = makeCampaignData({
      campaigns: [
        makeCampaign({ externalId: "c1", name: "A", effectiveStatus: "ACTIVE" }),
        makeCampaign({ externalId: "c2", name: "B", effectiveStatus: "ACTIVE" }),
      ],
      recommendations: [
        makeRec({
          recommendationType: "CAMPAIGN_LOW_DELIVERY",
          objectIds: ["c1"],
          importance: "MEDIUM",
          title: "low-delivery",
        }),
        makeRec({
          recommendationType: "CAMPAIGN_REJECTED",
          objectIds: ["c2"],
          importance: "CRITICAL",
          title: "rejected",
        }),
      ],
    });

    const { result } = renderHook(() =>
      useMetaAdsNotices({ campaignData, healthCheck: undefined }),
    );

    expect(result.current.byTab.campanas.map((n) => n.title)).toEqual(["rejected", "low-delivery"]);
  });

  it("deduplicates notices with the same id and keeps the most severe", () => {
    const campaignData = makeCampaignData({
      recommendations: [
        makeRec({
          recommendationType: "CREATIVE_FATIGUE",
          objectIds: ["c1"],
          importance: "HIGH",
          title: "one",
        }),
        makeRec({
          recommendationType: "CREATIVE_FATIGUE",
          objectIds: ["c1"],
          importance: "CRITICAL",
          title: "two",
        }),
      ],
    });

    const { result } = renderHook(() =>
      useMetaAdsNotices({ campaignData, healthCheck: undefined }),
    );

    expect(result.current.byTab.creativos).toHaveLength(1);
    expect(result.current.byTab.creativos[0].severity).toBe("critical");
  });

  it("computes severity breakdown per tab", () => {
    const campaignData = makeCampaignData({
      campaigns: [
        makeCampaign({ externalId: "c1", effectiveStatus: "ACTIVE" }),
        makeCampaign({ externalId: "c2", effectiveStatus: "ACTIVE" }),
      ],
      recommendations: [
        makeRec({
          recommendationType: "CAMPAIGN_REJECTED",
          objectIds: ["c1"],
          importance: "CRITICAL",
        }),
        makeRec({
          recommendationType: "CAMPAIGN_BUDGET_LEARNINGS",
          objectIds: ["c2"],
          importance: "HIGH",
        }),
      ],
    });

    const { result } = renderHook(() =>
      useMetaAdsNotices({ campaignData, healthCheck: undefined }),
    );

    expect(result.current.total).toBe(2);
    expect(result.current.severity.critical).toBe(1);
    expect(result.current.severity.warning).toBe(1);
    expect(result.current.severityPerTab.campanas.critical).toBe(1);
    expect(result.current.maxSeverityPerTab.campanas).toBe("critical");
    expect(result.current.maxSeverityPerTab.creativos).toBe(null);
  });

  it("hides notices that have been ignored (localStorage-backed)", () => {
    const campaignData = makeCampaignData({
      recommendations: [
        makeRec({ recommendationType: "CAMPAIGN_BUDGET_LEARNINGS", objectIds: ["c1"] }),
      ],
    });

    const { result: initial } = renderHook(() =>
      useMetaAdsNotices({ campaignData, healthCheck: undefined }),
    );
    const firstId = initial.current.byTab.campanas[0].id;

    // Write directly to the same storage the hook reads from.
    const IGNORE_KEY = "meta-ads-ignored-notices-v1";
    localStorage.setItem(IGNORE_KEY, JSON.stringify([[firstId, Date.now()]]));

    const { result: afterIgnore } = renderHook(() =>
      useMetaAdsNotices({ campaignData, healthCheck: undefined }),
    );

    expect(afterIgnore.current.total).toBe(0);
  });

  it("exposes a stable dedupe id that survives re-fetches", () => {
    const campaignData1 = makeCampaignData({
      recommendations: [makeRec({ recommendationType: "CREATIVE_FATIGUE", objectIds: ["c1"] })],
    });
    const campaignData2 = makeCampaignData({
      recommendations: [
        makeRec({
          recommendationType: "CREATIVE_FATIGUE",
          objectIds: ["c1"],
          // Different importance on refetch — but stable id.
          importance: "CRITICAL",
        }),
      ],
    });

    const { result: r1 } = renderHook(() =>
      useMetaAdsNotices({ campaignData: campaignData1, healthCheck: undefined }),
    );
    const { result: r2 } = renderHook(() =>
      useMetaAdsNotices({ campaignData: campaignData2, healthCheck: undefined }),
    );

    expect(r1.current.byTab.creativos[0].id).toBe(r2.current.byTab.creativos[0].id);
  });
});

// Silence "act" warnings from renderHook for sync hooks where setState happens
// inside the same render; renderHook already wraps things in act.
void act;
void vi;
