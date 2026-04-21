"use client";

import { useCallback, useMemo } from "react";

import { useOffer } from "./use-offer";
import { useOfferWithEdition } from "./use-offer-with-edition";

import type { SectionKey } from "../api/archetype-catalog-api";
import type { OfferFormValues } from "../types/schema";

/**
 * Aggregator hook mirroring ``useBrandSettings`` contract for offer-studio
 * section pages.
 *
 * Offer-studio differs from brand-studio in two ways:
 *
 *  1. **Save shape:** brand-studio persists a single ``BrandSettings`` root
 *     object; offer-studio persists per-section subsets via
 *     ``POST /offers/{id}/sections/{sectionId}``. The aggregator hides this
 *     by exposing a single ``settings`` blob (the offer rendered as form
 *     values) + per-section updaters that internally call
 *     ``saveSection(sectionKey, mergedValues)``.
 *
 *  2. **Edition context:** offers can host multiple editions; the active
 *     edition is resolved from the URL by ``useOfferWithEdition``. This
 *     hook surfaces it so pages can render edition-scoped overrides
 *     without reaching into useParams themselves.
 *
 * Consumers (section-pages factory, copilot sidebar, preview panes) only
 * see the brand-aligned contract:
 *
 *   const { settings, updateIdentity, updatePromise, ... } = useOfferSettings(offerId);
 *
 * Any future migration away from section-subset persistence (toward a
 * single PATCH /offers/{id}) only has to touch this file.
 */
export function useOfferSettings(offerId: string) {
  const { offer, formValues, loading, saving, error, saveSection, saveOffer, refetch } =
    useOffer(offerId);

  const edition = useOfferWithEdition(offerId);

  /**
   * Build a per-section updater that merges the incoming slice into the
   * current form values, then persists via ``saveSection``. Returns a
   * stable reference per ``sectionKey`` so React Query retries don't
   * trigger unnecessary re-renders in the factory-generated pages.
   */
  const makeUpdater = useCallback(
    (sectionKey: SectionKey) => {
      return async (slice: Partial<OfferFormValues>): Promise<void> => {
        if (!formValues) return;
        const next: OfferFormValues = { ...formValues, ...slice };
        await saveSection(sectionKey, next);
      };
    },
    [formValues, saveSection],
  );

  // Named updaters — one per singleton section whose data lives on the
  // Offer root (not a sub-entity). Collection sections (testimonials,
  // instructors, faq, assets) have their own dedicated hooks.
  const updateIdentity = useMemo(() => makeUpdater("identity"), [makeUpdater]);
  const updatePromise = useMemo(() => makeUpdater("promise"), [makeUpdater]);
  const updateStrategy = useMemo(() => makeUpdater("strategy"), [makeUpdater]);
  const updatePsychology = useMemo(() => makeUpdater("psychology"), [makeUpdater]);
  const updatePricing = useMemo(() => makeUpdater("pricing"), [makeUpdater]);
  const updateClosing = useMemo(() => makeUpdater("closing"), [makeUpdater]);
  const updateValueStack = useMemo(() => makeUpdater("value_stack"), [makeUpdater]);
  const updateProgramDetails = useMemo(() => makeUpdater("program_details"), [makeUpdater]);
  const updateProductDetails = useMemo(() => makeUpdater("product_details"), [makeUpdater]);
  const updateServiceDetails = useMemo(() => makeUpdater("service_details"), [makeUpdater]);
  const updateEventDetails = useMemo(() => makeUpdater("event_details"), [makeUpdater]);
  const updateSubscriptionDetails = useMemo(
    () => makeUpdater("subscription_details"),
    [makeUpdater],
  );
  const updatePlatformDetails = useMemo(() => makeUpdater("platform_details"), [makeUpdater]);
  const updateLocation = useMemo(() => makeUpdater("location"), [makeUpdater]);

  return {
    /** Current offer rendered as form values (null while loading or on error). */
    settings: formValues ?? null,
    /** Raw offer domain object for consumers that need non-form shapes (status, preset_id, …). */
    offer,
    /** Edition context resolved from the URL. Null when offer has no editions. */
    edition: edition.currentEdition,
    editionId: edition.currentEditionId,
    editions: edition.editions,

    loading: loading || edition.loading,
    saving,
    error,

    updateIdentity,
    updatePromise,
    updateStrategy,
    updatePsychology,
    updatePricing,
    updateClosing,
    updateValueStack,
    updateProgramDetails,
    updateProductDetails,
    updateServiceDetails,
    updateEventDetails,
    updateSubscriptionDetails,
    updatePlatformDetails,
    updateLocation,

    /** Escape hatch for flows that touch multiple sections atomically. */
    saveOffer,
    refetch,
  };
}

export type UseOfferSettingsHook = ReturnType<typeof useOfferSettings>;
