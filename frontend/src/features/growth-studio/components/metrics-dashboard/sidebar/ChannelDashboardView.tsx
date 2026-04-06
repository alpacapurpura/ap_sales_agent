'use client';

import { IgOrganicDashboard } from './ig-organic/IgOrganicDashboard';
import { MetaAdsDashboard } from './meta-ads/MetaAdsDashboard';

interface ChannelDashboardViewProps {
  channelSlug: string;
  initialTab?: string;
}

export function ChannelDashboardView({ channelSlug, initialTab }: ChannelDashboardViewProps) {
  if (channelSlug === 'ig-organic') {
    return <IgOrganicDashboard initialTab={initialTab} isRouteBased />;
  }
  if (channelSlug === 'meta-ads') {
    return <MetaAdsDashboard onClose={() => window.history.back()} />;
  }
  return <div className="flex items-center justify-center py-24 text-sm text-muted-foreground">Dashboard no disponible para este canal</div>;
}
