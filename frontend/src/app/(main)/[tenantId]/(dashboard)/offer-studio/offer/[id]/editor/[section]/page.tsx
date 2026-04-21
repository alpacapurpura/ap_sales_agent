import { notFound } from "next/navigation";

import {
  isOfferStudioSection,
  OFFER_SECTION_PAGE_MAP,
} from "@/features/offer-studio/pages/section-page-map";

/**
 * Offer Studio editor — section dispatcher.
 *
 * Route shape: `/{tenantId}/offer-studio/offer/{id}/editor/{section}`
 *
 * Field selection lives in the ``?field=`` query param and is handled
 * client-side via ``useActiveField`` — no server navigation on focus.
 *
 * Unknown section slugs return 404 via `notFound()`.
 */
interface PageParams {
  tenantId: string;
  id: string;
  section: string;
}

/**
 *
 */
export default async function OfferEditorSectionPage({ params }: { params: Promise<PageParams> }) {
  const { id: offerId, section } = await params;

  if (!isOfferStudioSection(section)) {
    notFound();
  }

  const Component = OFFER_SECTION_PAGE_MAP[section];
  return <Component offerId={offerId} editionCode="evergreen" />;
}
