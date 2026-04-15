"use client";

import { AssetsView } from "@/features/offer-studio/components/assets/assets-view";
import { useOfferShell } from "@/features/offer-studio/components/container/offer-shell";

/**
 * Assets tab — rendered inside the persistent Offer Studio shell. Reads the
 * offer id from `useOfferShell()` so the shell doesn't refetch.
 */
export default function AssetsPage() {
  const { offer } = useOfferShell();
  return <AssetsView offerId={offer.id} />;
}
