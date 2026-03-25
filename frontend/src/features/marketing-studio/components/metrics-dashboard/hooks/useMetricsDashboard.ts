import { useState } from 'react';
import type { StageId, StageSummary, MetricClickData, ChannelMetric } from '../../../types/metrics';
import { STAGE_SUMMARIES } from '../../../api/metrics-mock-data';
import { mergeStageData } from '../utils/stage-data-mapper';

// Parallel per-stage hooks
import { useAttractionDetail } from '../../../hooks/useAttractionDetail';
import { useCaptureDetail } from '../../../hooks/useCaptureDetail';
import { useNurtureDetail } from '../../../hooks/useNurtureDetail';
import { useOpportunityDetail } from '../../../hooks/useOpportunityDetail';
import { useSalesDetail } from '../../../hooks/useSalesDetail';
import { useAdoptionDetail } from '../../../hooks/useAdoptionDetail';
import { useExpansionDetail } from '../../../hooks/useExpansionDetail';
import { useEvangelizationDetail } from '../../../hooks/useEvangelizationDetail';

export function useMetricsDashboard() {
  const [activeStage, setActiveStage] = useState<StageId | null>('ATRACCION_CAPTURA');

  // Sidebar state — metric drill-down wired to detail panels
  const [sidebarMetric, setSidebarMetric] = useState<MetricClickData | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Channel detail sidebar state
  const [selectedChannel, setSelectedChannel] = useState<ChannelMetric | null>(null);
  const [channelSidebarOpen, setChannelSidebarOpen] = useState(false);

  // Channel connection modal state
  const [configureChannel, setConfigureChannel] = useState<{ slug: string; name: string } | null>(null);

  // All 8 stage hooks called in parallel
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

  const atraccionCapturaSummary: StageSummary = {
    id: 'ATRACCION_CAPTURA',
    order: 0,
    label: 'Atracción & Captura',
    description: 'Etapa 1 y 2 - Tráfico y visitantes convertidos a leads',
    mainKpi: atraccionSummary.mainKpi,
    secondaryKpi: { label: 'leads', value: capturaSummary.mainKpi.value, unit: capturaSummary.mainKpi.unit },
    hasDetail: true,
  };

  const nutricionOportunidadSummary: StageSummary = {
    id: 'NUTRICION_OPORTUNIDAD',
    order: 1,
    label: 'Nutrición & Oportunidad',
    description: 'Etapa 3 y 4 - Calentamiento de leads y generación de intenciones de compra',
    mainKpi: nutricionSummary.mainKpi,
    secondaryKpi: { label: 'SQLs', value: oportunidadSummary.mainKpi.value, unit: oportunidadSummary.mainKpi.unit },
    hasDetail: true,
  };

  const expansionEvangelizacionSummary: StageSummary = {
    id: 'EXPANSION_EVANGELIZACION',
    order: 4,
    label: 'Expansión & Evangelización',
    description: 'Etapa 5 y 6 - Retención, crecimiento de LTV y referidos',
    mainKpi: expansionSummary.mainKpi,
    secondaryKpi: { label: 'k-factor', value: evangelizacionSummary.mainKpi.value, unit: evangelizacionSummary.mainKpi.unit },
    hasDetail: true,
  };

  const enrichedSummaries = [
    atraccionCapturaSummary, nutricionOportunidadSummary,
    ventasSummary, adopcionSummary, expansionEvangelizacionSummary,
  ];

  const loadingMap: Record<StageId, boolean> = {
    ATRACCION_CAPTURA: atraccionIsLoading || capturaIsLoading,
    ATRACCION: false,
    CAPTURA: false,
    NUTRICION_OPORTUNIDAD: nutricionIsLoading || oportunidadIsLoading,
    NUTRICION: false,
    OPORTUNIDAD: false,
    VENTAS: ventasIsLoading,
    ADOPCION: adopcionIsLoading,
    EXPANSION_EVANGELIZACION: expansionIsLoading || evangelizacionIsLoading,
    EXPANSION: false,
    EVANGELIZACION: false,
  };

  const mockMap: Record<StageId, boolean> = {
    ATRACCION_CAPTURA: atraccionIsMock && capturaIsMock,
    ATRACCION: false,
    CAPTURA: false,
    NUTRICION_OPORTUNIDAD: nutricionIsMock && oportunidadIsMock,
    NUTRICION: false,
    OPORTUNIDAD: false,
    VENTAS: ventasIsMock,
    ADOPCION: adopcionIsMock,
    EXPANSION_EVANGELIZACION: expansionIsMock && evangelizacionIsMock,
    EXPANSION: false,
    EVANGELIZACION: false,
  };

  const handleStageClick = (id: StageId) => {
    setActiveStage(activeStage === id ? null : id);
  };

  const handleMetricClick = (metric: MetricClickData) => {
    setChannelSidebarOpen(false);
    setSelectedChannel(null);
    setSidebarMetric(metric);
    setSidebarOpen(true);
  };

  const handleSidebarClose = () => {
    setSidebarOpen(false);
    setSidebarMetric(null);
  };

  const handleChannelClick = (channel: ChannelMetric) => {
    if (!channel.connected || !channel.providerName) return;
    setSidebarOpen(false);
    setSidebarMetric(null);
    setSelectedChannel(channel);
    setChannelSidebarOpen(true);
  };

  const handleChannelSidebarClose = () => {
    setChannelSidebarOpen(false);
    setSelectedChannel(null);
  };

  const handleConfigure = (slug: string, name: string) => {
    setConfigureChannel({ slug, name });
  };

  const handleCloseConfigure = () => {
    setConfigureChannel(null);
  };

  const activeStageData = activeStage
    ? enrichedSummaries.find((s) => s.id === activeStage)
    : null;

  return {
    activeStage,
    activeStageData,
    enrichedSummaries,
    loadingMap,
    mockMap,
    sidebarMetric,
    sidebarOpen,
    selectedChannel,
    channelSidebarOpen,
    configureChannel,
    handleStageClick,
    handleMetricClick,
    handleSidebarClose,
    handleChannelClick,
    handleChannelSidebarClose,
    handleConfigure,
    handleCloseConfigure,
  };
}