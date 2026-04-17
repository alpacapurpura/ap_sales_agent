"use client";

import { OfferVentasTab } from "@/features/offer-studio/components/ventas/OfferVentasTab";
import { useOfferShell } from "@/features/offer-studio/context/OfferShellContext";
import { useOfferWithEdition } from "@/features/offer-studio/hooks/use-offer-with-edition";

/**
 * Ventas tab — lists enrollments scoped to the currently-selected edition
 * (or offer-wide when none is active). Deep-links to Closer Studio's
 * `/sales/enrollments` for richer ops.
 */
export default function VentasPage() {
  const { offer, tenantId } = useOfferShell();
  const { currentEditionId } = useOfferWithEdition(offer.id);
  return (
    <OfferVentasTab offerId={offer.id} currentEditionId={currentEditionId} tenantId={tenantId} />
  );
}
