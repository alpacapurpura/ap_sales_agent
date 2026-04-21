/**
 * Offer Studio — FAQ collection landing.
 *
 * TODO(F7): Wire OfferFaqLandingPage to the real `useOfferFaq` hook.
 */
import { OfferFaqLandingPage } from "@/features/offer-studio/components/collections/OfferFaqLandingPage";

export default async function OfferEditorFaqPage({
  params,
}: {
  params: Promise<{ tenantId: string; id: string }>;
}) {
  const { id: offerId } = await params;
  return <OfferFaqLandingPage offerId={offerId} />;
}
