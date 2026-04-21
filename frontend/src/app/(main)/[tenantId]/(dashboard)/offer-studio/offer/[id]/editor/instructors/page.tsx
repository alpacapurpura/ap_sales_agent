/**
 * Offer Studio — instructors collection landing.
 * Mirrors brand-studio's `/team` pattern.
 *
 * TODO(F7): Wire OfferInstructorsLandingPage to the real
 * `useOfferInstructors` hook. Currently renders an empty-state card.
 */
import { OfferInstructorsLandingPage } from "@/features/offer-studio/components/collections/OfferInstructorsLandingPage";

/**
 *
 */
export default async function OfferEditorInstructorsPage({
  params,
}: {
  params: Promise<{ tenantId: string; id: string }>;
}) {
  const { id: offerId } = await params;
  return <OfferInstructorsLandingPage offerId={offerId} />;
}
