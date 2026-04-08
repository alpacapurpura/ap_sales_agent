'use client';

import dynamic from 'next/dynamic';
import { Skeleton } from '@/components/ui/skeleton';

const DashboardSkeleton = () => (
  <div className="flex flex-col gap-4 p-6">
    <Skeleton className="h-8 w-48" />
    <Skeleton className="h-64 w-full" />
  </div>
);

const IgOrganicDashboard = dynamic(
  () => import('./ig-organic/IgOrganicDashboard').then(m => ({ default: m.IgOrganicDashboard })),
  { ssr: false, loading: DashboardSkeleton },
);
const MetaAdsDashboard = dynamic(
  () => import('./meta-ads/MetaAdsDashboard').then(m => ({ default: m.MetaAdsDashboard })),
  { ssr: false, loading: DashboardSkeleton },
);
const YouTubeDashboard = dynamic(
  () => import('./youtube-organic/YouTubeDashboard').then(m => ({ default: m.YouTubeDashboard })),
  { ssr: false, loading: DashboardSkeleton },
);
const MailDashboard = dynamic(
  () => import('./mail/MailDashboard').then(m => ({ default: m.MailDashboard })),
  { ssr: false, loading: DashboardSkeleton },
);

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
  if (channelSlug === 'yt-organic') {
    return <YouTubeDashboard initialTab={initialTab} isRouteBased />;
  }
  if (channelSlug === 'email-nurture') {
    return <MailDashboard initialTab={initialTab} isRouteBased />;
  }
  return <div className="flex items-center justify-center py-24 text-sm text-muted-foreground">Dashboard no disponible para este canal</div>;
}
