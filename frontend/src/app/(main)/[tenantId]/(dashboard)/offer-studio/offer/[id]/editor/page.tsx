import { redirect } from "next/navigation";

/**
 * Offer Studio editor landing. Mirrors brand-studio — sends the user
 * to ``identity`` so the first field (``public_name``) is auto-selected
 * by the runtime. The left nav rail is rendered by the layout regardless
 * of the section.
 */
export default async function OfferEditorLandingPage({
  params,
}: {
  params: Promise<{ tenantId: string; id: string }>;
}) {
  const { tenantId, id } = await params;
  redirect(`/${tenantId}/offer-studio/offer/${id}/editor/identity`);
}
