"use client";

import { use } from "react";

import { AssetsView } from "@/features/offer-studio/components/assets/AssetsView";

/**
 * Assets tab — rendered inside the persistent Offer Studio shell.
 * Reads offer id from route params directly (no shell context).
 */
export default function AssetsPage({
  params,
}: {
  params: Promise<{ tenantId: string; id: string }>;
}) {
  const { id: offerId } = use(params);
  return <AssetsView offerId={offerId} />;
}
