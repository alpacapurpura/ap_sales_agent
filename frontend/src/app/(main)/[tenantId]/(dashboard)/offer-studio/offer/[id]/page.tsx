import { DynamicOfferEditor } from "@/features/offer-studio/components/DynamicOfferEditor";

export default async function OfferPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = await params;
  return <DynamicOfferEditor offerId={resolvedParams.id} />;
}
