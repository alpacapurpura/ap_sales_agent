import { OfferFaqDetailPage } from "@/features/offer-studio/components/collections/OfferFaqDetailPage";

export default async function OfferEditorFaqDetailPage({
  params,
}: {
  params: Promise<{ tenantId: string; id: string; faqId: string; fieldId?: string[] }>;
}) {
  const { id: offerId, faqId } = await params;
  return <OfferFaqDetailPage offerId={offerId} faqId={faqId} />;
}
