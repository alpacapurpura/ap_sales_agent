"use client";

// TODO(F7): Implement real testimonials hook wired to the offer-studio
// testimonials API endpoint when it's available.
// For now this hook returns a static empty state so the collection
// routes render without a backend dependency.

/**
 * Stub hook for offer-scoped testimonials.
 *
 * Returns an empty list and a loading=false state so the collection
 * landing and detail pages can render the empty-state UI without
 * requiring a backend endpoint.
 *
 * Replace with a real React Query hook in F7 when the backend
 * exposes `GET /api/v1/offer/{offerId}/testimonials`.
 */
export function useOfferTestimonials(_offerId: string) {
  return {
    testimonials: [] as OfferTestimonialStub[],
    loading: false,
    error: null as string | null,
  };
}

/** Minimal stub type — expand in F7 when the real DTO arrives. */
export interface OfferTestimonialStub {
  id: string;
  author_name: string;
  quote: string;
  created_at: string;
}
