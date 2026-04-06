'use client';

import React, { useState, useMemo, useCallback } from 'react';
import { useAttractionDetail, useCaptureDetail, useStageTimeSeries } from '../../../hooks/useStageDetail';
import { useGrowthSync } from '../../../context/growth-sync-context';
import { ActionPanel } from '../action-widgets/ActionPanel';
import DetailSkeleton from '../ui/DetailSkeleton';
import DetailError from '../ui/DetailError';
import type { MetricClickData, StageTimeSeries as TSType, ChannelMetric } from '../../../types/metrics';
import { Button } from '@/components/ui/button';
import { Settings, RefreshCw, Plug, Zap, Megaphone, UserPlus, Coins, TrendingUp, Globe, Bot } from 'lucide-react';
import { formatMoney } from '@/lib/format-money';
import { DateRangePicker } from '../ui/DateRangePicker';
import { AttractionScorecards } from '../attraction/AttractionScorecards';
import { AttractionTrendChart } from '../attraction/AttractionTrendChart';
import { CaptureBreakdownChart } from '../attraction/CaptureBreakdownChart';
import { ConversionBridge } from '../attraction/ConversionBridge';
import { ChannelGroup } from '../attraction/ChannelGroup';
import ChannelDetailSidebar from '../sidebar/ChannelDetailSidebar';
import { MetaAdsDashboard } from '../sidebar/meta-ads/MetaAdsDashboard';
import { IgOrganicDashboard } from '../sidebar/ig-organic/IgOrganicDashboard';
import { YouTubeDashboard } from '../sidebar/youtube-organic/YouTubeDashboard';
import { MailDashboard } from '../sidebar/mail/MailDashboard';
import { useGrowthStudioContext } from '../context/GrowthStudioContext';

// ─── Helper ──────────────────────────────────────────────────────────────────

function getMetric(metrics: { name: string; value: number }[], name: string): number {
  return metrics.find((m) => m.name === name)?.value ?? 0;
}

function MetaAdsDashboardWrapper() {
  const { metaAdsDashboardOpen, handleCloseMetaAdsDashboard } = useGrowthStudioContext();
  if (!metaAdsDashboardOpen) return null;
  return <MetaAdsDashboard onClose={handleCloseMetaAdsDashboard} />;
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
  captureChannels,
  capLoading,
}: {
  timeSeries: TSType | undefined;
  tsLoading: boolean;
  captureChannels: ChannelMetric[];
  capLoading: boolean;
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
        {expanded ? 'Ocultar graficos' : 'Ver graficos'}
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
}

export const AttractionCaptureDetail = React.memo(function AttractionCaptureDetail({
  onMetricClick,
  onConfigure,
}: AttractionCaptureDetailProps) {
  const { data: attrData, isLoading: attrLoading, error: attrError, refetch: refetchAttr } = useAttractionDetail();
  const { data: capData, isLoading: capLoading, error: capError, refetch: refetchCap } = useCaptureDetail();
  const { startSync, isSyncing } = useGrowthSync();
  const [isPanelOpen, setIsPanelOpen] = useState(false);
  const [rangeDays, setRangeDays] = useState(30);
  const [sidebarChannel, setSidebarChannel] = useState<ChannelMetric | null>(null);
  const granularity = rangeDays >= 90 ? 'weekly' : 'daily';
  const { data: timeSeries, isLoading: tsLoading } = useStageTimeSeries('attraction', 'reach', rangeDays, granularity);

  // ─── Computed totals ─────────────────────────────────────────────────────
  // NOTE: reach/users are NON_AGGREGABLE (unique people) — never sum cross-group.
  // Use impressions (ADDITIVE) as the top-of-funnel awareness metric.
  // Use GA4 website users/sessions as the single authoritative visitor count.

  const { totalImpressions, totalVisitors, totalSpend } = useMemo(() => {
    if (!attrData) return { totalImpressions: 0, totalVisitors: 0, totalSpend: 0 };
    const attrGroups = [attrData.organicSocial, attrData.ga4Search, attrData.paid, attrData.outbound];
    const websiteUsers = attrData.website?.totals.users;
    const websiteSessions = attrData.website?.totals.sessions;
    return {
      totalImpressions: attrGroups.reduce((sum, g) => sum + (g.totals.impressions ?? 0), 0),
      totalVisitors: websiteUsers ?? websiteSessions ?? 0,
      totalSpend: attrGroups.reduce((sum, g) => sum + (g.totals.spend ?? 0), 0),
    };
  }, [attrData]);

  const totalLeads = capData?.headerKpis.totalLeads || 0;
  const leadConvRate = useMemo(() => totalVisitors > 0 ? (totalLeads / totalVisitors) * 100 : 0, [totalVisitors, totalLeads]);


  // ─── Channel groupings ──────────────────────────────────────────────────

  const paidChannels = useMemo(() => attrData?.paid.channels || [], [attrData?.paid.channels]);
  const organicChannels = useMemo(() => [
    ...(attrData?.organicSocial.channels || []),
    ...(attrData?.ga4Search.channels || []),
  ], [attrData?.organicSocial.channels, attrData?.ga4Search.channels]);


  const webCaptureChannels = useMemo(() => capData?.webInfrastructure.channels || [], [capData?.webInfrastructure.channels]);
  const messagingCaptureChannels = useMemo(() => capData?.aiAgent.channels || [], [capData?.aiAgent.channels]);
  const allCaptureChannels = useMemo(
    () => [...webCaptureChannels, ...messagingCaptureChannels],
    [webCaptureChannels, messagingCaptureChannels],
  );

  const availableChannels = useMemo(() => [
    ...(attrData?.available?.channels || []),
    ...(capData?.available?.channels || []),
  ], [attrData?.available?.channels, capData?.available?.channels]);

  // ─── Summary strings ───────────────────────────────────────────────────

  const paidSummary = useMemo(() => {
    const impressions = paidChannels.reduce((s, ch) => s + getMetric(ch.metrics, 'impressions'), 0);
    return `${impressions.toLocaleString('es-ES')} impresiones`;
  }, [paidChannels]);

  const paidCurrency = useMemo(() => {
    for (const ch of paidChannels) {
      for (const m of ch.metrics) {
        if (m.currency) return m.currency;
      }
    }
    return 'USD';
  }, [paidChannels]);

  const paidSpendSummary = useMemo(() => {
    const spend = paidChannels.reduce((s, ch) => s + getMetric(ch.metrics, 'spend'), 0);
    return spend > 0 ? `${formatMoney(spend, paidCurrency, { fractionDigits: 0 })} invertidos` : undefined;
  }, [paidChannels, paidCurrency]);

  const organicSummary = useMemo(() => {
    const sessions = organicChannels.reduce((s, ch) => s + getMetric(ch.metrics, 'sessions'), 0);
    return `${sessions.toLocaleString('es-ES')} sesiones`;
  }, [organicChannels]);

  const webCaptureSummary = useMemo(() => {
    const leads = webCaptureChannels.reduce((s, ch) => s + getMetric(ch.metrics, 'leads'), 0);
    const pct = totalLeads > 0 ? ((leads / totalLeads) * 100).toFixed(1) : '0';
    return `${leads} leads (${pct}%)`;
  }, [webCaptureChannels, totalLeads]);

  const msgCaptureSummary = useMemo(() => {
    const leads = messagingCaptureChannels.reduce((s, ch) => s + getMetric(ch.metrics, 'leads'), 0);
    const pct = totalLeads > 0 ? ((leads / totalLeads) * 100).toFixed(1) : '0';
    return `${leads} leads (${pct}%)`;
  }, [messagingCaptureChannels, totalLeads]);

  // ─── Handlers ──────────────────────────────────────────────────────────

  const handleChannelClick = useCallback((channel: ChannelMetric) => {
    setSidebarChannel(channel);
  }, []);

  // ─── Loading / Error / Empty ────────────────────────────────────────────

  if (attrLoading || capLoading) {
    return <DetailSkeleton isLoading><></></DetailSkeleton>;
  }

  if (attrError || capError) {
    return (
      <DetailError
        error={attrError instanceof Error ? attrError : (capError instanceof Error ? capError : new Error('Error desconocido'))}
        onRetry={() => { void refetchAttr(); void refetchCap(); }}
        lastData={attrData || capData}
      />
    );
  }

  if (!attrData || !capData) return null;

  const hasAnyAttractionData = [attrData.organicSocial, attrData.ga4Search, attrData.paid, attrData.outbound, attrData.website]
    .some(g => g?.channels.some(ch => ch.connected && ch.metrics.some(m => m.value > 0)));
  const hasCaptureData = totalLeads > 0;
  const isEmpty = !hasAnyAttractionData && !hasCaptureData;

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
            currency={paidCurrency}
          />

          {/* Section 2: Charts Side-by-Side */}
          <div className="hidden md:grid md:grid-cols-2 gap-4">
            <AttractionTrendChart timeSeries={timeSeries} isLoading={tsLoading} />
            <CaptureBreakdownChart channels={allCaptureChannels} isLoading={capLoading} />
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

            {/* COLUMNA ATRACCION */}
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
                <ChannelGroup
                  title="Inversión Pagada"
                  variant="paid"
                  channels={paidChannels}
                  headerIcon={Coins}
                  baseColor="blue"
                  summary={paidSummary}
                  summaryExtra={paidSpendSummary}
                  onChannelClick={handleChannelClick}
                  onConfigure={onConfigure}
                />
              )}

              {organicChannels.length > 0 && (
                <ChannelGroup
                  title="Trafico Organico"
                  variant="organic"
                  channels={organicChannels}
                  headerIcon={TrendingUp}
                  baseColor="blue"
                  summary={organicSummary}
                  onChannelClick={handleChannelClick}
                  onConfigure={onConfigure}
                />
              )}

              {/* Outbound oculto hasta tener datos reales */}
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

              <ChannelGroup
                title="Web & Formularios"
                variant="capture_web"
                channels={webCaptureChannels}
                headerIcon={Globe}
                baseColor="violet"
                summary={webCaptureSummary}
                onChannelClick={handleChannelClick}
                onConfigure={onConfigure}
              />

              {messagingCaptureChannels.length > 0 && (
                <ChannelGroup
                  title="AI Agent & Mensajeria"
                  variant="capture_messaging"
                  channels={messagingCaptureChannels}
                  headerIcon={Bot}
                  baseColor="violet"
                  summary={msgCaptureSummary}
                  onChannelClick={handleChannelClick}
                  onConfigure={onConfigure}
                />
              )}
            </div>
          </div>

          {/* Section 5: Connect More CTA */}
          {availableChannels.length > 0 && (
            <div className="bg-muted/30 border border-dashed border-border rounded-lg p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
              <div>
                <p className="text-sm font-medium text-foreground">Conectar mas canales</p>
                <p className="text-xs text-muted-foreground">Expande tu ecosistema para capturar mas leads</p>
              </div>
              <div className="flex flex-wrap gap-2">
                {availableChannels.slice(0, 4).map((ch) => (
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

      {/* Channel Detail Sidebar */}
      <ChannelDetailSidebar
        isOpen={sidebarChannel !== null}
        onClose={() => setSidebarChannel(null)}
        channel={sidebarChannel}
      />

      {/* Full-page dashboards */}
      <MetaAdsDashboardWrapper />
      <ExpandedDashboardWrapper />
    </div>
  );
});
