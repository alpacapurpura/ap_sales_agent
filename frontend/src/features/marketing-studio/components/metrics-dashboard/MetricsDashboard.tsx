'use client';

import type { StageId } from '../../types/metrics';
import { StageSummaryRow } from './stage-widgets/StageSummaryRow';
import { AttractionCaptureDetail } from './detail-panels/AttractionCaptureDetail';
import { NurtureOpportunityDetail } from './detail-panels/NurtureOpportunityDetail';
import { SalesDetail } from './detail-panels/SalesDetail';
import { AdoptionDetail } from './detail-panels/AdoptionDetail';
import { ExpansionEvangelizationDetail } from './detail-panels/ExpansionEvangelizationDetail';
import { PlaceholderDetail } from './detail-panels/PlaceholderDetail';
import MetricSidebar from './sidebar/MetricSidebar';
import { SidebarContent } from './sidebar/SidebarContent';
import { ChannelConnectionModal } from './channel-widgets/ChannelConnectionModal';
import { useMetricsDashboard } from './hooks/useMetricsDashboard';

export function MetricsDashboard() {
  const {
    activeStage,
    activeStageData,
    enrichedSummaries,
    loadingMap,
    mockMap,
    sidebarMetric,
    sidebarOpen,
    configureChannel,
    handleStageClick,
    handleMetricClick,
    handleSidebarClose,
    handleConfigure,
    handleCloseConfigure,
  } = useMetricsDashboard();

  // Map to dynamically render the correct detail panel based on the active stage
  const renderDetailPanel = () => {
    if (!activeStage || !activeStageData) return null;

    const panelProps = {
      onMetricClick: handleMetricClick,
      onConfigure: handleConfigure,
    };

    switch (activeStage) {
      case 'ATRACCION_CAPTURA':
        return <AttractionCaptureDetail {...panelProps} />;
      case 'NUTRICION_OPORTUNIDAD':
        return <NurtureOpportunityDetail {...panelProps} />;
      case 'VENTAS':
        return <SalesDetail onMetricClick={handleMetricClick} />;
      case 'ADOPCION':
        return <AdoptionDetail onMetricClick={handleMetricClick} />;
      case 'EXPANSION_EVANGELIZACION':
        return <ExpansionEvangelizationDetail onMetricClick={handleMetricClick} />;
      default:
        return <PlaceholderDetail stage={activeStageData} />;
    }
  };

  return (
    <>
      <div className="space-y-4">
        <StageSummaryRow
          stages={enrichedSummaries}
          activeStage={activeStage}
          onStageClick={handleStageClick}
          onMetricClick={handleMetricClick}
          loadingMap={loadingMap}
          mockMap={mockMap}
        />

        {renderDetailPanel()}
      </div>

      {/* Metric drill-down sidebar — renders polymorphic SidebarContent per stageId */}
      <MetricSidebar
        isOpen={sidebarOpen}
        onClose={handleSidebarClose}
        metric={sidebarMetric}
      >
        <SidebarContent metric={sidebarMetric} stageId={sidebarMetric?.stageId ?? activeStage} />
      </MetricSidebar>

      <ChannelConnectionModal
        channelSlug={configureChannel?.slug ?? null}
        channelName={configureChannel?.name ?? ''}
        onClose={handleCloseConfigure} 
      />
    </>
  );
}