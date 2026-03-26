'use client';

import { createContext, useContext, useState, useCallback, useEffect, useMemo, type ReactNode } from 'react';
import { usePathname } from 'next/navigation';
import type { StageId, MetricClickData, ChannelMetric } from '../../../types/metrics';

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

// ── Context shape ──────────────────────────────────────────────────

interface GrowthStudioContextValue {
  activeStage: CompositeStageId | null;
  sidebarMetric: MetricClickData | null;
  sidebarOpen: boolean;
  selectedChannel: ChannelMetric | null;
  channelSidebarOpen: boolean;
  configureChannel: { slug: string; name: string } | null;
  handleMetricClick: (metric: MetricClickData) => void;
  handleSidebarClose: () => void;
  handleChannelClick: (channel: ChannelMetric) => void;
  handleChannelSidebarClose: () => void;
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

  // Derive activeStage from URL
  const activeStage = useMemo<CompositeStageId | null>(() => {
    if (!pathname) return null;
    const segments = pathname.split('/');
    const slug = segments[segments.length - 1];
    return SLUG_TO_STAGE[slug] ?? null;
  }, [pathname]);

  // Sidebar state
  const [sidebarMetric, setSidebarMetric] = useState<MetricClickData | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [selectedChannel, setSelectedChannel] = useState<ChannelMetric | null>(null);
  const [channelSidebarOpen, setChannelSidebarOpen] = useState(false);
  const [configureChannel, setConfigureChannel] = useState<{ slug: string; name: string } | null>(null);

  // Reset sidebars when stage changes
  useEffect(() => {
    setSidebarOpen(false);
    setSidebarMetric(null);
    setChannelSidebarOpen(false);
    setSelectedChannel(null);
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
  }, []);

  const handleChannelSidebarClose = useCallback(() => {
    setChannelSidebarOpen(false);
    setSelectedChannel(null);
  }, []);

  const handleConfigure = useCallback((slug: string, name: string) => {
    setConfigureChannel({ slug, name });
  }, []);

  const handleCloseConfigure = useCallback(() => {
    setConfigureChannel(null);
  }, []);

  const value = useMemo<GrowthStudioContextValue>(() => ({
    activeStage,
    sidebarMetric,
    sidebarOpen,
    selectedChannel,
    channelSidebarOpen,
    configureChannel,
    handleMetricClick,
    handleSidebarClose,
    handleChannelClick,
    handleChannelSidebarClose,
    handleConfigure,
    handleCloseConfigure,
  }), [
    activeStage,
    sidebarMetric,
    sidebarOpen,
    selectedChannel,
    channelSidebarOpen,
    configureChannel,
    handleMetricClick,
    handleSidebarClose,
    handleChannelClick,
    handleChannelSidebarClose,
    handleConfigure,
    handleCloseConfigure,
  ]);

  return (
    <GrowthStudioContext.Provider value={value}>
      {children}
    </GrowthStudioContext.Provider>
  );
}
