import { redirect } from "next/navigation";

import { buildLegacyEditionRedirectUrl } from "@/features/offer-studio/components/OfferShellLayout";

/**
 * Legacy edition catch-all — 30-day redirect shim.
 *
 * Old URL: /{t}/offer-studio/offer/{id}/edition/{code}/{section}
 * New URL: /{t}/offer-studio/offer/{id}/editor/{section}?edition={code}
 *
 * This shim keeps bookmarks and external links working for 30 days
 * post-F3. Remove after 2026-05-20 (delete the entire `edition/`
 * directory under `offer/[id]/`).
 */
interface PageParams {
  tenantId: string;
  id: string;
  code: string;
  section: string;
}

/**
 *
 */
export default async function LegacyEditionSectionShim({
  params,
}: {
  params: Promise<PageParams>;
}) {
  const { tenantId, id: offerId, code, section } = await params;

  const newUrl = buildLegacyEditionRedirectUrl({
    tenantId,
    offerId,
    code,
    section,
    fieldId: undefined,
  });

  redirect(newUrl);
}
