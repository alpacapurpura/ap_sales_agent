/**
 * Offer Studio — testimonial detail route.
 *
 *   /editor/testimonials/{testimonialId}                  → list view / detail pane
 *   /editor/testimonials/{testimonialId}?field={fieldId}  → field-level edit
 */
import { OfferTestimonialDetailPage } from "@/features/offer-studio/components/collections/OfferTestimonialDetailPage";

/**
 *
 */
export default async function OfferEditorTestimonialDetailPage({
  params,
}: {
  params: Promise<{ tenantId: string; id: string; testimonialId: string }>;
}) {
  const { id: offerId, testimonialId } = await params;
  return <OfferTestimonialDetailPage offerId={offerId} testimonialId={testimonialId} />;
}
