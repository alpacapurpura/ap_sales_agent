import { notFound } from "next/navigation";

import {
  isOfferStudioSection,
  OFFER_SECTION_PAGE_MAP,
} from "@/features/offer-studio/pages/section-page-map";

/**
 * Offer-studio editor — catch-all section page.
 *
 * Route shape: ``/{tenantId}/offer-studio/offer/{offerId}/edition/{code}/{section}/{fieldId?}``
 *
 * - ``code = "evergreen"`` → offer-level context. Edition-level sections
 *   render the "needs a specific edition" card.
 * - ``code = "<N>"`` → resolves to ``LaunchEdition.edition_number === N`` via
 *   ``useOfferEditionResolver`` inside the mounted client page. 404 on miss.
 *
 * The Server Component here indexes ``OFFER_SECTION_PAGE_MAP`` to pick
 * the matching client page. Unknown section slugs trigger ``notFound()``
 * instead of surfacing a cryptic client-side error.
 */
interface PageParams {
  tenantId: string;
  id: string;
  code: string;
  section: string;
  fieldId?: string[];
}

/** Server Component dispatcher — picks the client page by section slug. */
export default async function OfferSectionCatchAllPage({
  params,
}: {
  params: Promise<PageParams>;
}) {
  const { id: offerId, code, section } = await params;

  if (!isOfferStudioSection(section)) {
    notFound();
  }

  const Component = OFFER_SECTION_PAGE_MAP[section];
  return <Component offerId={offerId} editionCode={code} />;
}
