import { CampaignDetailClient } from "@/features/campaigns-lite/components/CampaignDetailClient";

interface PageProps {
  params: Promise<{ tenantId: string; id: string }>;
}

export const metadata = {
  title: "Campaña — Nicolify",
};

/**
 * Página de detalle de una campaña (Server Component thin).
 * S4 PI-1 lite scope: stats + lifecycle buttons.
 * PI-3 expand: full overview, analytics, task list.
 */
export default async function CampaignDetailPage({ params }: PageProps) {
  const { id } = await params;

  return (
    <div className="container mx-auto p-6">
      <CampaignDetailClient campaignId={id} />
    </div>
  );
}
