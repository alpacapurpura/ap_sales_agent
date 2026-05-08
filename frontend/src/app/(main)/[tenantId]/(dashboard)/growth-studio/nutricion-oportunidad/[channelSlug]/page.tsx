import { notFound } from "next/navigation";

import { ChannelDispatcher } from "@/features/growth-studio/pages/ChannelDispatcher";
import { isGrowthStudioChannel } from "@/features/growth-studio/pages/channel-slugs";

interface ChannelDashboardPageProps {
  params: Promise<{ tenantId: string; channelSlug: string }>;
  searchParams: Promise<{ tab?: string }>;
}

/**
 * Server Component thin delegate para el dashboard de canal en Nutrición & Oportunidad.
 * Valida el slug en server y delega al ChannelDispatcher (Client Component).
 */
export default async function NutricionOportunidadChannelPage({
  params,
  searchParams,
}: ChannelDashboardPageProps) {
  const { channelSlug } = await params;
  const { tab } = await searchParams;

  if (!isGrowthStudioChannel(channelSlug)) {
    notFound();
  }

  return <ChannelDispatcher slug={channelSlug} initialTab={tab ?? "overview"} isRouteBased />;
}
