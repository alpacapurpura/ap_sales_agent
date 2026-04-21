"use client";

// TODO(F7): Implement real FAQ hook wired to the offer-studio FAQ API
// endpoint. The FAQ section stores Q&A pairs on the Offer domain object;
// this stub hook returns an empty list for the collection landing page.

/**
 * Stub hook for offer-scoped FAQ items.
 *
 * Returns an empty list so the collection landing renders the empty-state.
 * Replace with a real React Query hook in F7.
 */
export function useOfferFaq(_offerId: string) {
  return {
    faqItems: [] as OfferFaqItemStub[],
    loading: false,
    error: null as string | null,
  };
}

/** Minimal stub type — expand in F7. */
export interface OfferFaqItemStub {
  id: string;
  question: string;
  answer: string;
}
