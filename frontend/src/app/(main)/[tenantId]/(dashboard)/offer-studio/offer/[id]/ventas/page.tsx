"use client";

import { use } from "react";

import { OfferVentasTab } from "@/features/offer-studio/components/ventas/OfferVentasTab";
import { useOfferWithEdition } from "@/features/offer-studio/hooks/use-offer-with-edition";

/**
 * Ventas tab — lists enrollments scoped to the currently-selected edition
 * (or offer-wide when none is active). Deep-links to Closer Studio's
 * `/sales/enrollments` for richer ops.
 */
export default function VentasPage({
  params,
}: {
  params: Promise<{ tenantId: string; id: string }>;
}) {
  const { tenantId, id: offerId } = use(params);
  const { currentEditionId } = useOfferWithEdition(offerId);
  return (
    <OfferVentasTab offerId={offerId} currentEditionId={currentEditionId} tenantId={tenantId} />
  );
}
