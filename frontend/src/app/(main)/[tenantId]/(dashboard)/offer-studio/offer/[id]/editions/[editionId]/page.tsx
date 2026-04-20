"use client";

import { use } from "react";

import { ErrorBoundary } from "@/components/shared/ErrorBoundary";
import { OfferEditorContent } from "@/features/offer-studio/components/editor/OfferEditorContent";

/**
 * Edition's Info view. Content is offer-level (identity, strategy,
 * deliverables, pricing, knowledge…) — we keep the edition in the URL so
 * the rail highlight persists when the user navigates to or from a tab.
 */
export default function EditionInfoPage({
  params,
}: {
  params: Promise<{ id: string; editionId: string }>;
}) {
  const { id } = use(params);
  return (
    <ErrorBoundary>
      <OfferEditorContent offerId={id} />
    </ErrorBoundary>
  );
}
