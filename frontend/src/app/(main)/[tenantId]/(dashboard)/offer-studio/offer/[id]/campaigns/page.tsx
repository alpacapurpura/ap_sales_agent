"use client";

import { use } from "react";

import { CampaignsView } from "@/features/offer-studio/components/campaigns/CampaignsView";

/**
 * Campaigns tab — rendered inside the persistent Offer Studio shell.
 * Reads tenantId + offerId from route params directly.
 */
export default function CampaignsPage({
  params,
}: {
  params: Promise<{ tenantId: string; id: string }>;
}) {
  const { tenantId, id: offerId } = use(params);
  return <CampaignsView offerId={offerId} tenantId={tenantId} />;
}
