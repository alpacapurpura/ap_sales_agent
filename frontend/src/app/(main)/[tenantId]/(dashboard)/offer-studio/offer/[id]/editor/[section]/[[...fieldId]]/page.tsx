import { notFound } from "next/navigation";

import {
  isOfferStudioSection,
  OFFER_SECTION_PAGE_MAP,
} from "@/features/offer-studio/pages/section-page-map";

/**
 * Offer Studio editor — catch-all section dispatcher.
 *
 * Route shape: `/{tenantId}/offer-studio/offer/{id}/editor/{section}/{fieldId?}`
 *
 * Mirrors the legacy catch-all at
 * `.../offer/[id]/edition/[code]/[section]/[[...fieldId]]/page.tsx`
 * but uses the new flat URL without an edition-code segment.
 * Until F4 harmonises the edition-code flow, `editionCode="evergreen"` is
 * passed to every section page so the existing factory signature is unchanged.
 *
 * Unknown section slugs return 404 via `notFound()`.
 */
interface PageParams {
  tenantId: string;
  id: string;
  section: string;
  fieldId?: string[];
}

export default async function OfferEditorSectionPage({
  params,
}: {
  params: Promise<PageParams>;
}) {
  const { id: offerId, section } = await params;

  if (!isOfferStudioSection(section)) {
    notFound();
  }

  const Component = OFFER_SECTION_PAGE_MAP[section];
  // editionCode="evergreen" until F4 deletes the legacy edition-code scope.
  // The factory signature accepts editionCode and passes it to the active
  // edition resolver — "evergreen" maps to the single implicit variant for
  // offers without explicit editions.
  return <Component offerId={offerId} editionCode="evergreen" />;
}
