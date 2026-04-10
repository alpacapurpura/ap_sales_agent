'use client';

import React, { useState, useMemo, useCallback } from 'react';
import { useNurtureDetail, useOpportunityDetail } from '../../../hooks/useStageDetail';
import { ActionPanel } from '../action-widgets/ActionPanel';
import DetailSkeleton from '../ui/DetailSkeleton';
import DetailError from '../ui/DetailError';
import type { MetricClickData } from '../../../types/metrics';
import { Button } from '@/components/ui/button';
import { Settings, Calendar, Flame, Coins, Target, AlertTriangle, Lightbulb, MailOpen, Workflow, Repeat, Crosshair, CalendarCheck, ShoppingCart, Plug } from 'lucide-react';
import { BrandIcon } from '@/components/ui/brand-icons';
import { formatMoney } from '@/lib/format-money';
import { useTenantLocale } from '@/features/tenant/context/tenant-locale-context';
import { formatTenantTime } from '@/lib/format-date';
import { ChannelChip } from '../channel-widgets/ChannelChip';
import { ChannelRow } from '../channel-widgets/ChannelRow';
import { classifyChannel } from '../../../lib/classifyChannel';
import type { ChannelMetric } from '../../../types/metrics';

interface NurtureOpportunityDetailProps {
  onMetricClick?: (metric: MetricClickData) => void;
  onChannelClick?: (channel: ChannelMetric) => void;
  onConfigure?: (slug: string, name: string) => void;
  onDisconnectedClick?: (channel: ChannelMetric) => void;
  onNoDataClick?: (channel: ChannelMetric) => void;
}

export const NurtureOpportunityDetail = React.memo(function NurtureOpportunityDetail({ onMetricClick, onChannelClick, onConfigure, onDisconnectedClick, onNoDataClick }: NurtureOpportunityDetailProps) {
  const { timezone } = useTenantLocale();
  const { data: nurtureData, isLoading: nurtureLoading, error: nurtureError, refetch: refetchNurture } = useNurtureDetail();
  const { data: oppData, isLoading: oppLoading, error: oppError, refetch: refetchOpp } = useOpportunityDetail();
  const [isPanelOpen, setIsPanelOpen] = useState(false);

  const { totalNurtureLeads, totalMqls, totalNurtureSpend, totalSqls, oppConvRate, costPerSql } = useMemo(() => {
    if (!nurtureData || !oppData) return { totalNurtureLeads: 0, totalMqls: 0, totalNurtureSpend: 0, totalSqls: 0, oppConvRate: 0, costPerSql: 0 };
    const _totalNurtureLeads =
      (nurtureData.retargeting.totals.reach || nurtureData.retargeting.totals.visitors || 0) +
      (nurtureData.automation.totals.contacts || nurtureData.automation.totals.leads || 0);
    const _totalMqls = nurtureData.headerKpis.totalMqls || 0;
    const _totalNurtureSpend = nurtureData.retargeting.totals.spend || 0;
    const _totalSqls = oppData.headerKpis.totalSqls || 0;
    const _oppConvRate = _totalMqls > 0 ? (_totalSqls / _totalMqls) * 100 : 0;
    const _costPerSql = _totalSqls > 0 ? _totalNurtureSpend / _totalSqls : 0;
    return {
      totalNurtureLeads: _totalNurtureLeads,
      totalMqls: _totalMqls,
      totalNurtureSpend: _totalNurtureSpend,
      totalSqls: _totalSqls,
      oppConvRate: _oppConvRate,
      costPerSql: _costPerSql,
    };
  }, [nurtureData, oppData]);

  const nurtureChannels = useMemo(() => {
    if (!nurtureData) return [];
    return nurtureData.automation.channels.map(c => {
      if (c.slug.includes('mail')) return { ...c, name: 'eMailing Nurturing' };
      if (c.slug.includes('ai-sdr') || c.slug.includes('agent')) return { ...c, name: 'Nico Sales Agent', slug: 'nico-agent' };
      return c;
    });
  }, [nurtureData]);

  const retargetingChannels = useMemo(() => {
    if (!nurtureData) return [];
    return nurtureData.retargeting.channels.map(c => {
      if (c.slug.includes('meta') || c.slug.includes('fb') || c.slug.includes('ig')) return { ...c, name: 'Meta Retargeting' };
      return c;
    });
  }, [nurtureData]);

  const checkoutChannels = oppData?.checkout.channels;
  const paymentLinksChannels = oppData?.paymentLinks.channels;
  const oppCheckoutChannels = useMemo(() => [
    ...(checkoutChannels || []),
    ...(paymentLinksChannels || []),
  ], [checkoutChannels, paymentLinksChannels]);

  const activeBottlenecks = useMemo(() => oppData?.bottlenecks.filter(b => b.severity !== 'normal') ?? [], [oppData]);

  const handleMetricClick = useCallback((stageId: 'NUTRICION' | 'OPORTUNIDAD', channel: any, metricName: string, val: number) => {
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

  if (nurtureLoading || oppLoading) {
    return (
      <DetailSkeleton isLoading>
        <></>
      </DetailSkeleton>
    );
  }

  if (nurtureError || oppError) {
    return (
      <DetailError
        error={nurtureError instanceof Error ? nurtureError : (oppError instanceof Error ? oppError : new Error('Error desconocido'))}
        onRetry={() => {
          void refetchNurture();
          void refetchOpp();
        }}
        lastData={nurtureData || oppData}
      />
    );
  }

  if (!nurtureData || !oppData) return null;

  // Extract currency from retargeting channel metrics (first available)
  const currency = (() => {
    for (const ch of nurtureData.retargeting.channels) {
      for (const m of ch.metrics) {
        if (m.currency) return m.currency;
      }
    }
    return 'USD';
  })();

  // Formatters
  const formatNum = (num: number) => num.toLocaleString('es-ES');
  const fmtMoney = (num: number) => formatMoney(num, currency, { fractionDigits: 0 });

  // Helper to get specific metric
  const getMetric = (metrics: any[], name: string) => metrics.find((m) => m.name === name)?.value ?? 0;

  const oppQualificationChannels = oppData.qualification.channels || [];
  const availableNurtureChannels = nurtureData.available?.channels || [];
  const availableOppChannels = oppData.available?.channels || [];

  // Helper: split a channel list into active rows + chips
  const splitChannels = (channels: any[]) => {
    const rows: any[] = [];
    const chips: any[] = [];
    for (const ch of channels) {
      const cat = classifyChannel(ch);
      if (cat === 'active' || cat === 'proximamente') rows.push(ch);
      else chips.push(ch);
    }
    return { rows, chips };
  };

  const NurtureChannelRow = ({ channel, stageId, defaultMetricName, defaultMetricLabel, baseColor }: { channel: any, stageId: 'NUTRICION' | 'OPORTUNIDAD', defaultMetricName: string, defaultMetricLabel: string, baseColor?: string }) => {
    let Icon: React.ReactNode = '🔹';
    let bgColor = 'bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-300';
    let borderColor = 'hover:border-slate-300 dark:hover:border-slate-600';

    // Custom colors for this specific view based on stage
    if (baseColor === 'amber') {
      bgColor = 'bg-amber-100 text-amber-600 dark:bg-amber-500/20 dark:text-amber-400';
      borderColor = 'hover:border-amber-300 dark:hover:border-amber-700';
    } else if (baseColor === 'orange') {
      bgColor = 'bg-orange-100 text-orange-600 dark:bg-orange-500/20 dark:text-orange-400';
      borderColor = 'hover:border-orange-300 dark:hover:border-orange-700';
    } else if (baseColor === 'emerald') {
      bgColor = 'bg-emerald-100 text-emerald-600 dark:bg-emerald-500/20 dark:text-emerald-400';
      borderColor = 'hover:border-emerald-300 dark:hover:border-emerald-700';
    } else if (baseColor === 'blue') {
      bgColor = 'bg-blue-100 text-blue-600 dark:bg-blue-500/20 dark:text-blue-400';
      borderColor = 'hover:border-blue-300 dark:hover:border-blue-700';
    } else if (baseColor === 'green') {
      bgColor = 'bg-green-100 text-green-600 dark:bg-green-500/20 dark:text-green-400';
      borderColor = 'hover:border-green-300 dark:hover:border-green-700';
    }

    if (channel.slug.includes('meta') || channel.slug.includes('fb') || channel.slug.includes('ig') || channel.slug.includes('instagram')) {
      Icon = <BrandIcon name={channel.slug} className="w-5 h-5" />;
    } else if (channel.slug.includes('whatsapp') || channel.slug.includes('wa') || channel.slug.includes('nico-agent')) {
      Icon = <BrandIcon name={channel.slug.includes('nico-agent') ? 'nicolify' : channel.slug} className="w-5 h-5" />;
    } else if (channel.slug.includes('stripe') || channel.slug.includes('checkout')) {
      Icon = <BrandIcon name={channel.slug} className="w-5 h-5" />;
    } else if (channel.slug.includes('typeform') || channel.slug.includes('form')) {
      Icon = <BrandIcon name={channel.slug} className="w-5 h-5" />;
    } else if (channel.slug.includes('calendly') || channel.slug.includes('cal')) {
      Icon = <BrandIcon name={channel.slug} className="w-5 h-5" />;
    } else if (channel.slug.includes('mail') || channel.slug.includes('email')) {
      Icon = <BrandIcon name={channel.slug} className="w-5 h-5" />;
    } else {
      Icon = '❖';
    }

    const mainVal = getMetric(channel.metrics, defaultMetricName) || getMetric(channel.metrics, 'total_mqls') || getMetric(channel.metrics, 'total_sqls') || channel.value || 0;

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
          <p className="text-sm font-bold text-foreground transition-colors group-hover:text-amber-600 dark:group-hover:text-amber-400 underline decoration-dashed underline-offset-4">
            {formatNum(mainVal)}
          </p>
          <p className="text-[10px] text-muted-foreground">{defaultMetricLabel}</p>
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
            Nutrición &amp; Oportunidad
            <span className="px-2 py-0.5 mt-1 rounded-full bg-amber-100 dark:bg-amber-500/20 text-amber-700 dark:text-amber-400 text-xs font-medium tracking-wide">ETAPA 3 y 4</span>
          </h1>
          <p className="text-muted-foreground text-sm mt-1">Calentamiento de leads (MQLs) y generación de intenciones de compra (SQLs).</p>
        </div>
        <div className="flex items-center gap-3">
          <p className="text-xs text-muted-foreground italic mr-2">Actualizado: {nurtureData.lastUpdated ? formatTenantTime(nurtureData.lastUpdated, timezone) : 'Hoy'}</p>
          <Button variant="outline" onClick={() => setIsPanelOpen(true)}>
            <Calendar className="mr-2 h-4 w-4" /> Últimos 30 días
          </Button>
          <Button className="bg-amber-500 hover:bg-amber-600 text-white" onClick={() => setIsPanelOpen(true)}>
            <Settings className="mr-2 h-4 w-4" /> Gestionar Etapa
          </Button>
        </div>
      </div>

      <ActionPanel isOpen={isPanelOpen} onClose={() => setIsPanelOpen(false)} />

      {/* Global Performance Header */}
      <div className="bg-card rounded-xl p-6 shadow-sm border border-border relative overflow-hidden">
        <h2 className="text-lg font-semibold mb-6 flex items-center text-foreground/90">
          <Flame className="w-5 h-5 mr-2 text-amber-500" /> Termómetro de Ventas
        </h2>

        {totalNurtureLeads === 0 && totalMqls === 0 && totalSqls === 0 ? (
          <div className="text-center py-12 px-4 rounded-xl border-2 border-dashed border-border bg-muted/50">
            <Plug className="w-12 h-12 text-muted-foreground mx-auto mb-3" />
            <h3 className="text-lg font-semibold text-foreground mb-1">Sin leads en nutrición</h3>
            <p className="text-muted-foreground max-w-sm mx-auto mb-4">No hay datos suficientes para mostrar el termómetro de ventas.</p>
          </div>
        ) : (
          <div className="relative mb-6">
            {/* Horizontal Lines (Background Layer) */}
            <div className="hidden md:block absolute w-[10%] h-[2px] bg-gradient-to-r from-amber-200 to-amber-400 dark:from-amber-900 dark:to-amber-700 top-[40%] left-[20%] z-0"></div>
            <div className="hidden md:block absolute w-[10%] h-[2px] bg-gradient-to-r from-amber-400 to-orange-400 dark:from-amber-700 dark:to-orange-700 top-[40%] left-[45%] z-0"></div>
            <div className="hidden md:block absolute w-[10%] h-[2px] bg-gradient-to-r from-orange-400 to-orange-600 dark:from-orange-700 dark:to-orange-500 top-[40%] left-[70%] z-0"></div>

            {/* Metrics Row (Foreground Layer) */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 relative z-10 w-full mb-6">
              <div className="bg-background p-5 rounded-lg border border-border shadow-sm flex flex-col items-center justify-center relative">
                <span className="text-[10px] text-muted-foreground font-bold uppercase mb-1">Base en Nutrición</span>
                <span className="text-3xl font-black text-foreground">{formatNum(totalNurtureLeads)}</span>
                <span className="text-xs text-muted-foreground mt-1 mb-3">Leads Activos</span>
                <span className="text-xs text-amber-600 dark:text-amber-400 font-medium" title="Inversión en Retargeting y Automatizaciones">
                  <Coins className="w-3 h-3 mr-1 inline" /> {fmtMoney(totalNurtureSpend)} Gasto
                </span>
              </div>
              <div className="bg-background p-5 rounded-lg border border-amber-500/20 shadow-sm flex flex-col items-center justify-center relative ring-1 ring-amber-500/10">
                <span className="text-[10px] text-amber-600 dark:text-amber-500 font-bold uppercase mb-1">Interés Demostrado (MQL)</span>
                <span className="text-4xl font-black text-amber-600 dark:text-amber-500">{formatNum(totalMqls)}</span>
                <span className="text-xs text-amber-600/80 dark:text-amber-500/80 mt-1 font-medium">Leads Calificados (MQLs)</span>
                <span className="mt-3 text-[10px] text-muted-foreground text-center flex flex-col">
                  <span>Interactuaron con emails/ads</span>
                  {nurtureData.headerKpis.costPerMql != null && (
                    <span className="mt-1 font-medium text-amber-600/70 dark:text-amber-500/70">
                      Costo p/MQL: {fmtMoney(nurtureData.headerKpis.costPerMql)}
                    </span>
                  )}
                </span>
              </div>
              <div className="flex flex-col items-center justify-center relative">
                <div className="w-16 h-16 rounded-full bg-gradient-to-br from-orange-400 to-amber-500 text-white flex items-center justify-center shadow-md border-4 border-background">
                  <span className="font-bold text-lg">{oppConvRate.toFixed(1)}%</span>
                </div>
                <span className="text-[10px] text-muted-foreground font-bold uppercase mt-3 text-center">Tasa Oportunidad</span>
              </div>
              <div className="bg-orange-950 dark:bg-orange-950/50 p-5 rounded-lg border border-orange-900 shadow-md flex flex-col items-center justify-center relative text-white">
                <span className="text-[10px] text-orange-300 font-bold uppercase mb-1">Listos para Comprar (SQL)</span>
                <span className="text-4xl font-black text-white">{formatNum(totalSqls)}</span>
                <span className="text-xs text-orange-200 mt-1 mb-3">Oportunidades (SQLs)</span>
                <span className="text-xs text-emerald-300 font-medium">
                  <Target className="w-3 h-3 mr-1 inline" /> Costo p/Oportunidad: {fmtMoney(costPerSql)}
                </span>
              </div>
            </div>
            
            {/* Bottleneck Alerts */}
            {activeBottlenecks.length > 0 && (
              <div className="flex flex-col gap-2 mb-4">
                {activeBottlenecks.map((bottleneck, idx) => (
                  <div key={idx} className="bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900 rounded-lg p-3 flex gap-3 text-red-900 dark:text-red-200 items-center shadow-sm">
                    <AlertTriangle className="w-5 h-5 text-red-500 flex-shrink-0" />
                    <div className="flex-1">
                      <p className="text-sm font-medium"><strong>Cuello de Botella Detectado:</strong> {bottleneck.metricLabel} está en {bottleneck.currentRate}%. {bottleneck.tip}</p>
                    </div>
                    <Button variant="outline" size="sm" className="bg-red-100 hover:bg-red-200 text-red-700 border-red-200 h-8">
                      Solucionar
                    </Button>
                  </div>
                ))}
              </div>
            )}

            {/* Banner Motivacional */}
            <div className="bg-gradient-to-r from-amber-50 to-orange-50 dark:from-amber-950/20 dark:to-orange-950/20 border border-amber-100 dark:border-amber-900/50 rounded-lg p-3 flex gap-3 text-amber-900 dark:text-amber-200 items-center shadow-sm">
              <Lightbulb className="w-5 h-5 text-amber-500 flex-shrink-0" />
              <p className="text-sm font-medium">
                <strong>Entiende tus números:</strong> <em>Nutrición</em> mide cuántos leads calentaste (MQLs) y <em>Oportunidad</em> cuántos de esos están a un paso de pagar o agendar (SQLs). Haz clic en los números para accionar.
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Detail Split Columns */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
        
        {/* COLUMNA NUTRICIÓN */}
        <div className="space-y-6">
          <div className="border-b border-border pb-2">
            <h3 className="font-semibold text-lg flex items-center text-foreground/90">
              <MailOpen className="w-5 h-5 mr-2 text-amber-500" /> Nutrición (MQLs)
            </h3>
            <p className="text-xs text-muted-foreground mt-1">Canales que educan y convencen al lead de que tú eres la solución.</p>
          </div>
          
          {/* Automatizaciones */}
          <div className="bg-card rounded-lg border border-border shadow-sm overflow-hidden">
            <div className="bg-muted/50 px-4 py-3 border-b border-border flex justify-between items-center">
              <span className="font-medium text-sm text-foreground/90 flex items-center"><Workflow className="w-4 h-4 text-amber-600 mr-2" /> Automatizaciones & Secuencias</span>
              <div className="flex gap-4 text-xs font-medium">
                <span className="text-muted-foreground">{formatNum(nurtureData.automation.totals.leads || 0)} MQLs</span>
              </div>
            </div>
            <div className="p-4 space-y-2">
              <div className="grid grid-cols-1 gap-2">
                {splitChannels(nurtureChannels).rows.map((c) => {
                  // email-nurture gets the full ChannelRow (4 metrics + sidebar)
                  if (c.slug === 'email-nurture') {
                    return (
                      <ChannelRow
                        key={c.slug}
                        channel={{ ...c, name: 'Email Marketing' }}
                        stageId="NUTRICION"
                        onMetricClick={onMetricClick}
                        onChannelClick={onChannelClick}
                      />
                    );
                  }
                  const isAgent = c.slug.includes('agent');
                  const metricName = isAgent ? 'responses' : 'leads';
                  const metricLabel = isAgent ? 'Leads Interactuando' : 'leads interactuaron';
                  return (
                    <NurtureChannelRow key={c.slug} channel={c} stageId="NUTRICION" defaultMetricName={metricName} defaultMetricLabel={metricLabel} baseColor="amber" />
                  );
                })}
              </div>
              {splitChannels(nurtureChannels).chips.length > 0 && (
                <div className="flex flex-wrap gap-2 pt-2 border-t border-border/30 mt-2">
                  {splitChannels(nurtureChannels).chips.map((ch: ChannelMetric) => (
                    <ChannelChip key={ch.slug} channel={ch} variant={ch.connected ? 'no-data' : 'disconnected'} onDisconnectedClick={onDisconnectedClick} onNoDataClick={onNoDataClick} />
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Retargeting */}
          <div className="bg-card rounded-lg border border-border shadow-sm overflow-hidden">
            <div className="bg-muted/50 px-4 py-3 border-b border-border flex justify-between items-center">
              <span className="font-medium text-sm text-foreground/90 flex items-center"><Repeat className="w-4 h-4 text-blue-600 mr-2" /> Retargeting Omnicanal</span>
              <div className="flex gap-4 text-xs font-medium">
                <span className="text-muted-foreground">{formatNum(nurtureData.retargeting.totals.leads || 0)} MQLs</span>
                <span className="text-red-500">{fmtMoney(nurtureData.retargeting.totals.spend || 0)}</span>
              </div>
            </div>
            <div className="p-4 space-y-2">
              <div className="grid grid-cols-1 gap-2">
                {splitChannels(retargetingChannels).rows.map((c) => {
                  const isMeta = c.slug.includes('meta') || c.slug.includes('fb') || c.slug.includes('ig');
                  const metricName = isMeta ? 'clicks' : 'leads';
                  const metricLabel = isMeta ? 'clicks' : 'leads re-enganchados';
                  return (
                    <NurtureChannelRow key={c.slug} channel={c} stageId="NUTRICION" defaultMetricName={metricName} defaultMetricLabel={metricLabel} baseColor="blue" />
                  );
                })}
              </div>
              {splitChannels(retargetingChannels).chips.length > 0 && (
                <div className="flex flex-wrap gap-2 pt-2 border-t border-border/30 mt-2">
                  {splitChannels(retargetingChannels).chips.map((ch: ChannelMetric) => (
                    <ChannelChip key={ch.slug} channel={ch} variant={ch.connected ? 'no-data' : 'disconnected'} onDisconnectedClick={onDisconnectedClick} onNoDataClick={onNoDataClick} />
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Canales Disponibles - Nutrición */}
          {availableNurtureChannels.length > 0 && (
            <div className="flex flex-wrap gap-2 pt-2">
              {availableNurtureChannels.map((c: ChannelMetric) => (
                <ChannelChip
                  key={c.slug}
                  channel={c}
                  variant="disconnected"
                  onDisconnectedClick={onDisconnectedClick}
                />
              ))}
            </div>
          )}

        </div>

        {/* COLUMNA OPORTUNIDAD */}
        <div className="space-y-6">
          <div className="border-b border-border pb-2">
            <h3 className="font-semibold text-lg flex items-center text-foreground/90">
              <Crosshair className="w-5 h-5 mr-2 text-orange-500" /> Oportunidad (SQLs)
            </h3>
            <p className="text-xs text-muted-foreground mt-1">Donde el lead demuestra clara intención de pagar o hablar contigo.</p>
          </div>

          {/* Calificación & Citas */}
          <div className="bg-card rounded-lg border border-border shadow-sm overflow-hidden border-l-4 border-l-orange-400 hover:border-l-orange-500 transition-colors">
            <div className="bg-orange-500/5 px-4 py-3 border-b border-border flex justify-between items-center">
              <span className="font-medium text-sm flex items-center text-foreground/90"><CalendarCheck className="w-4 h-4 text-orange-600 mr-2" /> Calificación & Citas</span>
              <div className="flex gap-4 text-xs font-medium">
                <span className="text-orange-600 font-bold">{formatNum(oppData.qualification.totals.sqls || 0)} SQLs</span>
              </div>
            </div>
            <div className="p-4 space-y-2">
              <div className="grid grid-cols-1 gap-2">
                {splitChannels(oppQualificationChannels).rows.map((c) => (
                  <NurtureChannelRow key={c.slug} channel={c} stageId="OPORTUNIDAD" defaultMetricName="sqls" defaultMetricLabel="formularios / citas" baseColor="orange" />
                ))}
              </div>
              {splitChannels(oppQualificationChannels).chips.length > 0 && (
                <div className="flex flex-wrap gap-2 pt-2 border-t border-border/30 mt-2">
                  {splitChannels(oppQualificationChannels).chips.map((ch: ChannelMetric) => (
                    <ChannelChip key={ch.slug} channel={ch} variant={ch.connected ? 'no-data' : 'disconnected'} onDisconnectedClick={onDisconnectedClick} onNoDataClick={onNoDataClick} />
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Checkouts & Pagos */}
          <div className="bg-card rounded-lg border border-border shadow-sm overflow-hidden border-l-4 border-l-emerald-500 hover:border-l-emerald-600 transition-colors">
            <div className="bg-emerald-500/5 px-4 py-3 border-b border-border flex justify-between items-center">
              <span className="font-medium text-sm flex items-center text-foreground/90"><ShoppingCart className="w-4 h-4 text-emerald-600 mr-2" /> Checkouts & Pagos</span>
              <div className="flex gap-4 text-xs font-medium">
                <span className="text-emerald-600 font-bold">{formatNum((oppData.checkout.totals.sqls || 0) + (oppData.paymentLinks.totals.sqls || 0))} SQLs</span>
              </div>
            </div>
            <div className="p-4 space-y-2">
              <div className="grid grid-cols-1 gap-2">
                {splitChannels(oppCheckoutChannels).rows.map((c) => (
                  <NurtureChannelRow key={c.slug} channel={c} stageId="OPORTUNIDAD" defaultMetricName="sqls" defaultMetricLabel="iniciaron pago" baseColor="emerald" />
                ))}
              </div>
              {splitChannels(oppCheckoutChannels).chips.length > 0 && (
                <div className="flex flex-wrap gap-2 pt-2 border-t border-border/30 mt-2">
                  {splitChannels(oppCheckoutChannels).chips.map((ch: ChannelMetric) => (
                    <ChannelChip key={ch.slug} channel={ch} variant={ch.connected ? 'no-data' : 'disconnected'} onDisconnectedClick={onDisconnectedClick} onNoDataClick={onNoDataClick} />
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Canales Disponibles - Oportunidad */}
          {availableOppChannels.length > 0 && (
            <div className="flex flex-wrap gap-2 pt-2">
              {availableOppChannels.map((c: ChannelMetric) => (
                <ChannelChip
                  key={c.slug}
                  channel={c}
                  variant="disconnected"
                  onDisconnectedClick={onDisconnectedClick}
                />
              ))}
            </div>
          )}

        </div>

      </div>
    </div>
  );
});
