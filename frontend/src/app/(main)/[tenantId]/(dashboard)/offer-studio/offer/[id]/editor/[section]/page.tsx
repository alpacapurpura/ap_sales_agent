import { notFound } from "next/navigation";

import { isOfferStudioSection } from "@/features/offer-studio/pages/section-slugs";
import { SectionDispatcher } from "@/features/offer-studio/pages/SectionDispatcher";

/**
 * Offer Studio editor — section dispatcher (Server Component).
 *
 * Route: `/{tenantId}/offer-studio/offer/{id}/editor/{section}`
 *
 * Valida el slug contra `section-slugs.ts` (server-safe, sin imports
 * client). Delega el render al `SectionDispatcher` client que hace
 * lazy-load del chunk per-section via `next/dynamic`. Field selection
 * vive en el query param `?field=` y se maneja client-side.
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

  return <SectionDispatcher slug={section} offerId={offerId} editionCode="evergreen" />;
}
