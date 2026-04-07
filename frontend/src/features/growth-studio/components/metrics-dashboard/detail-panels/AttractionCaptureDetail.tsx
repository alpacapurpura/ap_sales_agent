'use client';

import React, { useState, useMemo, useCallback, useEffect } from 'react';
import { useStageTimeSeries } from '../../../hooks/useStageDetail';
import { useStageOverview } from '../../../hooks/useStageOverview';
import { useIntersectionObserver } from '../../../hooks/useIntersectionObserver';
import { useGrowthSync } from '../../../context/growth-sync-context';
import { ActionPanel } from '../action-widgets/ActionPanel';
import DetailSkeleton from '../ui/DetailSkeleton';
import DetailError from '../ui/DetailError';
import type { MetricClickData, StageTimeSeries as TSType, ChannelMetric } from '../../../types/metrics';
import { Button } from '@/components/ui/button';
import { Settings, RefreshCw, Plug, Zap, Megaphone, UserPlus, Coins, TrendingUp, Globe, Bot } from 'lucide-react';
import { DateRangePicker } from '../ui/DateRangePicker';
import { AttractionScorecards } from '../attraction/AttractionScorecards';
import { AttractionTrendChart } from '../attraction/AttractionTrendChart';
import { CaptureBreakdownChart } from '../attraction/CaptureBreakdownChart';
import { ConversionBridge } from '../attraction/ConversionBridge';
import { LazyChannelGroup } from '../channel-widgets/LazyChannelGroup';
import dynamic from 'next/dynamic';

const MetaAdsDashboard = dynamic(() => import('../sidebar/meta-ads/MetaAdsDashboard').then(m => ({ default: m.MetaAdsDashboard })), { ssr: false });
const IgOrganicDashboard = dynamic(() => import('../sidebar/ig-organic/IgOrganicDashboard').then(m => ({ default: m.IgOrganicDashboard })), { ssr: false });
const YouTubeDashboard = dynamic(() => import('../sidebar/youtube-organic/YouTubeDashboard').then(m => ({ default: m.YouTubeDashboard })), { ssr: false });
const MailDashboard = dynamic(() => import('../sidebar/mail/MailDashboard').then(m => ({ default: m.MailDashboard })), { ssr: false });
import { useGrowthStudioContext } from '../context/GrowthStudioContext';

// ─── Helper ──────────────────────────────────────────────────────────────────

function MetaAdsDashboardWrapper() {
  const { metaAdsDashboardOpen, metaAdsDashboardInitialTab, handleCloseMetaAdsDashboard } = useGrowthStudioContext();
  if (!metaAdsDashboardOpen) return null;
  return <MetaAdsDashboard onClose={handleCloseMetaAdsDashboard} initialTab={metaAdsDashboardInitialTab} />;
}

function ExpandedDashboardWrapper() {
  const { expandedDashboardChannel, handleCloseExpandedDashboard } = useGrowthStudioContext();
  if (expandedDashboardChannel === 'ig-organic') {
    return <IgOrganicDashboard onClose={handleCloseExpandedDashboard} />;
  }
  if (expandedDashboardChannel === 'yt-organic') {
    return <YouTubeDashboard onClose={handleCloseExpandedDashboard} />;
  }
  if (expandedDashboardChannel === 'email-nurture') {
    return <MailDashboard onClose={handleCloseExpandedDashboard} />;
  }
  return null;
}

// ─── Mobile Charts Expand ────────────────────────────────────────────────────

function MobileChartsExpand({
  timeSeries,
  tsLoading,
  capLoading,
  captureChannels,
}: {
  timeSeries: TSType | undefined;
  tsLoading: boolean;
  capLoading: boolean;
  captureChannels: ChannelMetric[];
}) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="md:hidden">
      <Button
        variant="outline"
        size="sm"
        className="w-full"
        onClick={() => setExpanded(!expanded)}
      >
        {expanded ? 'Ocultar gráficos' : 'Ver gráficos'}
      </Button>
      {expanded && (
        <div className="mt-4 space-y-4">
          <AttractionTrendChart timeSeries={timeSeries} isLoading={tsLoading} />
          <CaptureBreakdownChart channels={captureChannels} isLoading={capLoading} />
        </div>
      )}
    </div>
  );
}

// ─── Main Component ──────────────────────────────────────────────────────────

interface AttractionCaptureDetailProps {
  onMetricClick?: (metric: MetricClickData) => void;
  onConfigure?: (slug: string, name: string) => void;
  onChannelClick?: (channel: ChannelMetric) => void;
}

export const AttractionCaptureDetail = React.memo(function AttractionCaptureDetail({
  onMetricClick,
  onConfigure,
  onChannelClick,
}: AttractionCaptureDetailProps) {
  // ─── TIER 1: Lightweight overviews (render immediately) ─────────────
  const { data: attrOverview, isLoading: attrLoading, error: attrError, refetch: refetchAttr } = useStageOverview('attraction');
  const { data: capOverview, isLoading: capLoading, error: capError, refetch: refetchCap } = useStageOverview('capture');
  const { startSync, isSyncing } = useGrowthSync();
  const { pendingChannelSlug, resolvePendingChannel } = useGrowthStudioContext();

  // Resolve deep link ?channel= once overview data arrives
  useEffect(() => {
    if (!pendingChannelSlug) return;
    const allChannels = [
      ...(attrOverview?.channelList ?? []),
      ...(capOverview?.channelList ?? []),
    ];
    if (allChannels.length > 0) {
      resolvePendingChannel(allChannels);
    }
  }, [pendingChannelSlug, attrOverview?.channelList, capOverview?.channelList, resolvePendingChannel]);

  const [isPanelOpen, setIsPanelOpen] = useState(false);
  const [rangeDays, setRangeDays] = useState(30);
  const granularity = rangeDays >= 90 ? 'weekly' : 'daily';

  // ─── TIER 3: Charts deferred until visible ──────────────────────────
  const { ref: chartsRef, isVisible: chartsVisible } = useIntersectionObserver({ rootMargin: '200px' });
  const { data: timeSeries, isLoading: tsLoading } = useStageTimeSeries(
    'attraction', 'reach', rangeDays, granularity, { enabled: chartsVisible },
  );

  // ─── Computed totals from overview headerKpis ───────────────────────
  const totalImpressions = attrOverview?.headerKpis?.total_impressions ?? 0;
  const totalVisitors = attrOverview?.headerKpis?.total_sessions ?? 0;
  const totalSpend = 0; // Spend only available in Tier 2 — scorecards show 0 until groups load
  const totalLeads = capOverview?.headerKpis?.total_leads ?? 0;
  const leadConvRate = useMemo(() => totalVisitors > 0 ? (totalLeads / totalVisitors) * 100 : 0, [totalVisitors, totalLeads]);

  // ─── Channel groupings from overview channelList ────────────────────
  const paidChannels = useMemo(
    () => attrOverview?.channelList.filter(c => c.groupKey === 'paid') ?? [],
    [attrOverview?.channelList],
  );
  const organicChannels = useMemo(
    () => attrOverview?.channelList.filter(c =>
      c.groupKey === 'organic_social' || c.groupKey === 'ga4_search',
    ) ?? [],
    [attrOverview?.channelList],
  );
  const webCaptureChannels = useMemo(
    () => capOverview?.channelList.filter(c => c.groupKey === 'web_infrastructure') ?? [],
    [capOverview?.channelList],
  );
  const messagingCaptureChannels = useMemo(
    () => capOverview?.channelList.filter(c => c.groupKey === 'ai_agent') ?? [],
    [capOverview?.channelList],
  );

  // Build ChannelMetric[] for CaptureBreakdownChart from overview data
  const allCaptureChannels: ChannelMetric[] = useMemo(
    () => [...webCaptureChannels, ...messagingCaptureChannels].map(ch => ({
      slug: ch.slug,
      name: ch.name,
      channelType: ch.channelType,
      metrics: ch.headlineKpi ? [{ name: ch.headlineKpi.name, value: ch.headlineKpi.value, unit: ch.headlineKpi.unit }] : [],
      sourceLabel: ch.name,
      connected: ch.connected,
      lastUpdated: ch.lastUpdated,
      stale: ch.stale,
      providerName: ch.providerName,
    })),
    [webCaptureChannels, messagingCaptureChannels],
  );

  // ─── Handlers ──────────────────────────────────────────────────────
  const handleChannelClick = useCallback((channel: ChannelMetric) => {
    onChannelClick?.(channel);
  }, [onChannelClick]);

  // ─── Loading / Error / Empty ──────────────────────────────────────
  if (attrLoading || capLoading) {
    return <DetailSkeleton isLoading><></></DetailSkeleton>;
  }

  if (attrError || capError) {
    return (
      <DetailError
        error={attrError instanceof Error ? attrError : (capError instanceof Error ? capError : new Error('Error desconocido'))}
        onRetry={() => { void refetchAttr(); void refetchCap(); }}
        lastData={attrOverview || capOverview}
      />
    );
  }

  const hasAttrData = (attrOverview?.channelList.length ?? 0) > 0;
  const hasCaptureData = totalLeads > 0;
  const isEmpty = !hasAttrData && !hasCaptureData;

  return (
    <div className="space-y-6 animate-fade-in bg-background p-6 rounded-2xl text-foreground border border-border">

      {/* Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            Atracción &amp; Captura
            <span className="px-2 py-0.5 rounded-full bg-blue-100 dark:bg-blue-500/20 text-blue-700 dark:text-blue-400 text-xs font-medium tracking-wide">
              ETAPA 1 y 2
            </span>
          </h1>
          <p className="text-muted-foreground text-sm mt-1">Tu embudo de adquisición de leads</p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={() => startSync(30)}
            disabled={isSyncing}
          >
            <RefreshCw className="mr-2 h-4 w-4" />
            Sincronizar
          </Button>
          <Button size="sm" onClick={() => setIsPanelOpen(true)}>
            <Settings className="mr-2 h-4 w-4" /> Gestionar
          </Button>
        </div>
      </div>

      <ActionPanel isOpen={isPanelOpen} onClose={() => setIsPanelOpen(false)} />

      {/* Empty State */}
      {isEmpty ? (
        <div className="bg-card rounded-xl p-6 shadow-sm border border-border">
          <div className="text-center py-12 px-4 rounded-xl border-2 border-dashed border-border bg-muted/50">
            <Plug className="w-12 h-12 text-muted-foreground mx-auto mb-3" />
            <h3 className="text-lg font-semibold text-foreground mb-1">Tu ecosistema digital está vacío</h3>
            <p className="text-muted-foreground max-w-sm mx-auto mb-4">
              Conecta tus primeros canales de atracción para empezar a medir todo en un solo lugar.
            </p>
          </div>
        </div>
      ) : (
        <>
          {/* Date Range */}
          <div className="flex items-center justify-end">
            <DateRangePicker rangeDays={rangeDays} onRangeChange={setRangeDays} />
          </div>

          {/* Section 1: Hero KPI Strip */}
          <AttractionScorecards
            timeSeries={timeSeries}
            totalImpressions={totalImpressions}
            totalVisitors={totalVisitors}
            totalLeads={totalLeads}
            leadConvRate={leadConvRate}
            totalSpend={totalSpend}
            currency="USD"
          />

          {/* Section 2: Charts Side-by-Side (deferred until visible) */}
          <div ref={chartsRef as React.Ref<HTMLDivElement>} className="hidden md:grid md:grid-cols-2 gap-4">
            {chartsVisible ? (
              <>
                <AttractionTrendChart timeSeries={timeSeries} isLoading={tsLoading} />
                <CaptureBreakdownChart channels={allCaptureChannels} isLoading={capLoading} />
              </>
            ) : (
              <div className="h-48 animate-pulse bg-muted rounded-lg col-span-2" />
            )}
          </div>
          <MobileChartsExpand
            timeSeries={timeSeries}
            tsLoading={tsLoading}
            captureChannels={allCaptureChannels}
            capLoading={capLoading}
          />

          {/* Section 3: Conversion Bridge */}
          <ConversionBridge
            impressions={totalImpressions}
            visitors={totalVisitors}
            leads={totalLeads}
          />

          {/* Section 4: Two-Column Layout — Attraction + Capture */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">

            {/* COLUMNA ATRACCIÓN */}
            <div className="space-y-6">
              <div className="border-b border-border pb-2">
                <h3 className="font-semibold text-lg flex items-center text-foreground/90">
                  <Megaphone className="w-5 h-5 mr-2 text-blue-500" /> Atracción
                </h3>
                <p className="text-xs text-muted-foreground mt-1">
                  Canales que generan visibilidad y traen tráfico a tu ecosistema.
                </p>
              </div>

              {paidChannels.length > 0 && (
                <LazyChannelGroup
                  stage="attraction"
                  groupKey="paid"
                  title="Inversión Pagada"
                  overviewChannels={paidChannels}
                  headerIcon={Coins}
                  baseColor="blue"
                  stageId="ATRACCION"
                  onChannelClick={handleChannelClick}
                  onConfigure={onConfigure}
                />
              )}

              {organicChannels.length > 0 && (
                <LazyChannelGroup
                  stage="attraction"
                  groupKey="organic_social"
                  title="Tráfico Orgánico"
                  overviewChannels={organicChannels}
                  headerIcon={TrendingUp}
                  baseColor="blue"
                  stageId="ATRACCION"
                  onChannelClick={handleChannelClick}
                  onConfigure={onConfigure}
                />
              )}
            </div>

            {/* COLUMNA CAPTURA */}
            <div className="space-y-6">
              <div className="border-b border-border pb-2">
                <h3 className="font-semibold text-lg flex items-center text-foreground/90">
                  <UserPlus className="w-5 h-5 mr-2 text-violet-500" /> Captura
                </h3>
                <p className="text-xs text-muted-foreground mt-1">
                  Donde los visitantes se convierten en leads con datos de contacto.
                </p>
              </div>

              <LazyChannelGroup
                stage="capture"
                groupKey="web_infrastructure"
                title="Web & Formularios"
                overviewChannels={webCaptureChannels}
                headerIcon={Globe}
                baseColor="violet"
                stageId="CAPTURA"
                onChannelClick={handleChannelClick}
                onConfigure={onConfigure}
              />

              {messagingCaptureChannels.length > 0 && (
                <LazyChannelGroup
                  stage="capture"
                  groupKey="ai_agent"
                  title="AI Agent & Mensajería"
                  overviewChannels={messagingCaptureChannels}
                  headerIcon={Bot}
                  baseColor="violet"
                  stageId="CAPTURA"
                  onChannelClick={handleChannelClick}
                  onConfigure={onConfigure}
                />
              )}
            </div>
          </div>

          {/* Section 5: Connect More CTA */}
          {(attrOverview?.channelList.some(c => !c.connected) || capOverview?.channelList.some(c => !c.connected)) && (
            <div className="bg-muted/30 border border-dashed border-border rounded-lg p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
              <div>
                <p className="text-sm font-medium text-foreground">Conectar más canales</p>
                <p className="text-xs text-muted-foreground">Expande tu ecosistema para capturar más leads</p>
              </div>
              <div className="flex flex-wrap gap-2">
                {[...attrOverview?.channelList ?? [], ...capOverview?.channelList ?? []]
                  .filter(ch => !ch.connected)
                  .slice(0, 4)
                  .map((ch) => (
                    <button
                      key={ch.slug}
                      onClick={() => onConfigure?.(ch.slug, ch.name)}
                      className="flex items-center gap-1.5 text-xs text-muted-foreground border border-border rounded-md px-3 py-1.5 hover:bg-muted transition-colors"
                    >
                      <Zap className="w-3 h-3" />
                      {ch.name}
                    </button>
                  ))}
              </div>
            </div>
          )}
        </>
      )}

      {/* Full-page dashboards */}
      <MetaAdsDashboardWrapper />
      <ExpandedDashboardWrapper />
    </div>
  );
});
