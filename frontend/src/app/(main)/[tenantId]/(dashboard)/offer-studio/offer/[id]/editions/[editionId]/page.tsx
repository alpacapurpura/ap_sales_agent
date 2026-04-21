import { redirect } from "next/navigation";

/**
 * Legacy `/editions/[editionId]` root — after F3 routed offer-section editing
 * under `/editor/[section]`, this entry point is obsolete. Redirects to the
 * editor tab so users landing here (via old bookmarks or EditionsManagementClient
 * links awaiting follow-up) land on a live surface.
 */
export default async function EditionRootRedirect({
  params,
}: {
  params: Promise<{ tenantId: string; id: string; editionId: string }>;
}) {
  const { tenantId, id } = await params;
  redirect(`/${tenantId}/offer-studio/offer/${id}/editor/identity`);
}
