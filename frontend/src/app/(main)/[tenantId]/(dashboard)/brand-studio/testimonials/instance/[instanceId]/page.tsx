import { TestimonialDetailPage } from "@/features/brand-studio/pages/TestimonialDetailPage";

/**
 * Testimonial detail route.
 *
 *   /{tenantId}/brand-studio/testimonials/instance/{id}                 → list view
 *   /{tenantId}/brand-studio/testimonials/instance/{id}?field={fieldId} → detail view
 *
 * The page reads `tenantId` + `instanceId` from the URL via `useParams`;
 * the active field id lives in the `?field=` query param and is read
 * client-side via `useActiveField`.
 */
export default function BrandStudioTestimonialInstancePage() {
  return <TestimonialDetailPage />;
}
