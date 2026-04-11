// Offer lifecycle types — CONTRACT.md §6.2 + §9
import type { OfferLifecycleStatus } from "./enums";

export interface ChangeOfferStatusPayload {
  status: OfferLifecycleStatus;
  reason?: string;
}

export interface OfferStatusResponse {
  offer_id: string;
  status: OfferLifecycleStatus;
  previous_status: OfferLifecycleStatus;
  status_changed_at: string; // ISO 8601 UTC
  completion_percentage: number;
  landing_auto_unpublished: boolean;
}

/**
 * Client-side mirror of the canonical lifecycle state machine.
 * Kept in sync with backend LIFECYCLE_TRANSITIONS (CONTRACT.md §9).
 * The backend is the source of truth — this is only used to disable UI
 * transitions that would immediately fail with 409.
 */
export const LIFECYCLE_TRANSITIONS: Record<
  OfferLifecycleStatus,
  ReadonlySet<OfferLifecycleStatus>
> = {
  draft: new Set<OfferLifecycleStatus>(["active", "archived"]),
  active: new Set<OfferLifecycleStatus>(["draft", "paused", "archived"]),
  paused: new Set<OfferLifecycleStatus>(["draft", "active", "archived"]),
  archived: new Set<OfferLifecycleStatus>(), // terminal — use /restore
};

export function canTransition(
  from: OfferLifecycleStatus,
  to: OfferLifecycleStatus,
): boolean {
  return LIFECYCLE_TRANSITIONS[from].has(to);
}
