/**
 * Offer Studio — testimonials collection landing.
 *
 * Mirrors brand-studio's `/testimonials` pattern: an instance picker (list)
 * + welcome pane. Clicking a testimonial routes to
 * `editor/testimonials/{testimonialId}` for the detail view.
 *
 * TODO(F7): Wire OfferTestimonialsLandingPage to the real
 * `useOfferTestimonials` hook. Currently renders an empty-state card.
 */
import { OfferTestimonialsLandingPage } from "@/features/offer-studio/components/collections/OfferTestimonialsLandingPage";

/**
 *
 */
export default async function OfferEditorTestimonialsPage({
  params,
}: {
  params: Promise<{ tenantId: string; id: string }>;
}) {
  const { id: offerId } = await params;
  return <OfferTestimonialsLandingPage offerId={offerId} />;
}
