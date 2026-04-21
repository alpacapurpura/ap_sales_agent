"use client";

import { use } from "react";

import { AssetsView } from "@/features/offer-studio/components/assets/AssetsView";

/**
 * Assets scoped to a specific edition. `AssetsView` today renders offer-wide
 * assets; per-edition asset filtering is tracked as a follow-up (needs
 * backend `edition_id` filter on the assets list endpoint).
 */
export default function EditionAssetsPage({
  params,
}: {
  params: Promise<{ tenantId: string; id: string; editionId: string }>;
}) {
  const { id: offerId } = use(params);
  return <AssetsView offerId={offerId} />;
}
