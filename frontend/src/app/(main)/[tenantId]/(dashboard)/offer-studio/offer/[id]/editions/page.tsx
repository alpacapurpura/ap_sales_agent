import { redirect } from "next/navigation";

import { EditionsManagementClient } from "@/features/offer-studio/components/EditionsManagementClient";

/**
 * Offer Studio — editions management tab.
 *
 * Renders a full-width variant collection landing (polymorphic — adapts
 * noun per variant_structure: "Planes", "Variantes", "Regiones", etc.).
 * This is the dedicated management surface: create / duplicate / delete
 * variants. Quick switching between variants happens in the VariantRail
 * sidebar that lives inside the editor layout.
 *
 * When the offer can't hold multiple variants (archetype.allow_single_variant
 * + variants.length === 1) this route redirects to /editor via the client
 * guard — see EditionsManagementClient.
 */
export default async function OfferEditionsPage({
  params,
}: {
  params: Promise<{ tenantId: string; id: string }>;
}) {
  const { tenantId, id: offerId } = await params;

  if (!tenantId || !offerId) redirect("/");

  return <EditionsManagementClient offerId={offerId} tenantId={tenantId} />;
}
