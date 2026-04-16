"use client";

import { CampaignsView } from "@/features/offer-studio/components/campaigns/CampaignsView";
import { useOfferShell } from "@/features/offer-studio/components/container/OfferShell";

/**
 * Campaigns tab — rendered inside the persistent Offer Studio shell.
 */
export default function CampaignsPage() {
  const { offer } = useOfferShell();
  return <CampaignsView offerId={offer.id} />;
}
