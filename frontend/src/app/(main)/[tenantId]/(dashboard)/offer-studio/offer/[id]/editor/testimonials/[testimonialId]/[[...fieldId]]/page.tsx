/**
 * Offer Studio — testimonial detail route.
 *
 *   /editor/testimonials/{testimonialId}           → list view / detail pane
 *   /editor/testimonials/{testimonialId}/{fieldId} → field-level edit
 *
 * TODO(F7): Replace stub with real detail page when testimonial backend
 * endpoint and form-runtime schema are available.
 */
import { OfferTestimonialDetailPage } from "@/features/offer-studio/components/collections/OfferTestimonialDetailPage";

export default async function OfferEditorTestimonialDetailPage({
  params,
}: {
  params: Promise<{ tenantId: string; id: string; testimonialId: string; fieldId?: string[] }>;
}) {
  const { id: offerId, testimonialId } = await params;
  return <OfferTestimonialDetailPage offerId={offerId} testimonialId={testimonialId} />;
}
