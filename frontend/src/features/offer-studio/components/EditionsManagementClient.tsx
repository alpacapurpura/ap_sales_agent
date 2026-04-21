"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { useEditions } from "../hooks/use-editions";
import { useOffer } from "../hooks/use-offer";
import { useShouldShowVariantRail } from "../hooks/use-should-show-variant-rail";

import { VariantCollectionLandingPage } from "./variant/VariantCollectionLandingPage";

export interface EditionsManagementClientProps {
  offerId: string;
  tenantId: string;
}

/**
 * Client wrapper for the editions management tab. Handles:
 *
 *   - Loading state (offer + editions resolve independently).
 *   - Guard: if the offer only ever has one variant
 *     (``archetype.allow_single_variant + variants.length === 1``),
 *     redirects to ``/editor``. Server-side redirect would need to call
 *     the archetype catalog endpoint too, so we defer to the client once
 *     React Query has warmed the cache.
 *   - Mount: ``VariantCollectionLandingPage`` with polymorphic card
 *     rendering (noun adapts per variant_structure).
 */
export function EditionsManagementClient({ offerId, tenantId }: EditionsManagementClientProps) {
  const router = useRouter();
  const { offer, loading: offerLoading } = useOffer(offerId);
  const { editions } = useEditions(offerId);
  const { shouldShow } = useShouldShowVariantRail({
    archetype: offer?.archetype,
    variants: editions,
  });

  useEffect(() => {
    if (offerLoading) return;
    if (!offer) return;
    if (!shouldShow) {
      router.replace(`/${tenantId}/offer-studio/offer/${offerId}/editor`);
    }
  }, [offer, offerLoading, shouldShow, router, tenantId, offerId]);

  if (offerLoading || !offer) {
    return (
      <div className="flex h-64 items-center justify-center text-sm text-muted-foreground">
        Cargando ediciones…
      </div>
    );
  }

  if (!shouldShow) {
    return (
      <div className="flex h-64 items-center justify-center text-sm text-muted-foreground">
        Redirigiendo al editor…
      </div>
    );
  }

  return (
    <VariantCollectionLandingPage
      variants={editions}
      offerName={offer.public_name ?? "Oferta"}
      onCreate={() => {
        // TODO(F4): Wire to the real create-variant flow from useEditions.
      }}
      onEdit={(v) => router.push(`/${tenantId}/offer-studio/offer/${offerId}/editions/${v.id}`)}
      onDuplicate={() => {
        // TODO(F4): Wire to the real duplicate-variant flow.
      }}
      onDelete={() => {
        // TODO(F4): Wire to the real delete-variant flow.
      }}
    />
  );
}
