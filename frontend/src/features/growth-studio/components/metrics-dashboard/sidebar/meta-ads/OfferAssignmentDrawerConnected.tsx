"use client";

/**
 * Self-contained wrapper around OfferAssignmentDrawer.
 *
 * Fetches campaigns, associations and offers directly from their React Query
 * hooks so the drawer can be opened from ANY page without the parent having
 * to juggle the data plumbing. Simply pass `open` + `onOpenChange` and you
 * get a fully functional assignment drawer.
 */

import { useMemo } from "react";

import { useAssociations, useOffersForAssignment } from "../../../../api/offer-association-api";
import { useCampaignPerformance } from "../../../../api/campaigns-api";
import type { MetaAdsPeriod } from "../../../../types/metrics";
import type { Association } from "../../../../types/offer-association";
import { OfferAssignmentDrawer } from "./OfferAssignmentDrawer";
import type { AssignmentOffer, AssignmentTarget } from "./OfferAssignmentDrawer";

interface OfferAssignmentDrawerConnectedProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  period?: MetaAdsPeriod;
}

export function OfferAssignmentDrawerConnected({
  open,
  onOpenChange,
  period = "30d",
}: OfferAssignmentDrawerConnectedProps) {
  // Always subscribe so data is already cached when the drawer opens.
  // IMPORTANT: offers come from /api/v1/advertising/offers (ALL active offers),
  // NOT from /metrics-by-offer (which only returns offers with associations).
  const { data: campaignData } = useCampaignPerformance(period);
  const { data: associations } = useAssociations();
  const { data: availableOffers } = useOffersForAssignment();

  const associationByCampaign = useMemo(() => {
    const map = new Map<string, Association>();
    for (const a of associations ?? []) {
      if (a.targetType === "campaign") {
        map.set(a.targetExternalId, a);
      }
    }
    return map;
  }, [associations]);

  const targets = useMemo<AssignmentTarget[]>(() => {
    const campaigns = campaignData?.campaigns ?? [];
    // Sort active first so the most relevant campaigns appear on top.
    const sorted = [...campaigns].sort((a, b) => {
      const aActive = (a.effectiveStatus ?? "").toUpperCase() === "ACTIVE";
      const bActive = (b.effectiveStatus ?? "").toUpperCase() === "ACTIVE";
      if (aActive && !bActive) return -1;
      if (!aActive && bActive) return 1;
      return a.name.localeCompare(b.name);
    });
    return sorted.map((c) => {
      const existing = associationByCampaign.get(c.externalId);
      return {
        type: "campaign" as const,
        externalId: c.externalId,
        name: c.name,
        objective: c.objective,
        currentOfferId: existing?.offerId ?? null,
        suggestedOfferId: null,
        suggestedConfidence: null,
      };
    });
  }, [campaignData?.campaigns, associationByCampaign]);

  const offers = useMemo<AssignmentOffer[]>(
    () =>
      (availableOffers ?? []).map((o) => ({
        id: o.id,
        name: o.name,
        archetype: o.archetype,
        expectedMetricLabelEs: o.expectedMetricLabelEs,
      })),
    [availableOffers],
  );

  return (
    <OfferAssignmentDrawer
      open={open}
      onOpenChange={onOpenChange}
      targets={targets}
      offers={offers}
    />
  );
}
