import { redirect } from "next/navigation";

interface PageProps {
  params: Promise<{ tenantId: string }>;
  searchParams: Promise<{ offerId?: string; session?: string }>;
}

export default async function OfferInterviewPage({ params, searchParams }: PageProps) {
  const { tenantId } = await params;
  const { session, offerId } = await searchParams;

  // Redirect to offer editor/dashboard with interview query param for sidebar activation
  const base = offerId ? `/${tenantId}/offer-studio/offer/${offerId}` : `/${tenantId}/offer-studio`;

  const target = session ? `${base}?interview=${session}` : base;

  redirect(target);
}
