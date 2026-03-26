'use client';

import { GrowthStudioProvider, useGrowthStudioContext } from '@/features/growth-studio/components/metrics-dashboard/context/GrowthStudioContext';
import { StageSummaryRow } from '@/features/growth-studio/components/metrics-dashboard/stage-widgets/StageSummaryRow';
import { useStageSummaries } from '@/features/growth-studio/components/metrics-dashboard/hooks/useStageSummaries';
import MetricSidebar from '@/features/growth-studio/components/metrics-dashboard/sidebar/MetricSidebar';
import ChannelDetailSidebar from '@/features/growth-studio/components/metrics-dashboard/sidebar/ChannelDetailSidebar';
import { SidebarContent } from '@/features/growth-studio/components/metrics-dashboard/sidebar/SidebarContent';
import { ChannelConnectionModal } from '@/features/growth-studio/components/metrics-dashboard/channel-widgets/ChannelConnectionModal';

function GrowthStudioShell({ children }: { children: React.ReactNode }) {
  const {
    activeStage,
    sidebarMetric,
    sidebarOpen,
    selectedChannel,
    channelSidebarOpen,
    configureChannel,
    handleSidebarClose,
    handleChannelSidebarClose,
    handleCloseConfigure,
  } = useGrowthStudioContext();

  const { enrichedSummaries, loadingMap, mockMap } = useStageSummaries();

  return (
    <>
      <div className="flex-1 space-y-4">
        <div className="flex items-center justify-between space-y-2">
          <div>
            <h2 className="text-3xl font-bold tracking-tight">Growth Studio</h2>
            <p className="text-muted-foreground">
              Entiende tu negocio de un vistazo
            </p>
          </div>
        </div>

        <div className="space-y-4">
          <StageSummaryRow
            stages={enrichedSummaries}
            activeStage={activeStage}
            loadingMap={loadingMap}
            mockMap={mockMap}
          />
          {children}
        </div>
      </div>

      <MetricSidebar
        isOpen={sidebarOpen}
        onClose={handleSidebarClose}
        metric={sidebarMetric}
      >
        <SidebarContent metric={sidebarMetric} stageId={sidebarMetric?.stageId ?? activeStage} />
      </MetricSidebar>

      <ChannelDetailSidebar
        isOpen={channelSidebarOpen}
        onClose={handleChannelSidebarClose}
        channel={selectedChannel}
      />

      <ChannelConnectionModal
        channelSlug={configureChannel?.slug ?? null}
        channelName={configureChannel?.name ?? ''}
        onClose={handleCloseConfigure}
      />
    </>
  );
}

export default function GrowthStudioLayout({ children }: { children: React.ReactNode }) {
  return (
    <GrowthStudioProvider>
      <GrowthStudioShell>{children}</GrowthStudioShell>
    </GrowthStudioProvider>
  );
}
