import { LandingPageEditor } from "@/features/landing-builder/components/editor/landing-editor";

export default async function FullScreenEditorPage({ params }: { params: Promise<{ offerId: string }> }) {
  const { offerId } = await params;
  return <LandingPageEditor offerId={offerId} />;
}
