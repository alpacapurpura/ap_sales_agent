"use client";

import { use } from "react";

import { CampaignsView } from "@/features/offer-studio/components/campaigns/CampaignsView";

/**
 * Campaigns scoped to a specific edition. `CampaignsView` today renders
 * offer-wide campaigns; per-edition filtering is tracked as a follow-up
 * (needs backend association between Growth Studio campaigns and editions).
 */
export default function EditionCampaignsPage({
  params,
}: {
  params: Promise<{ tenantId: string; id: string; editionId: string }>;
}) {
  const { tenantId, id: offerId } = use(params);
  return <CampaignsView offerId={offerId} tenantId={tenantId} />;
}
