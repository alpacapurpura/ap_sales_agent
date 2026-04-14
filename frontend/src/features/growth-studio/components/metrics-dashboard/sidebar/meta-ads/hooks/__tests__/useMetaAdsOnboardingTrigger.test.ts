import { describe, expect, it } from "vitest";

import { computeMetaAdsOnboardingTrigger } from "../useMetaAdsOnboardingTrigger";
import type { CampaignPerformanceData } from "../../../../../../types/metrics";
import type { Association } from "../../../../../../types/offer-association";

// ---------------------------------------------------------------------------
// Factories — minimal shapes, only the fields the trigger actually reads.
// ---------------------------------------------------------------------------

function makeCampaignData(
  overrides: Partial<CampaignPerformanceData> = {},
): CampaignPerformanceData {
  return {
    campaigns: [],
    recommendations: [],
    totalCampaigns: 0,
    activeCampaigns: 0,
    currency: null,
    lastSynced: null,
    ...overrides,
  };
}

function makeAssociation(overrides: Partial<Association> = {}): Association {
  return {
    id: "assoc-1",
    tenantId: "t-1",
    targetType: "campaign",
    targetExternalId: "ext-1",
    offerId: "offer-1",
    offerName: "My Offer",
    offerArchetype: null,
    associationType: "manual",
    confidence: null,
    notes: null,
    createdAt: "2026-01-01T00:00:00Z",
    updatedAt: null,
    ...overrides,
  } as Association;
}

describe("computeMetaAdsOnboardingTrigger", () => {
  // -------------------------------------------------------------------------
  // Flicker regression — the exact race condition that made the modal
  // blink on the Meta Ads page for tenants that already had associations.
  // -------------------------------------------------------------------------
  describe("async loading gating (flicker regression)", () => {
    it("stays closed while BOTH queries are still loading", () => {
      const result = computeMetaAdsOnboardingTrigger({
        campaignData: undefined,
        associations: undefined,
        hasUserDismissed: false,
      });
      expect(result.isOpen).toBe(false);
    });

    it("stays closed when campaignData arrives before associations (flicker case)", () => {
      // This is the bug: old code evaluated `(associations?.length ?? 0) === 0`
      // as true while associations was still `undefined`, flashing the modal.
      const result = computeMetaAdsOnboardingTrigger({
        campaignData: makeCampaignData({ activeCampaigns: 5 }),
        associations: undefined,
        hasUserDismissed: false,
      });
      expect(result.isOpen).toBe(false);
    });

    it("stays closed when associations arrives before campaignData", () => {
      const result = computeMetaAdsOnboardingTrigger({
        campaignData: undefined,
        associations: [],
        hasUserDismissed: false,
      });
      expect(result.isOpen).toBe(false);
    });
  });

  // -------------------------------------------------------------------------
  // Legitimate "first-connect" case — must still open the modal.
  // -------------------------------------------------------------------------
  describe("first-connect trigger", () => {
    it("opens when both queries settled, campaigns active, zero associations", () => {
      const result = computeMetaAdsOnboardingTrigger({
        campaignData: makeCampaignData({ activeCampaigns: 3 }),
        associations: [],
        hasUserDismissed: false,
      });
      expect(result.isOpen).toBe(true);
    });
  });

  // -------------------------------------------------------------------------
  // Negative cases — modal must stay closed once settled.
  // -------------------------------------------------------------------------
  describe("settled negatives", () => {
    it("stays closed when tenant already has associations", () => {
      const result = computeMetaAdsOnboardingTrigger({
        campaignData: makeCampaignData({ activeCampaigns: 3 }),
        associations: [makeAssociation()],
        hasUserDismissed: false,
      });
      expect(result.isOpen).toBe(false);
    });

    it("stays closed when there are no active campaigns", () => {
      const result = computeMetaAdsOnboardingTrigger({
        campaignData: makeCampaignData({ activeCampaigns: 0 }),
        associations: [],
        hasUserDismissed: false,
      });
      expect(result.isOpen).toBe(false);
    });

    it("stays closed when user previously dismissed", () => {
      const result = computeMetaAdsOnboardingTrigger({
        campaignData: makeCampaignData({ activeCampaigns: 3 }),
        associations: [],
        hasUserDismissed: true,
      });
      expect(result.isOpen).toBe(false);
    });
  });

  // -------------------------------------------------------------------------
  // Derived campaigns list — must only include ACTIVE campaigns, mapped to
  // the minimal OnboardingCampaign shape that the modal consumes.
  // -------------------------------------------------------------------------
  describe("campaigns projection", () => {
    it("projects only ACTIVE campaigns to the onboarding shape", () => {
      const result = computeMetaAdsOnboardingTrigger({
        campaignData: makeCampaignData({
          activeCampaigns: 2,
          // Intentionally typed as `any` — the CampaignWithMetrics shape has
          // many irrelevant fields that the trigger does not read.
          campaigns: [
            {
              externalId: "camp-1",
              name: "Sales Master",
              effectiveStatus: "ACTIVE",
              objective: "OUTCOME_SALES",
            },
            {
              externalId: "camp-2",
              name: "Paused promo",
              effectiveStatus: "PAUSED",
              objective: "OUTCOME_TRAFFIC",
            },
            {
              externalId: "camp-3",
              name: "Tráfico",
              effectiveStatus: "active", // case-insensitive
              objective: "OUTCOME_TRAFFIC",
            },
          ] as unknown as CampaignPerformanceData["campaigns"],
        }),
        associations: [],
        hasUserDismissed: false,
      });

      expect(result.campaigns).toEqual([
        { externalId: "camp-1", name: "Sales Master", objective: "OUTCOME_SALES" },
        { externalId: "camp-3", name: "Tráfico", objective: "OUTCOME_TRAFFIC" },
      ]);
    });

    it("returns an empty list while campaignData is still loading", () => {
      const result = computeMetaAdsOnboardingTrigger({
        campaignData: undefined,
        associations: undefined,
        hasUserDismissed: false,
      });
      expect(result.campaigns).toEqual([]);
    });
  });
});
