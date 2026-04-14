import { ChannelDashboardView } from "@/features/growth-studio/components/metrics-dashboard/sidebar/ChannelDashboardView";

interface ChannelDashboardPageProps {
  params: Promise<{ tenantId: string; channelSlug: string }>;
  searchParams: Promise<{ tab?: string }>;
}

export default async function ExpansionEvangelizacionChannelPage({
  params,
  searchParams,
}: ChannelDashboardPageProps) {
  const { channelSlug } = await params;
  const { tab } = await searchParams;
  return <ChannelDashboardView channelSlug={channelSlug} initialTab={tab ?? "overview"} />;
}
