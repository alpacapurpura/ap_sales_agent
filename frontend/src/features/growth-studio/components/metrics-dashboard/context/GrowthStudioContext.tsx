"use client";

import {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  type ReactNode,
} from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import type {
  StageId,
  MetricClickData,
  ChannelMetric,
  MetaAdsDashboardTab,
} from "../../../types/metrics";
import type { PeriodType } from "../../../api/stage-detail-api";
import { useMetricClickHandler } from "./useMetricClickHandler";
import { providerToConnectionRoute } from "../../../lib/providerToConnectionRoute";

// ── Split contexts: stable actions vs reactive state ──────────────
// Actions context never changes identity after mount, preventing
// unnecessary re-renders of components that only call handlers.
interface GrowthStudioActionsValue {
  setSelectedPeriod: (period: PeriodType) => void;
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
  handleNoDataClick: (channel: ChannelMetric) => void;
  handleCloseNoData: () => void;
  handleDisconnectedClick: (channel: ChannelMetric) => void;
  resolvePendingChannel: (channels: ResolvableChannel[]) => void;
}

const GrowthStudioActionsContext = createContext<GrowthStudioActionsValue | null>(null);

export function useGrowthStudioActions() {
  const ctx = useContext(GrowthStudioActionsContext);
  if (!ctx) throw new Error("useGrowthStudioActions must be used inside GrowthStudioProvider");
  return ctx;
}

const CHANNEL_PARAM = "channel";
const TAB_PARAM = "tab";

/** Minimal shape needed to resolve a deep link channel. */
interface ResolvableChannel {
  slug: string;
  name: string;
  channelType: string;
  connected: boolean;
  providerName?: string;
}

// ── Slug ↔ StageId mappings ────────────────────────────────────────

type CompositeStageId = Extract<
  StageId,
  "ATRACCION_CAPTURA" | "NUTRICION_OPORTUNIDAD" | "VENTAS" | "ADOPCION" | "EXPANSION_EVANGELIZACION"
>;

export const SLUG_TO_STAGE: Record<string, CompositeStageId> = {
  "atraccion-captura": "ATRACCION_CAPTURA",
  "nutricion-oportunidad": "NUTRICION_OPORTUNIDAD",
  ventas: "VENTAS",
  adopcion: "ADOPCION",
  "expansion-evangelizacion": "EXPANSION_EVANGELIZACION",
};

export const STAGE_TO_SLUG: Record<CompositeStageId, string> = {
  ATRACCION_CAPTURA: "atraccion-captura",
  NUTRICION_OPORTUNIDAD: "nutricion-oportunidad",
  VENTAS: "ventas",
  ADOPCION: "adopcion",
  EXPANSION_EVANGELIZACION: "expansion-evangelizacion",
};

// ── Context shape ──────────────────────────────────────────────────

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
  noDataChannel: ChannelMetric | null;
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
  handleNoDataClick: (channel: ChannelMetric) => void;
  handleCloseNoData: () => void;
  handleDisconnectedClick: (channel: ChannelMetric) => void;
  pendingChannelSlug: string | null;
  pendingChannelTab: string | null;
  resolvePendingChannel: (channels: ResolvableChannel[]) => void;
}

const GrowthStudioContext = createContext<GrowthStudioContextValue | null>(null);

// ── Hook ───────────────────────────────────────────────────────────

export function useGrowthStudioContext() {
  const ctx = useContext(GrowthStudioContext);
  if (!ctx) throw new Error("useGrowthStudioContext must be used inside GrowthStudioProvider");
  return ctx;
}

// ── Provider ───────────────────────────────────────────────────────

export function GrowthStudioProvider({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const searchParams = useSearchParams();

  // Keep a stable ref to searchParams so callbacks don't depend on the
  // ever-changing object identity from useSearchParams().
  const searchParamsRef = useRef(searchParams);
  const pathnameRef = useRef(pathname);
  useEffect(() => {
    searchParamsRef.current = searchParams;
  }, [searchParams]);
  useEffect(() => {
    pathnameRef.current = pathname;
  }, [pathname]);

  // Derive activeStage from URL — scan all segments so nested routes
  // like /tenant/growth-studio/atraccion-captura/meta-ads still resolve
  // to 'ATRACCION_CAPTURA' (the stage segment, not the channel segment).
  const activeStage = useMemo<CompositeStageId | null>(() => {
    if (!pathname) return null;
    const segments = pathname.split("/");
    // Walk segments in reverse so that the deepest stage match wins
    // (though in practice there is only one stage segment per URL).
    for (let i = segments.length - 1; i >= 0; i--) {
      const match = SLUG_TO_STAGE[segments[i]];
      if (match) return match;
    }
    return null;
  }, [pathname]);

  // Period selection state (persists across stage navigation)
  const [selectedPeriod, setSelectedPeriod] = useState<PeriodType>("last_30_days");

  // Metric sidebar state (extracted hook — provides open/close + handlers)
  const {
    sidebarMetric,
    sidebarOpen,
    setSidebarOpen,
    setSidebarMetric,
    handleMetricClick: baseHandleMetricClick,
    handleSidebarClose,
  } = useMetricClickHandler();

  const [selectedChannel, setSelectedChannel] = useState<ChannelMetric | null>(null);
  const [channelSidebarOpen, setChannelSidebarOpen] = useState(false);
  const [expandedDashboardChannel, setExpandedDashboardChannel] = useState<string | null>(null);

  // Wrap metric click to also close channel sidebar
  const handleMetricClick = useCallback(
    (metric: MetricClickData) => {
      setChannelSidebarOpen(false);
      setSelectedChannel(null);
      baseHandleMetricClick(metric);
    },
    [baseHandleMetricClick],
  );
  const metaAdsDashboardOpen = expandedDashboardChannel === "meta-ads";
  const [metaAdsDashboardInitialTab, setMetaAdsDashboardInitialTab] = useState<
    MetaAdsDashboardTab | undefined
  >(undefined);
  const [configureChannel, setConfigureChannel] = useState<{ slug: string; name: string } | null>(
    null,
  );
  const [noDataChannel, setNoDataChannel] = useState<ChannelMetric | null>(null);

  // ── Deep link: read ?channel= and ?tab= from URL ──────────────────
  const pendingChannelSlug = searchParams.get(CHANNEL_PARAM);
  const pendingChannelTab = searchParams.get(TAB_PARAM);

  // Guard ref: once a slug is resolved (or the user closes the sidebar),
  // don't re-open on subsequent renders for the same slug.
  const resolvedSlugRef = useRef<string | null>(null);

  const resolvePendingChannel = useCallback(
    (channels: ResolvableChannel[]) => {
      if (!pendingChannelSlug) return;
      if (resolvedSlugRef.current === pendingChannelSlug) return;

      const match = channels.find((c) => c.slug === pendingChannelSlug);
      if (match && match.connected && match.providerName) {
        handleSidebarClose();
        // Build a minimal ChannelMetric from the resolvable data
        setSelectedChannel({
          slug: match.slug,
          name: match.name,
          channelType: match.channelType,
          connected: match.connected,
          providerName: match.providerName,
          sourceLabel: match.name,
          metrics: [],
        });
        setChannelSidebarOpen(true);
        // Do NOT update URL — it already has ?channel=
      }
      resolvedSlugRef.current = pendingChannelSlug;
    },
    [pendingChannelSlug],
  );

  // Reset sidebars when stage changes — legitimately syncs multiple pieces
  // of local UI state when the user navigates to a different funnel stage.
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- legitimately resets UI on stage nav
    setSidebarOpen(false);

    setSidebarMetric(null);

    setChannelSidebarOpen(false);

    setSelectedChannel(null);

    setExpandedDashboardChannel(null);

    setMetaAdsDashboardInitialTab(undefined);

    setConfigureChannel(null);

    setNoDataChannel(null);

    resolvedSlugRef.current = null;
  }, [activeStage]);

  const handleChannelClick = useCallback(
    (channel: ChannelMetric) => {
      if (!channel.connected || !channel.providerName) return;
      setSidebarOpen(false);
      setSidebarMetric(null);
      setSelectedChannel(channel);
      setChannelSidebarOpen(true);
      // Sync channel selection to URL search params (read from refs for stable deps)
      const params = new URLSearchParams(searchParamsRef.current.toString());
      params.set(CHANNEL_PARAM, channel.slug);
      router.replace(`${pathnameRef.current}?${params.toString()}`);
    },
    [router],
  );

  const handleChannelSidebarClose = useCallback(() => {
    setChannelSidebarOpen(false);
    setSelectedChannel(null);
    // Mark as resolved so deep link doesn't re-open
    const slug = searchParamsRef.current.get(CHANNEL_PARAM);
    if (slug) {
      resolvedSlugRef.current = slug;
    }
    // Remove channel and tab params from URL (read from refs for stable deps)
    const params = new URLSearchParams(searchParamsRef.current.toString());
    params.delete(CHANNEL_PARAM);
    params.delete(TAB_PARAM);
    const qs = params.toString();
    const currentPath = pathnameRef.current;
    router.replace(qs ? `${currentPath}?${qs}` : currentPath);
  }, [router]);

  /** @deprecated Use handleOpenExpandedDashboard('meta-ads') instead */
  const handleOpenMetaAdsDashboard = useCallback(() => {
    setChannelSidebarOpen(false);
    setSelectedChannel(null);
    setMetaAdsDashboardInitialTab(undefined);
    // Navigate to route instead of overlay state
    const stageSlug = activeStageRef.current
      ? STAGE_TO_SLUG[activeStageRef.current]
      : "atraccion-captura";
    const segments = pathnameRef.current.split("/");
    const gsIndex = segments.findIndex((s) => s === "growth-studio");
    const tid = gsIndex > 0 ? segments[gsIndex - 1] : "";
    router.push(`/${tid}/growth-studio/${stageSlug}/meta-ads`);
  }, [router]);

  /** @deprecated Use handleOpenExpandedDashboard('meta-ads') instead */
  const handleOpenMetaAdsDashboardToTab = useCallback(
    (tab: MetaAdsDashboardTab) => {
      setChannelSidebarOpen(false);
      setSelectedChannel(null);
      setMetaAdsDashboardInitialTab(tab);
      const stageSlug = activeStageRef.current
        ? STAGE_TO_SLUG[activeStageRef.current]
        : "atraccion-captura";
      const segments = pathnameRef.current.split("/");
      const gsIndex = segments.findIndex((s) => s === "growth-studio");
      const tid = gsIndex > 0 ? segments[gsIndex - 1] : "";
      router.push(`/${tid}/growth-studio/${stageSlug}/meta-ads?tab=${tab}`);
    },
    [router],
  );

  /** @deprecated Use handleCloseExpandedDashboard instead */
  const handleCloseMetaAdsDashboard = useCallback(() => {
    setExpandedDashboardChannel(null);
    setMetaAdsDashboardInitialTab(undefined);
  }, []);

  const activeStageRef = useRef<typeof activeStage | null>(null);
  // eslint-disable-next-line react-hooks/immutability
  activeStageRef.current = activeStage;

  const handleOpenExpandedDashboard = useCallback(
    (channelSlug: string) => {
      // Close sidebars
      setChannelSidebarOpen(false);
      setSelectedChannel(null);
      // Navigate to the nested channel route instead of overlay state
      const stageSlug = activeStageRef.current
        ? STAGE_TO_SLUG[activeStageRef.current]
        : "atraccion-captura";
      // Extract tenantId from pathname: /{tenantId}/growth-studio/...
      const segments = pathnameRef.current.split("/");
      const gsIndex = segments.findIndex((s) => s === "growth-studio");
      const tenantId = gsIndex > 0 ? segments[gsIndex - 1] : "";
      router.push(`/${tenantId}/growth-studio/${stageSlug}/${channelSlug}`);
    },
    [router],
  );

  const handleCloseExpandedDashboard = useCallback(() => {
    setExpandedDashboardChannel(null);
  }, []);

  const handleConfigure = useCallback((slug: string, name: string) => {
    setConfigureChannel({ slug, name });
  }, []);

  const handleCloseConfigure = useCallback(() => {
    setConfigureChannel(null);
  }, []);

  const handleNoDataClick = useCallback((channel: ChannelMetric) => {
    setNoDataChannel(channel);
  }, []);

  const handleCloseNoData = useCallback(() => {
    setNoDataChannel(null);
  }, []);

  const handleDisconnectedClick = useCallback(
    (channel: ChannelMetric) => {
      const route = providerToConnectionRoute(channel.providerName);
      const segments = pathnameRef.current.split("/");
      const gsIndex = segments.findIndex((s) => s === "growth-studio");
      const tenantId = gsIndex > 0 ? segments[gsIndex - 1] : "";
      if (route) {
        router.push(`/${tenantId}/connections/${route}`);
      } else {
        router.push(`/${tenantId}/connections`);
      }
    },
    [router],
  );

  // Actions value — stable identity (callbacks use refs, deps are minimal)
  const actions = useMemo<GrowthStudioActionsValue>(
    () => ({
      setSelectedPeriod,
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
      handleNoDataClick,
      handleCloseNoData,
      handleDisconnectedClick,
      resolvePendingChannel,
    }),
    [
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
      handleNoDataClick,
      handleCloseNoData,
      handleDisconnectedClick,
      resolvePendingChannel,
    ],
  );

  // Full value — includes both state and actions for backward compatibility
  const value = useMemo<GrowthStudioContextValue>(
    () => ({
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
      noDataChannel,
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
      handleNoDataClick,
      handleCloseNoData,
      handleDisconnectedClick,
      pendingChannelSlug,
      pendingChannelTab,
      resolvePendingChannel,
    }),
    [
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
      noDataChannel,
      pendingChannelSlug,
      pendingChannelTab,
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
      handleNoDataClick,
      handleCloseNoData,
      handleDisconnectedClick,
      resolvePendingChannel,
    ],
  );

  return (
    <GrowthStudioActionsContext.Provider value={actions}>
      <GrowthStudioContext.Provider value={value}>{children}</GrowthStudioContext.Provider>
    </GrowthStudioActionsContext.Provider>
  );
}
