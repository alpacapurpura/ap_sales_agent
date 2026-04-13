// Side-effect import: registers offer preview in the PreviewRegistry
import "@/features/offer-studio/components/interview/register-offer-preview";

import { InterviewSplitView } from "@/features/copilot/components/interview/interview-split-view";

interface PageProps {
  searchParams: Promise<{ offerId?: string; session?: string }>;
}

export default async function OfferInterviewPage({
  searchParams,
}: PageProps) {
  const params = await searchParams;
  return (
    <InterviewSplitView
      domain="offer"
      sessionId={params.session}
      entityId={params.offerId}
      routeBase="offer-studio/interview"
    />
  );
}
