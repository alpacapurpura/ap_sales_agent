import { redirect } from "next/navigation";

interface PageProps {
  params: Promise<{ tenantId: string }>;
  searchParams: Promise<{ session?: string }>;
}

export default async function InterviewPage({ params, searchParams }: PageProps) {
  const { tenantId } = await params;
  const { session } = await searchParams;

  // Redirect to brand-studio with interview query param for sidebar activation
  const target = session
    ? `/${tenantId}/brand-studio?interview=${session}`
    : `/${tenantId}/brand-studio`;

  redirect(target);
}
