import ErrorBoundary from "@/components/shared/error-boundary";
import { OfferEditorClient } from "@/features/offer-studio/components/editor/offer-editor-client";

export default async function OfferPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = await params;
  return (
    <ErrorBoundary>
      <OfferEditorClient offerId={resolvedParams.id} />
    </ErrorBoundary>
  );
}
