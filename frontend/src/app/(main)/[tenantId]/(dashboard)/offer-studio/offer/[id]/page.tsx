import { redirect } from "next/navigation";

/**
 * Offer Studio — offer root redirect. Jumps straight to the editor's
 * first section to avoid a two-hop redirect chain that triggers a
 * Turbopack `performance.measure` negative-timestamp warning.
 */
export default async function OfferRootPage({
  params,
}: {
  params: Promise<{ tenantId: string; id: string }>;
}) {
  const { tenantId, id } = await params;
  redirect(`/${tenantId}/offer-studio/offer/${id}/editor/identity`);
}
