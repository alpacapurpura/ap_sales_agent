'use client';

import React, { useState, useMemo, useCallback } from 'react';
import { useAttractionDetail, useCaptureDetail, useStageTimeSeries } from '../../../hooks/useStageDetail';
import { useMetaInitialLoad } from '../../../hooks/useMetaInitialLoad';
import { ActionPanel } from '../action-widgets/ActionPanel';
import DetailSkeleton from '../ui/DetailSkeleton';
import DetailError from '../ui/DetailError';
import type { MetricClickData, StageTimeSeries } from '../../../types/metrics';
import { Button } from '@/components/ui/button';
import { Settings, Download, Loader2, CheckCircle2, Plug } from 'lucide-react';
import { BrandIcon } from '@/components/ui/brand-icons';
import { DateRangePicker } from '../ui/DateRangePicker';
import { AttractionScorecards } from '../attraction/AttractionScorecards';
import { AttractionTrendChart } from '../attraction/AttractionTrendChart';
import { ChannelComparisonChart } from '../attraction/ChannelComparisonChart';

/** Mobile-only expandable chart section — hidden on md+ */
function MobileChartsExpand({ timeSeries, tsLoading }: { timeSeries: StageTimeSeries | undefined; tsLoading: boolean }) {
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
          <ChannelComparisonChart timeSeries={timeSeries} isLoading={tsLoading} />
        </div>
      )}
    </div>
  );
}

interface AttractionCaptureDetailProps {
  onMetricClick?: (metric: MetricClickData) => void;
  onConfigure?: (slug: string, name: string) => void;
}

export const AttractionCaptureDetail = React.memo(function AttractionCaptureDetail({ onMetricClick, onConfigure }: AttractionCaptureDetailProps) {
  const { data: attrData, isLoading: attrLoading, error: attrError, refetch: refetchAttr } = useAttractionDetail();
  const { data: capData, isLoading: capLoading, error: capError, refetch: refetchCap } = useCaptureDetail();
  const { trigger: triggerLoad, isLoading: isLoadingMeta, result: loadResult } = useMetaInitialLoad();
  const [isPanelOpen, setIsPanelOpen] = useState(false);
  const [rangeDays, setRangeDays] = useState(30);
  const granularity = rangeDays >= 90 ? 'weekly' : 'daily';
  const { data: timeSeries, isLoading: tsLoading } = useStageTimeSeries('attraction', 'visitors', rangeDays, granularity);

  const { totalReach, totalVisitors, totalSpend } = useMemo(() => {
    if (!attrData) return { totalReach: 0, totalVisitors: 0, totalSpend: 0 };
    const attrGroups = [attrData.organicSocial, attrData.ga4Search, attrData.paid, attrData.outbound];
    return {
      totalReach: attrGroups.reduce((sum, g) => sum + (g.totals.reach ?? 0), 0),
      totalVisitors: attrGroups.reduce((sum, g) => sum + (g.totals.visitors ?? g.totals.sessions ?? 0), 0),
      totalSpend: attrGroups.reduce((sum, g) => sum + (g.totals.spend ?? 0), 0),
    };
  }, [attrData]);

  const totalLeads = capData?.headerKpis.totalLeads || 0;
  const leadConvRate = useMemo(() => totalVisitors > 0 ? (totalLeads / totalVisitors) * 100 : 0, [totalVisitors, totalLeads]);

  const combinedOrganic = useMemo(() => [
    ...(attrData?.organicSocial.channels || []),
    ...(attrData?.ga4Search.channels || []),
  ], [attrData?.organicSocial.channels, attrData?.ga4Search.channels]);

  const captureChannels = useMemo(() => [
    ...(capData?.webInfrastructure.channels || []),
    ...(capData?.aiAgent.channels || []),
  ], [capData?.webInfrastructure.channels, capData?.aiAgent.channels]);

  const handleMetricClick = useCallback((stageId: 'ATRACCION' | 'CAPTURA', channel: any, metricName: string, val: number) => {
    if (onMetricClick) {
      onMetricClick({
        stageId,
        channelSlug: channel.slug,
        channelName: channel.name,
        metricName,
        currentValue: val,
        channelMetrics: channel.metrics
      });
    }
  }, [onMetricClick]);

  if (attrLoading || capLoading) {
    return (
      <DetailSkeleton isLoading>
        <></>
      </DetailSkeleton>
    );
  }

  if (attrError || capError) {
    return (
      <DetailError
        error={attrError instanceof Error ? attrError : (capError instanceof Error ? capError : new Error('Error desconocido'))}
        onRetry={() => {
          void refetchAttr();
          void refetchCap();
        }}
        lastData={attrData || capData}
      />
    );
  }

  // Si no hay datos (empty state base)
  if (!attrData || !capData) return null;

  // Formatters
  const formatNum = (num: number) => num.toLocaleString('es-ES');
  const formatMoney = (num: number) => `$${num.toLocaleString('es-ES', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;

  // Helpers to get specific metrics
  const getMetric = (metrics: any[], name: string) => metrics.find((m) => m.name === name)?.value ?? 0;

  // Organizar canales
  const paidChannels = attrData.paid.channels;
  const availableChannels = attrData.available?.channels || [];

  const ChannelRow = ({ channel, stageId, defaultMetricName, defaultMetricLabel }: { channel: any, stageId: 'ATRACCION' | 'CAPTURA', defaultMetricName: string, defaultMetricLabel: string }) => {
    if (!channel.connected) {
      // Disponible (Available) style
      return (
        <div className="bg-card text-card-foreground border border-border text-center p-3 rounded-md hover:bg-muted cursor-pointer transition-colors shadow-sm flex flex-col items-center justify-center gap-2"
          onClick={() => onConfigure && onConfigure(channel.slug, channel.name)}>
          <span className="text-xl">⚡</span>
          <span className="text-xs font-medium text-foreground">{channel.name}</span>
        </div>
      );
    }

    const hasData = channel.metrics && channel.metrics.length > 0 && channel.metrics.some((m: any) => m.value > 0);

    // Pick icon and color based on channel slug or type
    let Icon: React.ReactNode = '🔹';
    
    // We'll use specific colors for logos but semantic colors for default backgrounds where possible.
    let bgColor = 'bg-blue-100 text-blue-600 dark:bg-blue-500/20 dark:text-blue-400';
    let borderColor = 'hover:border-blue-300 dark:hover:border-blue-700';
    
    if (channel.slug.includes('meta') || channel.slug.includes('fb') || channel.slug.includes('ig') || channel.slug.includes('instagram')) {
      Icon = <BrandIcon name={channel.slug} className="w-5 h-5 text-blue-600 dark:text-blue-400" />;
      bgColor = 'bg-blue-100 text-blue-600 dark:bg-blue-500/20 dark:text-blue-400';
    } else if (channel.slug.includes('google') || channel.slug.includes('yt') || channel.slug.includes('youtube')) {
      Icon = <BrandIcon name={channel.slug} className="w-5 h-5 text-red-600 dark:text-red-400" />;
      bgColor = 'bg-red-100 text-red-600 dark:bg-red-500/20 dark:text-red-400';
      borderColor = 'hover:border-red-300 dark:hover:border-red-700';
    } else if (channel.slug.includes('whatsapp') || channel.slug.includes('wa')) {
      Icon = <BrandIcon name={channel.slug} className="w-5 h-5 text-green-600 dark:text-green-400" />;
      bgColor = 'bg-green-100 text-green-600 dark:bg-green-500/20 dark:text-green-400';
      borderColor = 'hover:border-green-300 dark:hover:border-green-700';
    } else if (channel.slug.includes('linkedin') || channel.slug.includes('tiktok') || channel.slug.includes('manychat')) {
      Icon = <BrandIcon name={channel.slug} className="w-5 h-5" />;
      bgColor = 'bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-300';
      borderColor = 'hover:border-slate-300 dark:hover:border-slate-600';
    } else {
      bgColor = 'bg-muted text-muted-foreground';
      borderColor = 'hover:border-input';
      Icon = '❖';
    }

    if (!hasData) {
      return (
        <div 
          className="border border-border rounded-md p-3 justify-between items-center bg-muted/30 hover:bg-muted/60 transition-colors flex cursor-pointer"
          onClick={() => handleMetricClick(stageId, channel, defaultMetricName, 0)}
        >
          <div className="flex items-center gap-3">
            <div className={`w-8 h-8 rounded flex items-center justify-center font-bold ${bgColor}`}>{Icon}</div>
            <div>
              <p className="text-sm font-medium text-foreground">{channel.name}</p>
              <p className="text-[10px] text-amber-600 dark:text-amber-500 font-semibold">Conectado, sin campañas</p>
            </div>
          </div>
          <div className="text-right">
            <p className="text-sm font-bold text-muted-foreground underline decoration-dashed underline-offset-4">
              0
            </p>
            <p className="text-[10px] text-muted-foreground">{defaultMetricLabel}</p>
          </div>
        </div>
      );
    }

    const mainVal = getMetric(channel.metrics, defaultMetricName) || getMetric(channel.metrics, 'reach') || getMetric(channel.metrics, 'visitors');
    let fallbackLabel = defaultMetricLabel;
    if (getMetric(channel.metrics, defaultMetricName) === 0 && getMetric(channel.metrics, 'reach') > 0) {
      fallbackLabel = 'alcance';
    }

    return (
      <div 
        className={`border border-border rounded-md p-3 flex justify-between items-center bg-card transition-colors group cursor-pointer ${borderColor}`}
        onClick={() => handleMetricClick(stageId, channel, defaultMetricName, mainVal)}
      >
        <div className="flex items-center gap-3">
          <div className={`w-8 h-8 rounded flex items-center justify-center font-bold ${bgColor}`}>{Icon}</div>
          <div>
            <p className="text-sm font-medium text-foreground">{channel.name}</p>
            <p className="text-[10px] text-emerald-600 dark:text-emerald-500">Activo</p>
          </div>
        </div>
        <div className="text-right">
          <p className="text-sm font-bold text-foreground transition-colors group-hover:text-blue-600 dark:group-hover:text-blue-400 underline decoration-dashed underline-offset-4">
            {formatNum(mainVal)}
          </p>
          <p className="text-[10px] text-muted-foreground">{fallbackLabel}</p>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-12 animate-fade-in bg-background p-6 rounded-2xl text-foreground border border-border">
      
      {/* Title & Actions Row */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground flex items-center gap-2">
            Atracción &amp; Captura
            <span className="px-2 py-0.5 mt-1 rounded-full bg-blue-100 dark:bg-blue-500/20 text-blue-700 dark:text-blue-400 text-xs font-medium tracking-wide">ETAPA 1 y 2</span>
          </h1>
          <p className="text-muted-foreground text-sm mt-1">Tráfico, alcance y conversión a leads desde todos tus canales.</p>
        </div>
        <div className="flex items-center gap-3">
           <Button variant="outline" onClick={() => triggerLoad(30)} disabled={isLoadingMeta}>
             {isLoadingMeta ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : (loadResult ? <CheckCircle2 className="mr-2 h-4 w-4" /> : <Download className="mr-2 h-4 w-4" />)}
             {loadResult ? 'Datos Meta OK' : 'Datos Meta'}
           </Button>
           <Button onClick={() => setIsPanelOpen(true)}>
             <Settings className="mr-2 h-4 w-4" /> Gestionar Etapa
           </Button>
        </div>
      </div>

      <ActionPanel isOpen={isPanelOpen} onClose={() => setIsPanelOpen(false)} />

      {/* Scorecards + Charts Section */}
      {totalReach === 0 && totalVisitors === 0 && totalLeads === 0 ? (
        <div className="bg-card rounded-xl p-6 shadow-sm border border-border">
          <div className="text-center py-12 px-4 rounded-xl border-2 border-dashed border-border bg-muted/50">
            <Plug className="w-12 h-12 text-muted-foreground mx-auto mb-3" />
            <h3 className="text-lg font-semibold text-foreground mb-1">Tu ecosistema digital esta vacio</h3>
            <p className="text-muted-foreground max-w-sm mx-auto mb-4">Conecta tus primeros canales de atraccion para empezar a medir todo en un solo lugar.</p>
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Date Range Picker */}
          <div className="flex items-center justify-end">
            <DateRangePicker rangeDays={rangeDays} onRangeChange={setRangeDays} />
          </div>

          {/* KPI Scorecards with sparklines */}
          <AttractionScorecards
            timeSeries={timeSeries}
            totalReach={totalReach}
            totalVisitors={totalVisitors}
            totalLeads={totalLeads}
            leadConvRate={leadConvRate}
          />

          {/* Charts: Stacked Area + Horizontal Bar side by side */}
          <div className="hidden md:grid md:grid-cols-2 gap-6">
            <AttractionTrendChart timeSeries={timeSeries} isLoading={tsLoading} />
            <ChannelComparisonChart timeSeries={timeSeries} isLoading={tsLoading} />
          </div>

          {/* Mobile: expandable charts */}
          <MobileChartsExpand timeSeries={timeSeries} tsLoading={tsLoading} />
        </div>
      )}

      {/* Detail Split Columns */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
        
        {/* COLUMNA ATRACCIÓN */}
        <div className="space-y-6">
          <h3 className="font-semibold text-lg flex items-center text-foreground/90 border-b border-border pb-2">
            🔗 Atracción
          </h3>
          
          {/* Paid Ads */}
          <div className="bg-card rounded-lg border border-border shadow-sm overflow-hidden">
            <div className="bg-muted/50 px-4 py-3 border-b border-border flex justify-between items-center">
              <span className="font-medium text-sm text-foreground/90 flex items-center">📢 Publicidad Pagada</span>
              <div className="flex gap-4 text-xs font-medium">
                <span className="text-muted-foreground">{formatNum(attrData.paid.totals.sessions ?? attrData.paid.totals.visitors ?? 0)} vis.</span>
                <span className="text-emerald-600 dark:text-emerald-500">{formatMoney(attrData.paid.totals.spend ?? 0)}</span>
              </div>
            </div>
            <div className="p-4 grid grid-cols-1 gap-2">
              {paidChannels.map((c) => <ChannelRow key={c.slug} channel={c} stageId="ATRACCION" defaultMetricName="sessions" defaultMetricLabel="visitantes" />)}
            </div>
          </div>

          {/* Organic & Direct */}
          <div className="bg-card rounded-lg border border-border shadow-sm overflow-hidden">
            <div className="bg-muted/50 px-4 py-3 border-b border-border flex justify-between items-center">
              <span className="font-medium text-sm text-foreground/90 flex items-center">👥 Tráfico Orgánico y Directo</span>
            </div>
            <div className="p-4 grid grid-cols-1 gap-2">
              {combinedOrganic.map((c) => <ChannelRow key={c.slug} channel={c} stageId="ATRACCION" defaultMetricName="sessions" defaultMetricLabel="visitantes" />)}
            </div>
          </div>

          {/* Available */}
          <div className="bg-muted/30 rounded-lg border border-border border-dashed shadow-sm overflow-hidden">
            <div className="px-4 py-3 border-b border-transparent flex justify-between items-center text-muted-foreground">
              <span className="font-medium text-sm flex items-center">➕ Canales Disponibles</span>
            </div>
            <div className="p-4 grid grid-cols-1 sm:grid-cols-3 gap-3">
              {availableChannels.map((c) => <ChannelRow key={c.slug} channel={c} stageId="ATRACCION" defaultMetricName="" defaultMetricLabel="" />)}
            </div>
          </div>

        </div>

        {/* COLUMNA CAPTURA */}
        <div className="space-y-6">
          <h3 className="font-semibold text-lg flex items-center text-foreground/90 border-b border-border pb-2">
            📥 Captura
          </h3>

          <div className="bg-card rounded-lg border border-border shadow-sm overflow-hidden border-l-4 border-l-primary hover:border-l-primary/80 transition-colors">
            <div className="bg-primary/5 px-4 py-3 border-b border-border flex justify-between items-center">
              <span className="font-medium text-sm flex items-center text-foreground/90">🤖 Agente y Formularios</span>
              <div className="flex gap-4 text-xs font-medium">
                <span className="text-primary font-bold">{formatNum(getMetric(captureChannels.flatMap(c => c.metrics), 'leads'))} leads</span>
              </div>
            </div>
            <div className="p-4 grid grid-cols-1 gap-2">
              {captureChannels.map((c) => <ChannelRow key={c.slug} channel={c} stageId="CAPTURA" defaultMetricName="leads" defaultMetricLabel="leads" />)}
            </div>
          </div>

        </div>

      </div>
    </div>
  );
});
