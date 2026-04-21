"use client";

import { use } from "react";

import { OfferVentasTab } from "@/features/offer-studio/components/ventas/OfferVentasTab";
import { useOfferWithEdition } from "@/features/offer-studio/hooks/use-offer-with-edition";

/**
 * Ventas for a specific edition. The `useOfferWithEdition` hook reads the
 * `editionId` route param and resolves it to the matching LaunchEdition;
 * the tab re-scopes enrollments automatically when the segment changes.
 */
export default function EditionVentasPage({
  params,
}: {
  params: Promise<{ tenantId: string; id: string; editionId: string }>;
}) {
  const { tenantId, id: offerId } = use(params);
  const { currentEditionId } = useOfferWithEdition(offerId);
  return (
    <OfferVentasTab offerId={offerId} currentEditionId={currentEditionId} tenantId={tenantId} />
  );
}
