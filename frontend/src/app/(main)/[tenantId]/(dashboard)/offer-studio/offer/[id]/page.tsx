"use client";

import { use } from "react";
import ErrorBoundary from "@/components/shared/error-boundary";
import { OfferEditorContent } from "@/features/offer-studio/components/editor/offer-editor-content";

/**
 * Editor tab — rendered inside the persistent shell (see `layout.tsx`).
 *
 * The shell owns the header rows, tab bar and lifecycle widgets. This page
 * renders ONLY the inner section list + live preview. The legacy
 * `<OfferStudioLayout>` wrapper has been retired.
 */
export default function OfferEditorPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return (
    <ErrorBoundary>
      <OfferEditorContent offerId={id} />
    </ErrorBoundary>
  );
}
