import { use } from "react";
import { OfferEditorLayout } from "@/components/offer-studio/layout/offer-editor-layout";
import { OfferSummaryForm } from "@/components/offer-studio/offer-summary-form";

export default function OfferSummaryPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  
  return (
    <OfferEditorLayout offerId={id}>
      <OfferSummaryForm offerId={id} />
    </OfferEditorLayout>
  );
}
