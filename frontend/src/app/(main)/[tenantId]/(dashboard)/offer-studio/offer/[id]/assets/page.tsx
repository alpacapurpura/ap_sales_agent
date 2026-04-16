"use client";

import { AssetsView } from "@/features/offer-studio/components/assets/AssetsView";
import { useOfferShell } from "@/features/offer-studio/context/OfferShellContext";

/**
 * Assets tab — rendered inside the persistent Offer Studio shell. Reads the
 * offer id from `useOfferShell()` so the shell doesn't refetch.
 */
export default function AssetsPage() {
  const { offer } = useOfferShell();
  return <AssetsView offerId={offer.id} />;
}
