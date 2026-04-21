import { redirect } from "next/navigation";

/**
 * Offer Studio — offer root redirect.
 *
 * Sends the user to `/editor` which is the canonical entry point for the
 * offer editor. The shell (layout.tsx) renders the header + rail + tab bar
 * regardless of which sub-route is active.
 *
 * URL contract: `/offer/{id}` → 307 → `/offer/{id}/editor`
 */
export default async function OfferRootPage({
  params,
}: {
  params: Promise<{ tenantId: string; id: string }>;
}) {
  const { tenantId, id } = await params;
  redirect(`/${tenantId}/offer-studio/offer/${id}/editor`);
}
