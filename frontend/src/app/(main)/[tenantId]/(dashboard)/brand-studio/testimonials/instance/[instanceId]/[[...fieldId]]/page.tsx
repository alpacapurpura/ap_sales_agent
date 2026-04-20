import { TestimonialDetailPage } from "@/features/brand-studio/pages/TestimonialDetailPage";

/**
 * Testimonial detail route.
 *
 *   /{tenantId}/brand-studio/testimonials/instance/{id}            → list view
 *   /{tenantId}/brand-studio/testimonials/instance/{id}/{fieldId}  → detail view
 *
 * The page reads `tenantId`, `instanceId` and `fieldId` from the URL via
 * `useParams` — this route file stays thin.
 */
export default function BrandStudioTestimonialInstancePage() {
  return <TestimonialDetailPage />;
}
