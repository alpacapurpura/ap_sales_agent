import { OfferEditor } from "@/features/offer-studio/components/offer-editor";

export default async function OfferPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = await params;
  return <OfferEditor offerId={resolvedParams.id} />;
}
