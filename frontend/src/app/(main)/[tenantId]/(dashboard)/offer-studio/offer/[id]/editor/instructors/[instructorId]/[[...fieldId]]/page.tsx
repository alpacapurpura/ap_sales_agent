import { OfferInstructorDetailPage } from "@/features/offer-studio/components/collections/OfferInstructorDetailPage";

/**
 *
 */
export default async function OfferEditorInstructorDetailPage({
  params,
}: {
  params: Promise<{ tenantId: string; id: string; instructorId: string; fieldId?: string[] }>;
}) {
  const { id: offerId, instructorId } = await params;
  return <OfferInstructorDetailPage offerId={offerId} instructorId={instructorId} />;
}
