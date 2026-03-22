import { LandingPageEditor } from "@/features/offer-studio/components/landing/components/editor/landing-editor";

export default async function FullScreenEditorPage({ params }: { params: Promise<{ tenantId: string; offerId: string }> }) {
  const { offerId } = await params;
  return <LandingPageEditor offerId={offerId} />;
}
