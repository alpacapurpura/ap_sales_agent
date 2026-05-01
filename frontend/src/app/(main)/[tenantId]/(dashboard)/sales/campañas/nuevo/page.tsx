import { CampaignNewClient } from "@/features/campaigns-lite/components/CampaignNewClient";

interface PageProps {
  searchParams: Promise<{ segment_id?: string }>;
}

export const metadata = {
  title: "Nueva campaña — Nicolify",
};

/**
 * Página de creación de campaña (Server Component thin).
 * Recibe segment_id de searchParams → pasa a CampaignNewClient.
 */
export default async function CampaignNewPage({ searchParams }: PageProps) {
  const params = await searchParams;
  const segmentId = params.segment_id ?? null;

  return (
    <div className="container mx-auto p-6 max-w-2xl">
      <CampaignNewClient segmentId={segmentId} />
    </div>
  );
}
