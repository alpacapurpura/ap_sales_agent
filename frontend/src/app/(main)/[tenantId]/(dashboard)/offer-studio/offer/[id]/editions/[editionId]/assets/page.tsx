"use client";

import { AssetsView } from "@/features/offer-studio/components/assets/AssetsView";
import { useOfferShell } from "@/features/offer-studio/context/OfferShellContext";

/**
 * Assets scoped to a specific edition. `AssetsView` today renders offer-wide
 * assets; per-edition asset filtering is tracked as a follow-up (needs
 * backend `edition_id` filter on the assets list endpoint).
 */
export default function EditionAssetsPage() {
  const { offer } = useOfferShell();
  return <AssetsView offerId={offer.id} />;
}
