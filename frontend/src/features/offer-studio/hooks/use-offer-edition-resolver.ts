"use client";

import { useMemo } from "react";

import { useEditions } from "./use-editions";
import { EVERGREEN_CODE } from "./use-visible-sections";

import type { LaunchEdition } from "../types";
import type { EditionCode } from "./use-visible-sections";

export type EditionScopeMode = "evergreen" | "edition";

/**
 * Result of resolving an URL edition code for a given offer.
 *
 * - ``mode = "evergreen"``: no edition context. ``edition`` is ``null``.
 *   Schemas filter out ``edition_level`` sections, fields with
 *   ``owner="edition"`` are hidden, saves route to the offer only.
 * - ``mode = "edition"``: a specific LaunchEdition is loaded by its
 *   ``edition_number``. ``edition`` carries the resolved row.
 * - ``status = "not_found"``: the URL code refers to an edition number
 *   that does not exist for this offer. The consumer should call
 *   ``notFound()`` (Next.js) or route to a 404 page.
 * - ``status = "loading"``: catalog still fetching.
 */
export interface OfferEditionResolution {
  mode: EditionScopeMode;
  edition: LaunchEdition | null;
  editions: readonly LaunchEdition[];
  status: "loading" | "ready" | "not_found";
}

/**
 * Resolve the URL edition segment to a concrete edition row, or
 * recognise it as the virtual ``evergreen`` sentinel.
 *
 * Contract locked in DECISIONS.md §D19:
 * - ``code === EVERGREEN_CODE`` → offer-level mode, no DB row.
 * - ``code === "<N>"`` (positive integer string) → resolves to
 *   ``LaunchEdition.edition_number === N``. 404 if missing.
 * - Any other input shape is treated as ``not_found`` so malformed URLs
 *   fail loudly rather than silently collapsing to evergreen.
 */
export function useOfferEditionResolver(
  offerId: string,
  code: EditionCode | undefined,
): OfferEditionResolution {
  const { editions, loading } = useEditions(offerId);

  return useMemo<OfferEditionResolution>(() => {
    if (code === undefined) {
      return { mode: "evergreen", edition: null, editions, status: loading ? "loading" : "ready" };
    }

    if (code === EVERGREEN_CODE) {
      return { mode: "evergreen", edition: null, editions, status: loading ? "loading" : "ready" };
    }

    const parsed = parseEditionNumber(code);
    if (parsed === null) {
      return {
        mode: "edition",
        edition: null,
        editions,
        status: loading ? "loading" : "not_found",
      };
    }

    if (loading) {
      return { mode: "edition", edition: null, editions, status: "loading" };
    }

    const match = editions.find((e) => e.edition_number === parsed);
    if (!match) {
      return { mode: "edition", edition: null, editions, status: "not_found" };
    }

    return { mode: "edition", edition: match, editions, status: "ready" };
  }, [code, editions, loading]);
}

/** Positive integer parser — returns ``null`` for any non-numeric / non-positive input. */
function parseEditionNumber(code: string): number | null {
  if (!/^[1-9]\d*$/.test(code)) return null;
  const parsed = Number.parseInt(code, 10);
  return Number.isSafeInteger(parsed) && parsed > 0 ? parsed : null;
}
