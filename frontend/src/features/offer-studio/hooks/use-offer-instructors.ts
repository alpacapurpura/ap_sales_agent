"use client";

// TODO(F7): Implement real instructors hook wired to the offer-studio
// instructors API endpoint when it's available.
// The INSTRUCTORS section of the offer references brand-studio team members
// by ID. This stub hook mirrors that relationship without a real API call.

/**
 * Stub hook for offer-scoped instructors.
 *
 * Returns an empty list so the collection landing renders the empty-state.
 * The INSTRUCTORS section already stores instructor IDs on the Offer domain
 * object (`offer.instructors[]`); in F7 this hook will fetch the full
 * brand-team records matching those IDs.
 *
 * Replace with a real React Query hook in F7 when the backend exposes
 * `GET /api/v1/offer/{offerId}/instructors` or when the offer-studio
 * INSTRUCTORS section picker is connected to brand-studio/team.
 */
export function useOfferInstructors(_offerId: string) {
  return {
    instructors: [] as OfferInstructorStub[],
    loading: false,
    error: null as string | null,
  };
}

/** Minimal stub type — expand in F7 when the real DTO arrives. */
export interface OfferInstructorStub {
  id: string;
  name: string;
  role?: string;
}
