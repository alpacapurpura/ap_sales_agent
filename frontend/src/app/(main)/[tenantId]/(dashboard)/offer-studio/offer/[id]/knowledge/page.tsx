"use client";

import { useOfferShell } from "@/features/offer-studio/context/OfferShellContext";
import { KnowledgeView } from "@/features/offer-studio/components/knowledge/KnowledgeView";

/**
 * Knowledge tab — rendered inside the persistent Offer Studio shell. The old
 * mock uploader + `OfferEditorLayout` wrapper has been retired; the shell
 * (`layout.tsx`) already owns the header, tab bar and chrome.
 */
export default function KnowledgePage() {
  const { offer } = useOfferShell();
  return <KnowledgeView offerId={offer.id} />;
}
