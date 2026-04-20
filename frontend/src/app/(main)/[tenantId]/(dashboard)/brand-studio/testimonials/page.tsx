import { TestimonialsLandingPage } from "@/features/brand-studio/pages/TestimonialsLandingPage";

/**
 * Testimonials landing — InstancePicker (col 2) + welcome pane. Clicking
 * or creating a testimonial routes to
 * /{tenantId}/brand-studio/testimonials/instance/{id} where the Finder
 * 4-column layout takes over (TestimonialDetailPage).
 */
export default function BrandStudioTestimonialsPage() {
  return <TestimonialsLandingPage />;
}
