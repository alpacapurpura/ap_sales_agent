import { redirect } from "next/navigation";

import { getStageForChannel } from "@/features/growth-studio/lib/registries/channel-registry";

interface ChannelDashboardPageProps {
  params: Promise<{ tenantId: string; channelSlug: string }>;
  searchParams: Promise<{ tab?: string }>;
}

/**
 * Legacy route — redirects to the new nested stage route.
 * /[tenantId]/growth-studio/channel/[channelSlug]
 *   -> /[tenantId]/growth-studio/[stageSlug]/[channelSlug]
 */
export default async function ChannelDashboardPage({
  params,
  searchParams,
}: ChannelDashboardPageProps) {
  const { tenantId, channelSlug } = await params;
  const { tab } = await searchParams;
  const stageSlug = getStageForChannel(channelSlug);
  const tabQuery = tab ? `?tab=${encodeURIComponent(tab)}` : "";
  redirect(`/${tenantId}/growth-studio/${stageSlug}/${channelSlug}${tabQuery}`);
}
