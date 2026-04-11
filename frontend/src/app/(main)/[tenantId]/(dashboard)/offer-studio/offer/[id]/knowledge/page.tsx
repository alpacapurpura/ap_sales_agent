"use client";

import { useOfferShell } from "@/features/offer-studio/components/container/offer-shell";
import { KnowledgeView } from "@/features/offer-studio/components/knowledge/knowledge-view";

/**
 * Knowledge tab — rendered inside the persistent Offer Studio shell. The old
 * mock uploader + `OfferEditorLayout` wrapper has been retired; the shell
 * (`layout.tsx`) already owns the header, tab bar and chrome.
 */
export default function KnowledgePage() {
  const { offer } = useOfferShell();
  return <KnowledgeView offerId={offer.id} />;
}
