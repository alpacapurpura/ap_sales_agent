'use client';

import React from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { Zap, Rocket, Briefcase, Layers, Package } from 'lucide-react';
import type { RevenueGroupData, OfferSaleData, MetricClickData } from '../../../types/metrics';
import { formatMoney } from '@/lib/format-money';

interface OfferLadderProps {
  adquisicion: RevenueGroupData;
  expansion: RevenueGroupData;
  onMetricClick?: (metric: MetricClickData) => void;
}

function formatCompactMoney(amount: number, currency: string) {
  return formatMoney(amount, currency, { compact: true });
}

function getOfferLabel(offerType: string, pricingType: string) {
  // Map archetype values to labels
  const archetypeMap: Record<string, string> = {
    'producto': 'Producto',
    'programa': 'Programa',
    'servicio': 'Servicio',
    'membresia': 'Membresía',
    'experiencia': 'Experiencia',
  };

  const pricingMap: Record<string, string> = {
    'one_time': 'Pago Único',
    'subscription': 'Suscripción',
    'payment_plan': 'Cuotas',
  };

  const t = archetypeMap[offerType] || offerType;
  const p = pricingMap[pricingType] || pricingType;

  return `${t} • ${p}`;
}

function OfferCard({ 
  offer, 
  currency, 
  colorTheme,
  onMetricClick 
}: { 
  offer: OfferSaleData; 
  currency: string; 
  colorTheme: 'blue' | 'indigo' | 'amber';
  onMetricClick?: (metric: MetricClickData) => void;
}) {
  const sources = Object.entries(offer.sourceBreakdown || {});
  
  // Theme classes
  const themeClasses = {
    blue: {
      wrapper: 'hover:bg-blue-50/50 hover:border-blue-300 dark:hover:bg-blue-900/10 dark:hover:border-blue-700',
      bar: 'bg-slate-200 group-hover:bg-blue-400 dark:bg-slate-700',
    },
    indigo: {
      wrapper: 'hover:bg-indigo-50/50 hover:border-indigo-300 dark:hover:bg-indigo-900/10 dark:hover:border-indigo-700',
      bar: 'bg-slate-200 group-hover:bg-indigo-400 dark:bg-slate-700',
    },
    amber: {
      wrapper: 'hover:bg-amber-50/50 hover:border-amber-300 dark:hover:bg-amber-900/10 dark:hover:border-amber-700',
      bar: 'bg-slate-200 group-hover:bg-amber-400 dark:bg-slate-700',
    }
  };

  const theme = themeClasses[colorTheme];

  return (
    <div 
      className={`group relative overflow-hidden border border-slate-100 dark:border-slate-800 rounded-md p-3 bg-white dark:bg-slate-900 transition-all cursor-pointer shadow-sm hover:shadow ${theme.wrapper}`}
      onClick={() => {
        if (onMetricClick) {
          onMetricClick({
            stageId: 'VENTAS',
            channelSlug: offer.offerId,
            metricName: 'offer_detail',
            currentValue: offer.totalRevenue,
            currency: currency,
            extraData: { salesCount: offer.salesCount },
          });
        }
      }}
    >
      <div className={`absolute top-0 left-0 w-1 h-full transition-colors ${theme.bar}`}></div>
      <div className="flex justify-between items-start">
        <div className="pl-2">
          <h5 className="font-semibold text-sm text-slate-800 dark:text-slate-200 leading-tight truncate max-w-[140px] sm:max-w-[160px]" title={offer.publicName}>
            {offer.publicName}
          </h5>
          <p className="text-[10px] text-slate-400 dark:text-slate-500 uppercase tracking-wider mt-1">
            {getOfferLabel(offer.offerType, offer.pricingType)}
          </p>
          
          <div className="mt-2 flex flex-wrap items-center gap-1.5">
            <span className="text-[9px] font-semibold text-slate-400 dark:text-slate-500 uppercase">Vía:</span>
            {sources.length > 0 ? (
              sources.map(([src, count]) => {
                let badgeClass = 'bg-slate-100 text-slate-700 border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700';
                let title = 'Cierre manual o llamada de ventas';
                let initial = 'M';
                
                if (src === 'SHOPIFY') {
                  badgeClass = 'bg-blue-50 text-blue-700 border-blue-100 dark:bg-blue-900/30 dark:text-blue-300 dark:border-blue-800';
                  title = 'Cierre automático procesado por Shopify';
                  initial = 'S';
                } else if (src === 'AGENT') {
                  badgeClass = 'bg-purple-50 text-purple-700 border-purple-100 dark:bg-purple-900/30 dark:text-purple-300 dark:border-purple-800';
                  title = 'Cierre conversacional gestionado por el AI Agent';
                  initial = 'A';
                }
                
                return (
                  <span 
                    key={src} 
                    className={`inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-medium border cursor-help ${badgeClass}`}
                    title={title}
                  >
                    {initial}: {count}
                  </span>
                );
              })
            ) : (
              <span className="text-[9px] text-slate-400 dark:text-slate-500">Sin datos</span>
            )}
          </div>
        </div>
        <div className="text-right shrink-0">
          <span className="text-sm font-bold text-slate-800 dark:text-slate-200">
            {formatCompactMoney(offer.totalRevenue, currency)}
          </span>
          <p className="text-[10px] text-slate-500 dark:text-slate-400 mt-1">
            {offer.salesCount} {offer.salesCount === 1 ? 'venta' : 'ventas'}
          </p>
        </div>
      </div>
    </div>
  );
}

function EmptyTierCta({ tenantId }: { tenantId: string }) {
  return (
    <div className="h-full flex flex-col items-center justify-center py-6 text-center">
      <Package className="w-5 h-5 text-muted-foreground/40 mb-2" />
      <span className="text-xs text-muted-foreground italic">Sin ofertas configuradas</span>
      <Link
        href={`/${tenantId}/offer-studio`}
        className="mt-2 text-xs font-medium text-amber-700 dark:text-amber-400 hover:underline"
      >
        Ir a Offer Studio &rarr;
      </Link>
    </div>
  );
}

export function OfferLadder({ adquisicion, expansion, onMetricClick }: OfferLadderProps) {
  const params = useParams();
  const tenantId = (params?.tenantId as string) || '';

  // Extract all offers from Adquisicion and Expansion
  const getAllOffersByTier = (tierKey: string) => {
    const adqTier = adquisicion.tiers.find(t => t.tierKey === tierKey);
    const expTier = expansion.tiers.find(t => t.tierKey === tierKey);
    
    const adqOffers = adqTier?.offers || [];
    const expOffers = expTier?.offers || [];
    
    // Merge offers with the same ID, or just concat them? 
    // Usually they are distinct or we can just display them together.
    // In our backend, they should be distinct by offerId, but an offer could have both acquisition and expansion revenue.
    // For now, we concat them. If there are duplicates, we might want to group them, but the backend separates by groupKey.
    // Actually, backend returns them separated. Let's combine them by offerId.
    const combinedOffers = new Map<string, OfferSaleData>();
    
    [...adqOffers, ...expOffers].forEach(offer => {
      if (combinedOffers.has(offer.offerId)) {
        const existing = combinedOffers.get(offer.offerId)!;
        existing.totalRevenue += offer.totalRevenue;
        existing.salesCount += offer.salesCount;
        if (offer.usdRevenue) existing.usdRevenue = (existing.usdRevenue || 0) + offer.usdRevenue;
        // Merge source breakdown
        Object.entries(offer.sourceBreakdown || {}).forEach(([src, count]) => {
          existing.sourceBreakdown[src] = (existing.sourceBreakdown[src] || 0) + count;
        });
      } else {
        // Deep copy to avoid mutating original props
        combinedOffers.set(offer.offerId, JSON.parse(JSON.stringify(offer)));
      }
    });
    
    return Array.from(combinedOffers.values()).sort((a, b) => b.totalRevenue - a.totalRevenue);
  };

  const activacionOffers = getAllOffersByTier('activacion');
  const transformacionOffers = getAllOffersByTier('transformacion');
  const maximizacionOffers = getAllOffersByTier('maximizacion');
  const corporativoOffers = getAllOffersByTier('corporativo');

  const currency = adquisicion.currency;

  return (
    <div className="pt-4 space-y-6">
      <div className="flex items-end justify-between border-b border-border pb-2">
        <div>
          <h3 className="font-semibold text-xl flex items-center text-foreground">
            <Layers className="w-5 h-5 mr-2 text-emerald-600 dark:text-emerald-500" /> Desglose por Offer Ladder
          </h3>
          <p className="text-sm text-muted-foreground mt-1">
            Ingresos organizados por la jerarquía de tus productos (Alineado con Offer Studio).
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

        {/* Col 1: Activacion */}
        <div className="bg-card rounded-xl border border-border p-4 shadow-sm flex flex-col">
          <div className="mb-4 pb-3 border-b border-border flex items-center gap-2">
            <div className="p-1.5 rounded bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400">
              <Zap className="w-4 h-4" />
            </div>
            <h4 className="font-bold text-foreground text-sm">Activacion</h4>
          </div>

          <div className="space-y-3 flex-1">
            {activacionOffers.length > 0 ? (
              activacionOffers.map(offer => (
                <OfferCard
                  key={offer.offerId}
                  offer={offer}
                  currency={currency}
                  colorTheme="blue"
                  onMetricClick={onMetricClick}
                />
              ))
            ) : (
              <EmptyTierCta tenantId={tenantId} />
            )}
          </div>
        </div>

        {/* Col 2: Transformacion */}
        <div className="bg-card rounded-xl border border-indigo-200 dark:border-indigo-900/50 p-4 shadow-sm flex flex-col relative">
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-indigo-400 to-purple-400 rounded-t-xl"></div>
          <div className="mb-4 pb-3 border-b border-border flex items-center gap-2">
            <div className="p-1.5 rounded bg-indigo-50 text-indigo-600 dark:bg-indigo-900/30 dark:text-indigo-400">
              <Rocket className="w-4 h-4" />
            </div>
            <h4 className="font-bold text-foreground text-sm">Transformacion</h4>
          </div>

          <div className="space-y-3 flex-1">
            {transformacionOffers.length > 0 ? (
              transformacionOffers.map(offer => (
                <OfferCard
                  key={offer.offerId}
                  offer={offer}
                  currency={currency}
                  colorTheme="indigo"
                  onMetricClick={onMetricClick}
                />
              ))
            ) : (
              <EmptyTierCta tenantId={tenantId} />
            )}
          </div>
        </div>

        {/* Col 3: Maximizacion */}
        <div className="bg-card rounded-xl border border-border p-4 shadow-sm flex flex-col">
          <div className="mb-4 pb-3 border-b border-border flex items-center gap-2">
            <div className="p-1.5 rounded bg-amber-50 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400">
              <Briefcase className="w-4 h-4" />
            </div>
            <h4 className="font-bold text-foreground text-sm">Maximizacion</h4>
          </div>

          <div className="space-y-3 flex-1">
            {maximizacionOffers.length > 0 ? (
              maximizacionOffers.map(offer => (
                <OfferCard
                  key={offer.offerId}
                  offer={offer}
                  currency={currency}
                  colorTheme="amber"
                  onMetricClick={onMetricClick}
                />
              ))
            ) : (
              <EmptyTierCta tenantId={tenantId} />
            )}
          </div>
        </div>
      </div>

      {/* Fila Inferior: Corporativo */}
      <div className="mt-6 bg-slate-800 dark:bg-slate-900 rounded-xl p-4 flex flex-col md:flex-row gap-6 items-center justify-between text-white shadow-md border border-slate-700">
        <div className="flex items-center gap-4 md:w-1/3">
          <div className="p-2.5 bg-emerald-500/20 rounded-full text-emerald-400 flex-shrink-0">
            <Briefcase className="w-6 h-6" />
          </div>
          <div>
            <h4 className="font-bold text-lg leading-tight text-white">Corporativo</h4>
            <p className="text-xs text-slate-400 mt-0.5">Ventas B2B y grandes contratos</p>
          </div>
        </div>

        <div className="flex-1 flex flex-col gap-3 w-full md:w-auto px-0 md:px-6 md:border-x md:border-slate-700">
          {corporativoOffers.length > 0 ? (
            corporativoOffers.map(offer => (
              <div
                key={offer.offerId}
                className="bg-slate-700/50 dark:bg-slate-800/80 rounded p-3 flex justify-between items-center hover:bg-slate-700/80 transition-colors cursor-pointer"
                onClick={() => {
                  if (onMetricClick) {
                    onMetricClick({
                      stageId: 'VENTAS',
                      channelSlug: offer.offerId,
                      metricName: 'offer_detail',
                      currentValue: offer.totalRevenue,
                      currency: currency,
                      extraData: { salesCount: offer.salesCount },
                    });
                  }
                }}
              >
                <div>
                  <span className="text-sm font-medium text-slate-200">{offer.publicName}</span>
                  <p className="text-[10px] text-slate-400 mt-1">
                    {Object.entries(offer.sourceBreakdown || {}).map(([src, count]) => `${src}: ${count}`).join(', ') || 'Sin datos'}
                  </p>
                </div>
                <span className="font-bold text-emerald-400">{formatMoney(offer.totalRevenue, currency, { fractionDigits: 0 })}</span>
              </div>
            ))
          ) : (
            <div className="text-center py-2">
              <span className="text-xs text-slate-400 italic">Sin servicios corporativos</span>
              <Link
                href={`/${tenantId}/offer-studio`}
                className="block mt-1 text-xs font-medium text-amber-400 hover:underline"
              >
                Ir a Offer Studio &rarr;
              </Link>
            </div>
          )}
        </div>

        <div className="text-right md:w-1/4">
          <div className="text-2xl font-black text-emerald-400">
            {formatCompactMoney(corporativoOffers.reduce((s, o) => s + o.totalRevenue, 0), currency)}
          </div>
          <p className="text-xs text-slate-400 mt-1">{corporativoOffers.reduce((s, o) => s + o.salesCount, 0)} ventas</p>
        </div>
      </div>

    </div>
  );
}
