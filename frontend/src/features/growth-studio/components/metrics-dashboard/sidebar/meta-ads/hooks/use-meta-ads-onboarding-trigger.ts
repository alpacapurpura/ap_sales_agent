/**
 * Pure trigger logic for the Meta Ads first-connect onboarding modal.
 *
 * The modal should open when — and only when — the tenant has JUST connected
 * Meta Ads and needs guidance to associate their active campaigns with
 * offers. Concretely:
 *
 *   1. The user has NOT dismissed the onboarding before.
 *   2. Both source queries (campaign performance + offer associations) have
 *      finished loading. This is load-bearing: evaluating the expression
 *      while one of them is still `undefined` causes a visible flicker
 *      (see `__tests__/useMetaAdsOnboardingTrigger.test.ts`).
 *   3. Meta reports at least one ACTIVE campaign.
 *   4. The tenant has zero offer↔campaign associations.
 *
 * Split out as a pure function so it can be unit-tested in isolation
 * without mounting the full MetaAdsDashboard and its react-query tree.
 */
import type { CampaignPerformanceData } from "../../../../../types/metrics";
import type { Association } from "../../../../../types/offer-association";
import type { OnboardingCampaign } from "../MetaAdsOnboardingModal";

export interface MetaAdsOnboardingTriggerInput {
  campaignData: CampaignPerformanceData | undefined;
  associations: Association[] | undefined;
  hasUserDismissed: boolean;
}

export interface MetaAdsOnboardingTriggerResult {
  isOpen: boolean;
  campaigns: OnboardingCampaign[];
}

/**
 *
 */
export function computeMetaAdsOnboardingTrigger(
  input: MetaAdsOnboardingTriggerInput,
): MetaAdsOnboardingTriggerResult {
  const { campaignData, associations, hasUserDismissed } = input;

  // Gate on BOTH queries having produced data. Treating `undefined` as an
  // empty list (the old behaviour) causes the modal to open transiently
  // whenever campaignData resolves before associations.
  const bothLoaded = campaignData !== undefined && associations !== undefined;

  const isOpen =
    !hasUserDismissed &&
    bothLoaded &&
    campaignData.activeCampaigns > 0 &&
    associations.length === 0;

  const campaigns: OnboardingCampaign[] = (campaignData?.campaigns ?? [])
    .filter((c) => (c.effectiveStatus ?? "").toUpperCase() === "ACTIVE")
    .map((c) => ({
      externalId: c.externalId,
      name: c.name,
      objective: c.objective,
    }));

  return { isOpen, campaigns };
}
