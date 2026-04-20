import { useParams } from "next/navigation";
import { useMemo } from "react";

import { EditionStatus } from "../types";

import { useEditions } from "./use-editions";

import type { LaunchEdition } from "../types";

/**
 * Result of resolving which edition the user is currently viewing.
 *
 * `currentEditionId` is the route-bound edition when the URL lives under
 * `/offer/{id}/editions/{editionId}/...`; otherwise it falls back to the
 * "next relevant" edition (active first, else the soonest upcoming, else
 * the most recent past edition, else null).
 */
export interface OfferEditionResolution {
  editions: LaunchEdition[];
  currentEditionId: string | null;
  currentEdition: LaunchEdition | null;
  loading: boolean;
}

/**
 * Resolve the current edition the user is viewing from the route's
 * `editionId` dynamic segment, with a sensible fallback when the URL
 * has none (Info routes) or when the segment references a deleted
 * edition. Order of preference:
 *
 *   1. ACTIVE edition
 *   2. Nearest future UPCOMING edition (by start_date ascending)
 *   3. Most recent COMPLETED/CANCELLED edition
 *
 * This hook is read-only — URL transitions happen via router.push in
 * the rail/TabBar components, never here.
 */
export function useOfferWithEdition(offerId: string): OfferEditionResolution {
  const params = useParams();
  const rawEditionId = params?.editionId;
  // Next.js types `params` values as `string | string[] | undefined`. We
  // only honour single-string segments; array-shaped params come from
  // catch-all routes, which this hook doesn't support.
  const requestedEditionId = typeof rawEditionId === "string" ? rawEditionId : null;

  const { editions, loading } = useEditions(offerId);

  const currentEdition = useMemo<LaunchEdition | null>(() => {
    if (!editions.length) return null;

    if (requestedEditionId) {
      const match = editions.find((e) => e.id === requestedEditionId);
      if (match) return match;
    }
    const active = editions.find((e) => e.status === EditionStatus.ACTIVE);
    if (active) return active;

    const upcoming = editions
      .filter((e) => e.status === EditionStatus.UPCOMING && e.start_date)
      .sort((a, b) => ((a.start_date ?? "") < (b.start_date ?? "") ? -1 : 1));
    if (upcoming.length) return upcoming[0];

    const past = editions
      .filter((e) => e.status === EditionStatus.COMPLETED || e.status === EditionStatus.CANCELLED)
      .sort((a, b) => ((a.start_date ?? "") > (b.start_date ?? "") ? -1 : 1));
    if (past.length) return past[0];

    return editions[0];
  }, [editions, requestedEditionId]);

  return {
    editions,
    currentEditionId: currentEdition?.id ?? null,
    currentEdition,
    loading,
  };
}
