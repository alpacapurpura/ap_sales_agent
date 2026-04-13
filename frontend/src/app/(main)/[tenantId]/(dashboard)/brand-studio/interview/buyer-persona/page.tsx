import { redirect } from "next/navigation";

interface PageProps {
  params: Promise<{ tenantId: string }>;
  searchParams: Promise<{ personaId?: string; session?: string }>;
}

export default async function BuyerPersonaInterviewPage({
  params,
  searchParams,
}: PageProps) {
  const { tenantId } = await params;
  const { session, personaId } = await searchParams;

  // Redirect to brand-studio with interview query param for sidebar activation
  const query = new URLSearchParams();
  if (session) query.set("interview", session);
  if (personaId) query.set("personaId", personaId);
  query.set("domain", "buyer_persona");

  const qs = query.toString();
  const target = `/${tenantId}/brand-studio${qs ? `?${qs}` : ""}`;

  redirect(target);
}
