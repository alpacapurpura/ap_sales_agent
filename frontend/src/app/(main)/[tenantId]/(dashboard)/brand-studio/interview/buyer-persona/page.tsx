// Side-effect import: registers buyer_persona preview in the PreviewRegistry
import "@/features/brand/components/interview/previews/register-persona-preview";

import { InterviewSplitView } from "@/features/copilot/components/interview/interview-split-view";

interface PageProps {
  searchParams: Promise<{ personaId?: string; session?: string }>;
}

export default async function BuyerPersonaInterviewPage({
  searchParams,
}: PageProps) {
  const params = await searchParams;
  return (
    <InterviewSplitView
      domain="buyer_persona"
      sessionId={params.session}
      entityId={params.personaId}
      routeBase="brand-studio/interview/buyer-persona"
    />
  );
}
