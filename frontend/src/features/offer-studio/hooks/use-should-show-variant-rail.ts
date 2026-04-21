"use client";

import { useMemo } from "react";

import { useArchetypeCapabilities } from "./use-archetype-catalog";

import type { LaunchEdition, OfferArchetype } from "../types";

export interface ShouldShowVariantRailInput {
  /** Archetype of the offer — drives ``allow_single_variant`` lookup. */
  archetype: OfferArchetype | undefined;
  /** Current list of variants for the offer. Includes drafts + placeholders. */
  variants: readonly LaunchEdition[];
}

export interface ShouldShowVariantRailResult {
  /**
   * True when the rail should mount. The user sees a variant sidebar only
   * if the offer has >1 variant OR the archetype explicitly forbids the
   * single-variant-only flow.
   */
  shouldShow: boolean;
  /** Reason label useful for telemetry + debug tooltips. */
  reason:
    | "catalog-loading"
    | "archetype-forbids-single"
    | "multiple-variants"
    | "single-variant-allowed"
    | "no-variants";
}

/**
 * Decide whether the polymorphic ``VariantRail`` should mount for an offer.
 *
 * Product rules:
 *   1. If the archetype does NOT allow a single-variant-only flow
 *      (``allow_single_variant === false``) → always mount the rail. These
 *      offers always have ≥1 cohort/salida/convocatoria and need the
 *      switcher even when only one is published so the user can clone
 *      or create the next one.
 *   2. If the archetype allows single-variant AND the offer has exactly
 *      one variant → hide the rail. The editor edits the single implicit
 *      variant directly (lead-magnet / ebook UX).
 *   3. If the offer has >1 variant → mount the rail regardless of the
 *      archetype's default.
 *   4. While the archetype catalog is loading → hide the rail. The
 *      consumer decides whether to render a loading skeleton in its
 *      place; defaulting to "hide" avoids flashing an empty rail during
 *      hydration.
 *
 * Consumers pair this with a redirect helper — when ``shouldShow === false``,
 * the ``/offer/{id}/editions`` route should 302 to ``/offer/{id}/editor``
 * so users don't land on a management surface that doesn't apply to their
 * offer. See the companion ``buildNoVariantRedirect`` below.
 */
export function useShouldShowVariantRail(
  input: ShouldShowVariantRailInput,
): ShouldShowVariantRailResult {
  const capabilities = useArchetypeCapabilities(input.archetype);
  const variantCount = input.variants.length;

  return useMemo<ShouldShowVariantRailResult>(() => {
    if (!capabilities) {
      return { shouldShow: false, reason: "catalog-loading" };
    }
    if (variantCount === 0) {
      // Offers with no variants yet rely on the create-first flow inside
      // the editor; the rail empty-state is not mounted until at least
      // one placeholder variant exists (the backend creates one on offer
      // create, so this branch is rare but defensively handled).
      return { shouldShow: false, reason: "no-variants" };
    }
    if (variantCount > 1) {
      return { shouldShow: true, reason: "multiple-variants" };
    }
    if (capabilities.allow_single_variant) {
      return { shouldShow: false, reason: "single-variant-allowed" };
    }
    return { shouldShow: true, reason: "archetype-forbids-single" };
  }, [capabilities, variantCount]);
}

/**
 * Build the redirect path from ``/offer/{id}/editions*`` to
 * ``/offer/{id}/editor`` when the rail is hidden. Preserves the tenant
 * segment. Returns ``null`` when the input path isn't an editions path, so
 * callers can early-return without a branch.
 *
 * Used by the ``app/.../offer/[id]/editions/page.tsx`` guard and the
 * client-side ``useShouldShowVariantRail`` consumer that handles tab
 * visibility in the topbar.
 */
export function buildNoVariantRedirect(pathname: string): string | null {
  const match = /^(\/[^/]+\/offer-studio\/offer\/[^/]+)\/editions(?:\/.*)?$/.exec(pathname);
  if (!match) return null;
  return `${match[1]}/editor`;
}
