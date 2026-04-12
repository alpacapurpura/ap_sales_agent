import { InterviewSplitView } from "@/features/brand/components/interview/interview-split-view";

interface PageProps {
  searchParams: Promise<{ session?: string }>;
}

export default async function InterviewPage({ searchParams }: PageProps) {
  const params = await searchParams;
  return <InterviewSplitView sessionId={params.session} />;
}
