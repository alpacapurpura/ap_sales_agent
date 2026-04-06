'use client';

import { createContext, useContext, useState, useCallback, useEffect, useMemo, type ReactNode } from 'react';
import { usePathname, useRouter, useSearchParams } from 'next/navigation';
import type { StageId, MetricClickData, ChannelMetric, MetaAdsDashboardTab } from '../../../types/metrics';
import type { PeriodType } from '../../../api/stage-detail-api';

const CHANNEL_PARAM = 'channel';

// ── Slug ↔ StageId mappings ────────────────────────────────────────

type CompositeStageId = Extract<
  StageId,
  'ATRACCION_CAPTURA' | 'NUTRICION_OPORTUNIDAD' | 'VENTAS' | 'ADOPCION' | 'EXPANSION_EVANGELIZACION'
>;

export const SLUG_TO_STAGE: Record<string, CompositeStageId> = {
  'atraccion-captura': 'ATRACCION_CAPTURA',
  'nutricion-oportunidad': 'NUTRICION_OPORTUNIDAD',
  'ventas': 'VENTAS',
  'adopcion': 'ADOPCION',
  'expansion-evangelizacion': 'EXPANSION_EVANGELIZACION',
};

export const STAGE_TO_SLUG: Record<CompositeStageId, string> = {
  ATRACCION_CAPTURA: 'atraccion-captura',
  NUTRICION_OPORTUNIDAD: 'nutricion-oportunidad',
  VENTAS: 'ventas',
  ADOPCION: 'adopcion',
  EXPANSION_EVANGELIZACION: 'expansion-evangelizacion',
};

// ── Context shape ────���─────────────────────────────────────────────

interface GrowthStudioContextValue {
  activeStage: CompositeStageId | null;
  selectedPeriod: PeriodType;
  setSelectedPeriod: (period: PeriodType) => void;
  sidebarMetric: MetricClickData | null;
  sidebarOpen: boolean;
  selectedChannel: ChannelMetric | null;
  channelSidebarOpen: boolean;
  /** @deprecated Use expandedDashboardChannel === 'meta-ads' instead */
  metaAdsDashboardOpen: boolean;
  metaAdsDashboardInitialTab: MetaAdsDashboardTab | undefined;
  expandedDashboardChannel: string | null;
  configureChannel: { slug: string; name: string } | null;
  handleMetricClick: (metric: MetricClickData) => void;
  handleSidebarClose: () => void;
  handleChannelClick: (channel: ChannelMetric) => void;
  handleChannelSidebarClose: () => void;
  handleOpenMetaAdsDashboard: () => void;
  handleOpenMetaAdsDashboardToTab: (tab: MetaAdsDashboardTab) => void;
  handleCloseMetaAdsDashboard: () => void;
  handleOpenExpandedDashboard: (channelSlug: string) => void;
  handleCloseExpandedDashboard: () => void;
  handleConfigure: (slug: string, name: string) => void;
  handleCloseConfigure: () => void;
}

const GrowthStudioContext = createContext<GrowthStudioContextValue | null>(null);

// ── Hook ───────────────────────────────────────────────────────────

export function useGrowthStudioContext() {
  const ctx = useContext(GrowthStudioContext);
  if (!ctx) throw new Error('useGrowthStudioContext must be used inside GrowthStudioProvider');
  return ctx;
}

// ── Provider ───────────────────────────────────────────────────────

export function GrowthStudioProvider({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const searchParams = useSearchParams();

  // Derive activeStage from URL — scan all segments so nested routes
  // like /tenant/growth-studio/atraccion-captura/meta-ads still resolve
  // to 'ATRACCION_CAPTURA' (the stage segment, not the channel segment).
  const activeStage = useMemo<CompositeStageId | null>(() => {
    if (!pathname) return null;
    const segments = pathname.split('/');
    // Walk segments in reverse so that the deepest stage match wins
    // (though in practice there is only one stage segment per URL).
    for (let i = segments.length - 1; i >= 0; i--) {
      const match = SLUG_TO_STAGE[segments[i]];
      if (match) return match;
    }
    return null;
  }, [pathname]);

  // Period selection state (persists across stage navigation)
  const [selectedPeriod, setSelectedPeriod] = useState<PeriodType>('last_30_days');

  // Sidebar state
  const [sidebarMetric, setSidebarMetric] = useState<MetricClickData | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [selectedChannel, setSelectedChannel] = useState<ChannelMetric | null>(null);
  const [channelSidebarOpen, setChannelSidebarOpen] = useState(false);
  const [expandedDashboardChannel, setExpandedDashboardChannel] = useState<string | null>(null);
  const metaAdsDashboardOpen = expandedDashboardChannel === 'meta-ads';
  const [metaAdsDashboardInitialTab, setMetaAdsDashboardInitialTab] = useState<MetaAdsDashboardTab | undefined>(undefined);
  const [configureChannel, setConfigureChannel] = useState<{ slug: string; name: string } | null>(null);

  // Reset sidebars when stage changes — legitimately syncs multiple pieces
  // of local UI state when the user navigates to a different funnel stage.
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setSidebarOpen(false);

    setSidebarMetric(null);

    setChannelSidebarOpen(false);

    setSelectedChannel(null);

    setExpandedDashboardChannel(null);

    setMetaAdsDashboardInitialTab(undefined);

    setConfigureChannel(null);
  }, [activeStage]);

  const handleMetricClick = useCallback((metric: MetricClickData) => {
    setChannelSidebarOpen(false);
    setSelectedChannel(null);
    setSidebarMetric(metric);
    setSidebarOpen(true);
  }, []);

  const handleSidebarClose = useCallback(() => {
    setSidebarOpen(false);
    setSidebarMetric(null);
  }, []);

  const handleChannelClick = useCallback((channel: ChannelMetric) => {
    if (!channel.connected || !channel.providerName) return;
    setSidebarOpen(false);
    setSidebarMetric(null);
    setSelectedChannel(channel);
    setChannelSidebarOpen(true);
    // Sync channel selection to URL search params
    const params = new URLSearchParams(searchParams.toString());
    params.set(CHANNEL_PARAM, channel.slug);
    router.replace(`${pathname}?${params.toString()}`);
  }, [searchParams, router, pathname]);

  const handleChannelSidebarClose = useCallback(() => {
    setChannelSidebarOpen(false);
    setSelectedChannel(null);
    // Remove channel param from URL
    const params = new URLSearchParams(searchParams.toString());
    params.delete(CHANNEL_PARAM);
    const qs = params.toString();
    router.replace(qs ? `${pathname}?${qs}` : pathname);
  }, [searchParams, router, pathname]);

  const handleOpenMetaAdsDashboard = useCallback(() => {
    setChannelSidebarOpen(false);
    setSelectedChannel(null);
    setMetaAdsDashboardInitialTab(undefined);
    setExpandedDashboardChannel('meta-ads');
  }, []);

  const handleOpenMetaAdsDashboardToTab = useCallback((tab: MetaAdsDashboardTab) => {
    setChannelSidebarOpen(false);
    setSelectedChannel(null);
    setMetaAdsDashboardInitialTab(tab);
    setExpandedDashboardChannel('meta-ads');
  }, []);

  const handleCloseMetaAdsDashboard = useCallback(() => {
    setExpandedDashboardChannel(null);
    setMetaAdsDashboardInitialTab(undefined);
  }, []);

  const handleOpenExpandedDashboard = useCallback((channelSlug: string) => {
    // Close sidebars
    setChannelSidebarOpen(false);
    setSelectedChannel(null);
    // Navigate to the nested channel route instead of overlay state
    const stageSlug = activeStage ? STAGE_TO_SLUG[activeStage] : 'atraccion-captura';
    // Extract tenantId from pathname: /{tenantId}/growth-studio/...
    const segments = pathname.split('/');
    const gsIndex = segments.findIndex(s => s === 'growth-studio');
    const tenantId = gsIndex > 0 ? segments[gsIndex - 1] : '';
    router.push(`/${tenantId}/growth-studio/${stageSlug}/${channelSlug}`);
  }, [activeStage, pathname, router]);

  const handleCloseExpandedDashboard = useCallback(() => {
    setExpandedDashboardChannel(null);
  }, []);

  const handleConfigure = useCallback((slug: string, name: string) => {
    setConfigureChannel({ slug, name });
  }, []);

  const handleCloseConfigure = useCallback(() => {
    setConfigureChannel(null);
  }, []);

  const value = useMemo<GrowthStudioContextValue>(() => ({
    activeStage,
    selectedPeriod,
    setSelectedPeriod,
    sidebarMetric,
    sidebarOpen,
    selectedChannel,
    channelSidebarOpen,
    metaAdsDashboardOpen,
    metaAdsDashboardInitialTab,
    expandedDashboardChannel,
    configureChannel,
    handleMetricClick,
    handleSidebarClose,
    handleChannelClick,
    handleChannelSidebarClose,
    handleOpenMetaAdsDashboard,
    handleOpenMetaAdsDashboardToTab,
    handleCloseMetaAdsDashboard,
    handleOpenExpandedDashboard,
    handleCloseExpandedDashboard,
    handleConfigure,
    handleCloseConfigure,
  }), [
    activeStage,
    selectedPeriod,
    sidebarMetric,
    sidebarOpen,
    selectedChannel,
    channelSidebarOpen,
    metaAdsDashboardOpen,
    metaAdsDashboardInitialTab,
    expandedDashboardChannel,
    configureChannel,
    handleMetricClick,
    handleSidebarClose,
    handleChannelClick,
    handleChannelSidebarClose,
    handleOpenMetaAdsDashboard,
    handleOpenMetaAdsDashboardToTab,
    handleCloseMetaAdsDashboard,
    handleOpenExpandedDashboard,
    handleCloseExpandedDashboard,
    handleConfigure,
    handleCloseConfigure,
  ]);

  return (
    <GrowthStudioContext.Provider value={value}>
      {children}
    </GrowthStudioContext.Provider>
  );
}
