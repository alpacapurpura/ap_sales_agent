"use client";

import { OfferVentasTab } from "@/features/offer-studio/components/ventas/OfferVentasTab";
import { useOfferShell } from "@/features/offer-studio/context/OfferShellContext";
import { useOfferWithEdition } from "@/features/offer-studio/hooks/use-offer-with-edition";

/**
 * Ventas for a specific edition. The `useOfferWithEdition` hook reads the
 * `editionId` route param and resolves it to the matching LaunchEdition;
 * the tab re-scopes enrollments automatically when the segment changes.
 */
export default function EditionVentasPage() {
  const { offer, tenantId } = useOfferShell();
  const { currentEditionId } = useOfferWithEdition(offer.id);
  return (
    <OfferVentasTab offerId={offer.id} currentEditionId={currentEditionId} tenantId={tenantId} />
  );
}
