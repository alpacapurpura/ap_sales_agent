'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { StageId, StageSummary, MetricClickData } from '../../types/metrics';
import { STAGE_SUMMARIES } from '../../api/metrics-mock-data';
import { StageSummaryRow } from './StageSummaryRow';
import { AttractionDetail } from './detail-panels/AttractionDetail';
import { CaptureDetail } from './detail-panels/CaptureDetail';
import { NurtureDetail } from './detail-panels/NurtureDetail';
import { OpportunityDetail } from './detail-panels/OpportunityDetail';
import { SalesDetail } from './detail-panels/SalesDetail';
import { AdoptionDetail } from './detail-panels/AdoptionDetail';
import { ExpansionDetail } from './detail-panels/ExpansionDetail';
import { EvangelizationDetail } from './detail-panels/EvangelizationDetail';
import { PlaceholderDetail } from './detail-panels/PlaceholderDetail';
import MetricSidebar from './MetricSidebar';
import { SidebarContent } from './sidebar/SidebarContent';

// Parallel per-stage hooks — all called unconditionally on mount (React Query deduplicates)
import { useAttractionDetail } from '../../hooks/useAttractionDetail';
import { useCaptureDetail } from '../../hooks/useCaptureDetail';
import { useNurtureDetail } from '../../hooks/useNurtureDetail';
import { useOpportunityDetail } from '../../hooks/useOpportunityDetail';
import { useSalesDetail } from '../../hooks/useSalesDetail';
import { useAdoptionDetail } from '../../hooks/useAdoptionDetail';
import { useExpansionDetail } from '../../hooks/useExpansionDetail';
import { useEvangelizationDetail } from '../../hooks/useEvangelizationDetail';

/**
 * Derives a StageSummary from a per-stage detail API response, merging with the
 * mock StageSummary baseline when the API has not yet returned data.
 *
 * Progressive loading: each stage updates independently as its hook resolves.
 */
function mergeStageData(
  base: StageSummary,
  apiData: unknown,
  isLoading: boolean,
  isError: boolean
): { summary: StageSummary; isLoading: boolean; isMock: boolean } {
  // If we have real API data, extract the main KPI based on stage id
  if (apiData != null && !isError) {
    const data = apiData as Record<string, unknown>;
    const kpis = (data.headerKpis ?? {}) as Record<string, unknown>;
    const miniFunnel = (data.miniFunnel ?? {}) as Record<string, unknown>;

    // Map each stage to its primary KPI field from backend
    let mainValue: number = base.mainKpi.value as number;
    let mainLabel: string = base.mainKpi.label;
    let mainUnit: string | undefined = base.mainKpi.unit;
    let secondaryValue: number = base.secondaryKpi.value as number;
    let secondaryUnit: string | undefined = base.secondaryKpi.unit;

    switch (base.id) {
      case 'ATRACCION': {
        // Sum totals across all group totals for total visitors
        const groups = ['organicSocial', 'ga4Search', 'paid', 'outbound'] as const;
        let totalVisitors = 0;
        for (const g of groups) {
          const group = (data[g] ?? {}) as Record<string, unknown>;
          const totals = (group.totals ?? {}) as Record<string, number>;
          totalVisitors += totals.visitors ?? totals.totalVisitors ?? 0;
        }
        if (totalVisitors > 0) {
          mainValue = totalVisitors;
          mainLabel = 'visitantes';
          mainUnit = undefined;
        }
        // No conversion rate for Stage 0; secondary = channels connected count (keep mock)
        break;
      }
      case 'CAPTURA': {
        const captured = (kpis.totalLeads ?? base.mainKpi.value) as number;
        const rate = (kpis.conversionRate ?? (miniFunnel.conversionRate ?? 0)) as number;
        mainValue = captured;
        mainLabel = 'leads';
        mainUnit = undefined;
        secondaryValue = rate;
        secondaryUnit = '%';
        break;
      }
      case 'NUTRICION': {
        const mqls = (kpis.totalMqls ?? base.mainKpi.value) as number;
        const rate = (kpis.conversionRate ?? (miniFunnel.conversionRate ?? 0)) as number;
        mainValue = mqls;
        mainLabel = 'MQLs';
        mainUnit = undefined;
        secondaryValue = rate;
        secondaryUnit = '%';
        break;
      }
      case 'OPORTUNIDAD': {
        const sqls = (kpis.totalSqls ?? base.mainKpi.value) as number;
        const rate = (kpis.conversionRate ?? (miniFunnel.conversionRate ?? 0)) as number;
        mainValue = sqls;
        mainLabel = 'SQLs';
        mainUnit = undefined;
        secondaryValue = rate;
        secondaryUnit = '%';
        break;
      }
      case 'VENTAS': {
        const revenue = (kpis.totalRevenue ?? base.mainKpi.value) as number;
        const newCust = (kpis.newCustomers ?? 0) as number;
        const rate = (miniFunnel.conversionRate ?? 0) as number;
        mainValue = revenue;
        mainLabel = 'revenue';
        mainUnit = '$';
        secondaryValue = rate > 0 ? rate : newCust;
        secondaryUnit = rate > 0 ? '%' : undefined;
        break;
      }
      case 'ADOPCION': {
        const health = (kpis.healthPct ?? base.mainKpi.value) as number;
        const active = (kpis.activeCustomers ?? 0) as number;
        const rate = (miniFunnel.conversionRate ?? 0) as number;
        mainValue = health;
        mainLabel = 'salud %';
        mainUnit = '%';
        secondaryValue = rate > 0 ? rate : active;
        secondaryUnit = rate > 0 ? '%' : undefined;
        break;
      }
      case 'EXPANSION': {
        const netMrr = (kpis.netMrr ?? base.mainKpi.value) as number;
        const rate = (kpis.churnRatePct ?? (miniFunnel.conversionRate ?? 0)) as number;
        mainValue = netMrr;
        mainLabel = 'net MRR';
        mainUnit = '$';
        secondaryValue = rate;
        secondaryUnit = '%';
        break;
      }
      case 'EVANGELIZACION': {
        const kFactor = (kpis.kFactor ?? base.mainKpi.value) as number;
        const rate = (miniFunnel.conversionRate ?? 0) as number;
        mainValue = kFactor;
        mainLabel = 'k-factor';
        mainUnit = undefined;
        secondaryValue = rate;
        secondaryUnit = rate > 0 ? '%' : undefined;
        break;
      }
    }

    return {
      summary: {
        ...base,
        mainKpi: { label: mainLabel, value: mainValue, unit: mainUnit },
        secondaryKpi: { label: base.secondaryKpi.label, value: secondaryValue, unit: secondaryUnit },
      },
      isLoading: false,
      isMock: false,
    };
  }

  return {
    summary: base,
    isLoading,
    isMock: !isLoading, // if not loading and no data, we're showing fallback mock
  };
}

export function MetricsDashboard() {
  const [activeStage, setActiveStage] = useState<StageId | null>('ATRACCION');

  // Sidebar state — metric drill-down wired to detail panels
  const [sidebarMetric, setSidebarMetric] = useState<MetricClickData | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // All 8 stage hooks called in parallel — React Query handles deduplication
  const { data: attractionData, isLoading: attractionLoading, error: attractionError } = useAttractionDetail();
  const { data: captureData, isLoading: captureLoading, error: captureError } = useCaptureDetail();
  const { data: nurtureData, isLoading: nurtureLoading, error: nurtureError } = useNurtureDetail();
  const { data: opportunityData, isLoading: opportunityLoading, error: opportunityError } = useOpportunityDetail();
  const { data: salesData, isLoading: salesLoading, error: salesError } = useSalesDetail();
  const { data: adoptionData, isLoading: adoptionLoading, error: adoptionError } = useAdoptionDetail();
  const { data: expansionData, isLoading: expansionLoading, error: expansionError } = useExpansionDetail();
  const { data: evangelizationData, isLoading: evangelizationLoading, error: evangelizationError } = useEvangelizationDetail();

  // Build a progressive StageSummary[] — each stage updates independently as hooks resolve
  const baseSummaries = STAGE_SUMMARIES;

  const { summary: atraccionSummary, isLoading: atraccionIsLoading, isMock: atraccionIsMock } =
    mergeStageData(baseSummaries[0], attractionData, attractionLoading, !!attractionError);
  const { summary: capturaSummary, isLoading: capturaIsLoading, isMock: capturaIsMock } =
    mergeStageData(baseSummaries[1], captureData, captureLoading, !!captureError);
  const { summary: nutricionSummary, isLoading: nutricionIsLoading, isMock: nutricionIsMock } =
    mergeStageData(baseSummaries[2], nurtureData, nurtureLoading, !!nurtureError);
  const { summary: oportunidadSummary, isLoading: oportunidadIsLoading, isMock: oportunidadIsMock } =
    mergeStageData(baseSummaries[3], opportunityData, opportunityLoading, !!opportunityError);
  const { summary: ventasSummary, isLoading: ventasIsLoading, isMock: ventasIsMock } =
    mergeStageData(baseSummaries[4], salesData, salesLoading, !!salesError);
  const { summary: adopcionSummary, isLoading: adopcionIsLoading, isMock: adopcionIsMock } =
    mergeStageData(baseSummaries[5], adoptionData, adoptionLoading, !!adoptionError);
  const { summary: expansionSummary, isLoading: expansionIsLoading, isMock: expansionIsMock } =
    mergeStageData(baseSummaries[6], expansionData, expansionLoading, !!expansionError);
  const { summary: evangelizacionSummary, isLoading: evangelizacionIsLoading, isMock: evangelizacionIsMock } =
    mergeStageData(baseSummaries[7], evangelizationData, evangelizationLoading, !!evangelizationError);

  const enrichedSummaries = [
    atraccionSummary, capturaSummary, nutricionSummary, oportunidadSummary,
    ventasSummary, adopcionSummary, expansionSummary, evangelizacionSummary,
  ];

  const loadingMap: Record<StageId, boolean> = {
    ATRACCION: atraccionIsLoading,
    CAPTURA: capturaIsLoading,
    NUTRICION: nutricionIsLoading,
    OPORTUNIDAD: oportunidadIsLoading,
    VENTAS: ventasIsLoading,
    ADOPCION: adopcionIsLoading,
    EXPANSION: expansionIsLoading,
    EVANGELIZACION: evangelizacionIsLoading,
  };

  const mockMap: Record<StageId, boolean> = {
    ATRACCION: atraccionIsMock,
    CAPTURA: capturaIsMock,
    NUTRICION: nutricionIsMock,
    OPORTUNIDAD: oportunidadIsMock,
    VENTAS: ventasIsMock,
    ADOPCION: adopcionIsMock,
    EXPANSION: expansionIsMock,
    EVANGELIZACION: evangelizacionIsMock,
  };

  const handleStageClick = (id: StageId) => {
    setActiveStage(activeStage === id ? null : id);
  };

  const handleMetricClick = (metric: MetricClickData) => {
    setSidebarMetric(metric);
    setSidebarOpen(true);
  };

  const handleSidebarClose = () => {
    setSidebarOpen(false);
    setSidebarMetric(null);
  };

  const activeStageData = activeStage
    ? enrichedSummaries.find((s) => s.id === activeStage)
    : null;

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

        {activeStageData && (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg">
                Detalle: {activeStageData.label}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {activeStage === 'ATRACCION' ? (
                <AttractionDetail onMetricClick={handleMetricClick} />
              ) : activeStage === 'CAPTURA' ? (
                <CaptureDetail onMetricClick={handleMetricClick} />
              ) : activeStage === 'NUTRICION' ? (
                <NurtureDetail onMetricClick={handleMetricClick} />
              ) : activeStage === 'OPORTUNIDAD' ? (
                <OpportunityDetail onMetricClick={handleMetricClick} />
              ) : activeStage === 'VENTAS' ? (
                <SalesDetail onMetricClick={handleMetricClick} />
              ) : activeStage === 'ADOPCION' ? (
                <AdoptionDetail onMetricClick={handleMetricClick} />
              ) : activeStage === 'EXPANSION' ? (
                <ExpansionDetail onMetricClick={handleMetricClick} />
              ) : activeStage === 'EVANGELIZACION' ? (
                <EvangelizationDetail onMetricClick={handleMetricClick} />
              ) : (
                <PlaceholderDetail stage={activeStageData} />
              )}
            </CardContent>
          </Card>
        )}
      </div>

      {/* Metric drill-down sidebar — renders polymorphic SidebarContent per stageId */}
      <MetricSidebar
        isOpen={sidebarOpen}
        onClose={handleSidebarClose}
        metric={sidebarMetric}
      >
        <SidebarContent metric={sidebarMetric} stageId={activeStage} />
      </MetricSidebar>
    </>
  );
}
