import { useSearchParams } from "next/navigation";
import { useMemo } from "react";

import { EditionStatus } from "../types";

import { useEditions } from "./use-editions";

import type { LaunchEdition } from "../types";

/**
 * Result of resolving which edition the user is currently viewing.
 *
 * `currentEditionId` is the URL-requested edition when valid; otherwise it
 * falls back to the "next relevant" edition (active first, else the
 * soonest upcoming, else the most recent past edition, else null).
 */
export interface OfferEditionResolution {
  editions: LaunchEdition[];
  currentEditionId: string | null;
  currentEdition: LaunchEdition | null;
  loading: boolean;
}

/**
 * Resolve the current edition the user is viewing from URL `?edition=`,
 * with a sensible fallback when the URL has none (or references a
 * deleted one). Order of preference:
 *   1. ACTIVE edition
 *   2. Nearest future UPCOMING edition (by start_date ascending)
 *   3. Most recent COMPLETED/CANCELLED edition
 *
 * This is a read-only hook — it does NOT mutate the URL itself. The
 * caller updates the URL via `router.replace('?edition=...')` when the
 * user clicks an entry in the rail.
 */
export function useOfferWithEdition(offerId: string): OfferEditionResolution {
  const searchParams = useSearchParams();
  const requested = searchParams?.get("edition") ?? null;
  const { editions, loading } = useEditions(offerId);

  const currentEdition = useMemo<LaunchEdition | null>(() => {
    if (!editions.length) return null;

    // 1. honour an explicit ?edition= if it still exists in the list.
    if (requested) {
      const match = editions.find((e) => e.id === requested);
      if (match) return match;
    }
    // 2. active first.
    const active = editions.find((e) => e.status === EditionStatus.ACTIVE);
    if (active) return active;
    // 3. next upcoming by start_date.
    const upcoming = editions
      .filter((e) => e.status === EditionStatus.UPCOMING && e.start_date)
      .sort((a, b) => ((a.start_date ?? "") < (b.start_date ?? "") ? -1 : 1));
    if (upcoming.length) return upcoming[0];
    // 4. latest past (completed/cancelled).
    const past = editions
      .filter((e) => e.status === EditionStatus.COMPLETED || e.status === EditionStatus.CANCELLED)
      .sort((a, b) => ((a.start_date ?? "") > (b.start_date ?? "") ? -1 : 1));
    if (past.length) return past[0];
    // 5. anything else.
    return editions[0];
  }, [editions, requested]);

  return {
    editions,
    currentEditionId: currentEdition?.id ?? null,
    currentEdition,
    loading,
  };
}
