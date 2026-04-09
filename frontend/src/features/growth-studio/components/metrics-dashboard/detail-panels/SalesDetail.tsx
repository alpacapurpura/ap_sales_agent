'use client';

import React, { useState, useMemo, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Banknote, Calendar, Crosshair, Download, Loader2, CheckCircle2, Settings, ShoppingCart, AlertTriangle } from 'lucide-react';
import { ActionPanel } from '../action-widgets/ActionPanel';
import { useSalesDetail } from '../../../hooks/useStageDetail';
import { MiniFunnel } from '../channel-widgets/MiniFunnel';
import { OfferLadder } from '../offer-widgets/OfferLadder';
import { SourceProducts } from '../offer-widgets/SourceProducts';
import { BottleneckBanner } from './BottleneckBanner';
import DetailSkeleton from '../ui/DetailSkeleton';
import DetailEmpty from '../ui/DetailEmpty';
import DetailError from '../ui/DetailError';
import { formatLastUpdated, formatDualCurrency } from '../utils/format';
import { useTenantLocale } from '@/features/tenant/context/tenant-locale-context';
import { useInitialLoad } from '../../../hooks/useInitialLoad';
import { useQueryClient } from '@tanstack/react-query';
import type { MetricClickData, StageSummary } from '../../../types/metrics';

const VENTAS_STAGE: StageSummary = {
  id: 'VENTAS',
  order: 4,
  label: 'Ventas',
  description: 'Revenue y clientes nuevos por oferta',
  mainKpi: { label: 'revenue', value: 0, unit: '$' },
  secondaryKpi: { label: 'nuevos clientes', value: 0 },
  hasDetail: true,
};

interface SalesDetailProps {
  onMetricClick?: (metric: MetricClickData) => void;
}

export const SalesDetail = React.memo(function SalesDetail({ onMetricClick }: SalesDetailProps) {
  const { timezone } = useTenantLocale();
  const { data, isLoading, error, refetch } = useSalesDetail();
  const [isPanelOpen, setIsPanelOpen] = useState(false);
  const queryClient = useQueryClient();

  // Shopify sync button
  const { trigger: triggerShopify, isLoading: isLoadingShopify, result: shopifyResult, error: shopifyError, reset: resetShopify } = useInitialLoad();
  const handleShopifySync = useCallback(() => {
    if (shopifyError) resetShopify();
    triggerShopify({ provider: 'shopify', days: 30 }, {
      onSuccess: () => {
        void queryClient.invalidateQueries({ queryKey: ['sales-detail'] });
      },
    });
  }, [triggerShopify, queryClient, shopifyError, resetShopify]);

  const oppToSalesConvRate = useMemo(
    () => {
      if (!data) return 0;
      return data.miniFunnel?.conversionRate || (data.headerKpis.newCustomers > 0 && data.miniFunnel.sourceValue > 0 ? (data.headerKpis.newCustomers / data.miniFunnel.sourceValue) * 100 : 0);
    },
    [data]
  );

  const extraData = useMemo<Record<string, number>>(() => {
    if (!data) return {} as Record<string, number>;
    const { headerKpis: kpis, miniFunnel: mf } = data;
    return {
      totalRevenue: kpis.totalRevenue,
      newCustomers: kpis.newCustomers,
      netSales: kpis.netSales ?? 0,
      totalDiscounts: kpis.totalDiscounts ?? 0,
      totalTax: kpis.totalTax ?? 0,
      refundCount: kpis.refundCount ?? 0,
      refundAmount: kpis.refundAmount ?? 0,
      shippingRevenue: kpis.shippingRevenue ?? 0,
      repeatCustomers: kpis.repeatCustomers ?? 0,
      discountUsageCount: kpis.discountUsageCount ?? 0,
      cac: kpis.cac ?? 0,
      conversionRate: oppToSalesConvRate,
      sqls: mf.sourceValue,
    };
  }, [data, oppToSalesConvRate]);

  const handleKpiClick = useCallback((metricName: string, currentValue: number) => {
    if (!data) return;
    onMetricClick?.({
      stageId: 'VENTAS',
      channelSlug: 'shopify',
      metricName,
      currentValue,
      currency: data.headerKpis.currency,
      extraData,
    });
  }, [onMetricClick, data, extraData]);

  if (isLoading) {
    return (
      <DetailSkeleton isLoading>
        <></>
      </DetailSkeleton>
    );
  }

  if (error) {
    return (
      <DetailError
        error={error instanceof Error ? error : new Error('Error desconocido')}
        onRetry={() => { void refetch(); }}
        lastData={data}
      />
    );
  }

  if (!data) {
    return <DetailEmpty stage={VENTAS_STAGE} />;
  }

  const { headerKpis, miniFunnel, adquisicion, expansion, bottlenecks } = data;

  return (
    <div className="space-y-12 animate-fade-in bg-background p-6 rounded-2xl text-foreground border border-border">

      {/* Title & Actions Row */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground flex items-center gap-2">
            Ventas
            <span className="px-2 py-0.5 mt-1 rounded-full bg-emerald-100 dark:bg-emerald-500/20 text-emerald-700 dark:text-emerald-400 text-xs font-medium tracking-wide">ETAPA 4</span>
          </h1>
          <p className="text-muted-foreground text-sm mt-1">Ingresos generados (Revenue), clientes nuevos y costo de adquisición por oferta.</p>
        </div>
        <div className="flex items-center gap-3">
          <p className="text-xs text-muted-foreground italic mr-2">
            Actualizado: {data.lastUpdated ? formatLastUpdated(data.lastUpdated, timezone) : 'Hoy'}
          </p>
          <Button variant={shopifyError ? 'destructive' : 'outline'} onClick={handleShopifySync} disabled={isLoadingShopify}>
            {isLoadingShopify ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : shopifyError ? (
              <AlertTriangle className="mr-2 h-4 w-4" />
            ) : shopifyResult ? (
              shopifyResult.loaded_days > 0 ? <CheckCircle2 className="mr-2 h-4 w-4 text-emerald-500" /> :
              shopifyResult.skipped_days > 0 ? <CheckCircle2 className="mr-2 h-4 w-4 text-muted-foreground" /> :
              <AlertTriangle className="mr-2 h-4 w-4 text-amber-500" />
            ) : (
              <Download className="mr-2 h-4 w-4" />
            )}
            {isLoadingShopify
              ? 'Cargando...'
              : shopifyError
                ? (shopifyError.message.includes('Disponible en') ? shopifyError.message : 'Error — Reintentar')
                : shopifyResult
                  ? shopifyResult.loaded_days > 0
                    ? `Shopify OK (${shopifyResult.loaded_days} dias)`
                    : shopifyResult.skipped_days > 0
                      ? 'Shopify (ya cargado)'
                      : 'Shopify (sin datos)'
                  : 'Datos Shopify'}
          </Button>
          <Button variant="outline" onClick={() => setIsPanelOpen(true)}>
            <Calendar className="mr-2 h-4 w-4" /> Últimos 30 días
          </Button>
          <Button className="bg-emerald-600 hover:bg-emerald-700 text-white" onClick={() => setIsPanelOpen(true)}>
            <Settings className="mr-2 h-4 w-4" /> Gestionar Etapa
          </Button>
        </div>
      </div>

      <ActionPanel isOpen={isPanelOpen} onClose={() => setIsPanelOpen(false)} />

      {/* Global Performance Header (Funnel visual) */}
      <div className="bg-card rounded-xl p-6 shadow-sm border border-border relative overflow-hidden">
        <h2 className="text-lg font-semibold mb-6 flex items-center text-foreground/90">
          <Banknote className="w-5 h-5 mr-2 text-emerald-600 dark:text-emerald-500" /> Rendimiento de Ventas
        </h2>

        <div className="relative mb-2">
          {/* Horizontal Lines (Background Layer) */}
          <div className="hidden md:block absolute w-[10%] h-[2px] bg-gradient-to-r from-slate-200 to-slate-400 dark:from-slate-800 dark:to-slate-600 top-[40%] left-[20%] z-0"></div>
          <div className="hidden md:block absolute w-[10%] h-[2px] bg-gradient-to-r from-emerald-200 to-emerald-400 dark:from-emerald-900 dark:to-emerald-700 top-[40%] left-[45%] z-0"></div>
          <div className="hidden md:block absolute w-[10%] h-[2px] bg-gradient-to-r from-emerald-400 to-emerald-600 dark:from-emerald-700 dark:to-emerald-500 top-[40%] left-[70%] z-0"></div>

          {/* Metrics Row (Foreground Layer) */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 relative z-10 w-full">
            {/* Bloque 1: Pipeline Inicial */}
            <button
              type="button"
              className="bg-background p-5 rounded-lg border border-border shadow-sm flex flex-col items-center justify-center relative text-center hover:border-emerald-500/40 hover:shadow-md transition-all cursor-pointer"
              onClick={() => handleKpiClick('pipeline', miniFunnel.sourceValue)}
            >
              <span className="text-[10px] text-muted-foreground font-bold uppercase mb-1">Oportunidades (SQLs)</span>
              <span className="text-3xl font-black text-foreground">{miniFunnel.sourceValue.toLocaleString('es-ES')}</span>
              <span className="text-xs text-muted-foreground mt-1">Leads Listos para Comprar</span>
            </button>

            {/* Bloque 2: Nuevos Clientes */}
            <button
              type="button"
              className="bg-background p-5 rounded-lg border border-emerald-500/20 shadow-sm flex flex-col items-center justify-center relative text-center ring-1 ring-emerald-500/10 hover:ring-emerald-500/30 hover:shadow-md transition-all cursor-pointer"
              onClick={() => handleKpiClick('customers', headerKpis.newCustomers)}
            >
              <span className="text-[10px] text-emerald-600 dark:text-emerald-500 font-bold uppercase mb-1">Nuevos Clientes</span>
              <span className="text-4xl font-black text-emerald-600 dark:text-emerald-500">{headerKpis.newCustomers.toLocaleString('es-ES')}</span>
              <span className="text-xs text-emerald-600/80 dark:text-emerald-500/80 mt-1 font-medium">Conversiones Exitosas</span>
              <div className="mt-3 text-[10px] text-muted-foreground font-medium flex items-center justify-center">
                <Crosshair className="w-3 h-3 mr-1 text-emerald-600 dark:text-emerald-500" />
                <span>
                  CAC Promedio: {headerKpis.cac != null ? new Intl.NumberFormat('es-MX', { style: 'currency', currency: headerKpis.currency, minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(headerKpis.cac) : '--'}
                </span>
              </div>
            </button>

            {/* Bloque 3: Tasa de Conversión */}
            <div className="flex flex-col items-center justify-center relative">
              <div className="w-16 h-16 rounded-full bg-gradient-to-br from-emerald-400 to-emerald-500 dark:from-emerald-600 dark:to-emerald-500 text-white flex items-center justify-center shadow-md border-4 border-background">
                <span className="font-bold text-lg">{oppToSalesConvRate.toFixed(1)}%</span>
              </div>
              <span className="text-[10px] text-muted-foreground font-bold uppercase mt-3 text-center">Tasa de Cierre</span>
            </div>

            {/* Bloque 4: Revenue Total */}
            <button
              type="button"
              className="bg-emerald-950 dark:bg-emerald-950/50 p-5 rounded-lg border border-emerald-900 shadow-md flex flex-col items-center justify-center relative text-center text-white hover:border-emerald-700 hover:shadow-lg transition-all cursor-pointer"
              onClick={() => handleKpiClick('revenue', headerKpis.totalRevenue)}
            >
              <span className="text-[10px] text-emerald-300 font-bold uppercase mb-1">Revenue Total</span>
              <span className="text-4xl font-black text-white">{formatDualCurrency(headerKpis.totalRevenue, headerKpis.currency, headerKpis.totalRevenueUsd).replace(/ \(.+\)/, '')}</span>
              <span className="text-xs text-emerald-200 mt-1">Ingresos Generados</span>
              {headerKpis.totalRevenueUsd && headerKpis.currency !== 'USD' && (
                <div className="mt-3 text-xs font-medium text-emerald-300">
                  (~{new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(headerKpis.totalRevenueUsd)} USD)
                </div>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Shopify Stats Breakdown (only when Shopify data exists) */}
      {headerKpis.shopifyOrderCount > 0 && (
        <div className="bg-card rounded-xl p-6 shadow-sm border border-border">
          <h2 className="text-lg font-semibold mb-4 flex items-center text-foreground/90">
            <ShoppingCart className="w-5 h-5 mr-2 text-emerald-600 dark:text-emerald-500" />
            Detalle Shopify
          </h2>

          {/* Primary KPI cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <div className="bg-background p-4 rounded-lg border border-border text-center">
              <span className="text-[10px] text-muted-foreground font-bold uppercase">Revenue</span>
              <p className="text-2xl font-bold text-foreground mt-1">
                {new Intl.NumberFormat('es-MX', { style: 'currency', currency: headerKpis.shopifyCurrency, minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(headerKpis.shopifyRevenue)}
              </p>
            </div>
            <div className="bg-background p-4 rounded-lg border border-border text-center">
              <span className="text-[10px] text-muted-foreground font-bold uppercase">Pedidos</span>
              <p className="text-2xl font-bold text-foreground mt-1">{headerKpis.shopifyOrderCount.toLocaleString('es-ES')}</p>
            </div>
            <div className="bg-background p-4 rounded-lg border border-border text-center">
              <span className="text-[10px] text-muted-foreground font-bold uppercase">Ticket Promedio</span>
              <p className="text-2xl font-bold text-foreground mt-1">
                {new Intl.NumberFormat('es-MX', { style: 'currency', currency: headerKpis.shopifyCurrency, minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(headerKpis.shopifyAvgOrderValue)}
              </p>
            </div>
            <div className="bg-background p-4 rounded-lg border border-border text-center">
              <span className="text-[10px] text-muted-foreground font-bold uppercase">Ventas Netas</span>
              <p className="text-2xl font-bold text-foreground mt-1">
                {new Intl.NumberFormat('es-MX', { style: 'currency', currency: headerKpis.shopifyCurrency, minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(headerKpis.netSales)}
              </p>
            </div>
          </div>

          {/* Secondary detail rows */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3 text-sm">
            <div className="flex flex-col items-center p-2 rounded-md bg-muted/50">
              <span className="text-[10px] text-muted-foreground font-medium uppercase">Descuentos</span>
              <span className="font-semibold text-foreground">
                {new Intl.NumberFormat('es-MX', { style: 'currency', currency: headerKpis.shopifyCurrency, minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(headerKpis.totalDiscounts)}
              </span>
            </div>
            <div className="flex flex-col items-center p-2 rounded-md bg-muted/50">
              <span className="text-[10px] text-muted-foreground font-medium uppercase">Impuestos</span>
              <span className="font-semibold text-foreground">
                {new Intl.NumberFormat('es-MX', { style: 'currency', currency: headerKpis.shopifyCurrency, minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(headerKpis.totalTax)}
              </span>
            </div>
            <div className="flex flex-col items-center p-2 rounded-md bg-muted/50">
              <span className="text-[10px] text-muted-foreground font-medium uppercase">Envios</span>
              <span className="font-semibold text-foreground">
                {new Intl.NumberFormat('es-MX', { style: 'currency', currency: headerKpis.shopifyCurrency, minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(headerKpis.shippingRevenue)}
              </span>
            </div>
            <div className="flex flex-col items-center p-2 rounded-md bg-muted/50">
              <span className="text-[10px] text-muted-foreground font-medium uppercase">Reembolsos</span>
              <span className="font-semibold text-foreground">
                {headerKpis.refundCount} ({new Intl.NumberFormat('es-MX', { style: 'currency', currency: headerKpis.shopifyCurrency, minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(headerKpis.refundAmount)})
              </span>
            </div>
            <div className="flex flex-col items-center p-2 rounded-md bg-muted/50">
              <span className="text-[10px] text-muted-foreground font-medium uppercase">Clientes Recurrentes</span>
              <span className="font-semibold text-foreground">{headerKpis.repeatCustomers}</span>
            </div>
          </div>
        </div>
      )}

      {/* Bottleneck Banners */}
      {bottlenecks.length > 0 && (
        <div className="space-y-2">
          {bottlenecks.map((b) => (
            <BottleneckBanner key={`${b.type}-${b.metricLabel}`} bottleneck={b} />
          ))}
        </div>
      )}

      {/* Source Products (Shopify) — mapped + unmapped with inline association */}
      <SourceProducts source="shopify" />

      {/* Offer Ladder — always rendered, shows CTA per empty column */}
      <OfferLadder
        adquisicion={adquisicion}
        expansion={expansion}
        onMetricClick={onMetricClick}
      />
    </div>
  );
});
