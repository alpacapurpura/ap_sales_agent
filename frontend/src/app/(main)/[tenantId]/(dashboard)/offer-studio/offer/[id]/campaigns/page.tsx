"use client";

import { useOfferShell } from "@/features/offer-studio/components/container/offer-shell";
import { CampaignsView } from "@/features/offer-studio/components/campaigns/campaigns-view";

/**
 * Campaigns tab — rendered inside the persistent Offer Studio shell.
 */
export default function CampaignsPage() {
  const { offer } = useOfferShell();
  return <CampaignsView offerId={offer.id} />;
}
