"use client";

import { CampaignsView } from "@/features/offer-studio/components/campaigns/CampaignsView";
import { useOfferShell } from "@/features/offer-studio/context/OfferShellContext";

/**
 * Campaigns scoped to a specific edition. `CampaignsView` today renders
 * offer-wide campaigns; per-edition filtering is tracked as a follow-up
 * (needs backend association between Growth Studio campaigns and editions).
 */
export default function EditionCampaignsPage() {
  const { offer } = useOfferShell();
  return <CampaignsView offerId={offer.id} />;
}
