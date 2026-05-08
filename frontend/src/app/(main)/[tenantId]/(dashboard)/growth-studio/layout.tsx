"use client";

import { memo } from "react";

import { PageContainer } from "@/components/shared/layout/PageContainer";
import { ChannelConnectionModal } from "@/features/growth-studio/components/metrics-dashboard/channel-widgets/ChannelConnectionModal";
import { NoDataSidebarPanel } from "@/features/growth-studio/components/metrics-dashboard/channel-widgets/NoDataSidebarPanel";
import {
  GrowthStudioProvider,
  useGrowthStudioContext,
} from "@/features/growth-studio/components/metrics-dashboard/context/GrowthStudioContext";
import { useTier0Summary } from "@/features/growth-studio/pages/tiers/tier0-summary";
import { ChannelDetailSidebar } from "@/features/growth-studio/components/metrics-dashboard/sidebar/ChannelDetailSidebar";
import { MetricSidebar } from "@/features/growth-studio/components/metrics-dashboard/sidebar/MetricSidebar";
import { SidebarContent } from "@/features/growth-studio/components/metrics-dashboard/sidebar/SidebarContent";
import { StageSummaryRow } from "@/features/growth-studio/components/metrics-dashboard/stage-widgets/StageSummaryRow";
import { SyncProgressDialog } from "@/features/growth-studio/components/SyncProgressDialog";
import { GrowthSyncProvider } from "@/features/growth-studio/context/growth-sync-context";

const GrowthStudioShell = memo(function GrowthStudioShell({
  children,
}: {
  children: React.ReactNode;
}) {
  const {
    activeStage,
    sidebarMetric,
    sidebarOpen,
    selectedChannel,
    channelSidebarOpen,
    configureChannel,
    noDataChannel,
    pendingChannelTab,
    handleSidebarClose,
    handleChannelSidebarClose,
    handleCloseConfigure,
    handleCloseNoData,
  } = useGrowthStudioContext();

  const { enrichedSummaries, loadingMap, mockMap } = useTier0Summary();

  return (
    <PageContainer>
      <div className="flex-1 space-y-4">
        <div className="flex items-center justify-between space-y-2">
          <div>
            <h2 className="text-3xl font-bold tracking-tight">Growth Studio</h2>
            <p className="text-muted-foreground">Entiende tu negocio de un vistazo</p>
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

      <MetricSidebar isOpen={sidebarOpen} onClose={handleSidebarClose} metric={sidebarMetric}>
        <SidebarContent metric={sidebarMetric} stageId={sidebarMetric?.stageId ?? activeStage} />
      </MetricSidebar>

      <ChannelDetailSidebar
        isOpen={channelSidebarOpen}
        onClose={handleChannelSidebarClose}
        channel={selectedChannel}
        initialTab={pendingChannelTab}
      />

      <ChannelConnectionModal
        channelSlug={configureChannel?.slug ?? null}
        channelName={configureChannel?.name ?? ""}
        onClose={handleCloseConfigure}
      />

      <NoDataSidebarPanel
        isOpen={!!noDataChannel}
        onClose={handleCloseNoData}
        channel={noDataChannel}
      />
    </PageContainer>
  );
});

/**
 *
 */
export default function GrowthStudioLayout({ children }: { children: React.ReactNode }) {
  return (
    <GrowthStudioProvider>
      <GrowthSyncProvider>
        <GrowthStudioShell>{children}</GrowthStudioShell>
        <SyncProgressDialog />
      </GrowthSyncProvider>
    </GrowthStudioProvider>
  );
}
