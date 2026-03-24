import React from 'react';
import { Zap, Rocket, Briefcase, RefreshCw, Layers } from 'lucide-react';
import type { RevenueGroupData, OfferSaleData, MetricClickData } from '../../../types/metrics';

interface OfferLadderProps {
  adquisicion: RevenueGroupData;
  expansion: RevenueGroupData;
  onMetricClick?: (metric: MetricClickData) => void;
}

function formatMoney(amount: number, currency: string) {
  return new Intl.NumberFormat('es-MX', {
    style: 'currency',
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
}

function formatCompactMoney(amount: number, currency: string) {
  return new Intl.NumberFormat('es-MX', {
    style: 'currency',
    currency,
    notation: 'compact',
    maximumFractionDigits: 1,
  }).format(amount);
}

function getOfferTypeLabel(offerType: string, pricingType: string) {
  const typeMap: Record<string, string> = {
    'FREE_RESOURCE': 'Lead Magnet',
    'TRIPWIRE': 'Tripwire',
    'SELF_PACED_COURSE': 'Curso',
    'COHORT_PROGRAM': 'Programa Grupal',
    'HYBRID_MENTORSHIP': 'Mentoría Híbrida',
    'ONE_ON_ONE_PRIVATE_MENTORING': '1 a 1',
    'PRODUCTIZED_SERVICE': 'Servicio',
    'DONE_FOR_YOU_SERVICE': 'DFY',
    'CONSULTING_RETAINER': 'Retainer',
    'MASTERMIND_NETWORK': 'Mastermind',
    'IN_PERSON_RETREAT': 'Retiro',
    'CORPORATE_WORKSHOP': 'Workshop Corp',
    'CORPORATE_CONSULTING': 'Consultoría Corp',
    'COMMUNITY_MEMBERSHIP': 'Membresía',
    'SOFTWARE_AS_A_SERVICE': 'SaaS',
    'PHYSICAL_PRODUCT': 'Producto Físico',
  };
  
  const pricingMap: Record<string, string> = {
    'one_time': 'Pago Único',
    'subscription': 'Suscripción',
    'payment_plan': 'Cuotas',
  };

  const t = typeMap[offerType] || offerType;
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
            metricName: 'revenue',
            currentValue: offer.totalRevenue,
            currency: currency,
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
            {getOfferTypeLabel(offer.offerType, offer.pricingType)}
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

export function OfferLadder({ adquisicion, expansion, onMetricClick }: OfferLadderProps) {
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

  const lowTicketOffers = getAllOffersByTier('low_ticket');
  const midTicketOffers = getAllOffersByTier('mid_ticket');
  const highTicketOffers = getAllOffersByTier('high_ticket');
  const recurrenteOffers = getAllOffersByTier('recurrente');

  // Calculate total MRR
  const totalMrr = recurrenteOffers.reduce((sum, offer) => sum + offer.totalRevenue, 0);
  const totalMrrSubs = recurrenteOffers.reduce((sum, offer) => sum + offer.salesCount, 0);
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
        
        {/* Col 1: Iniciación (DIY) */}
        <div className="bg-card rounded-xl border border-border p-4 shadow-sm flex flex-col">
          <div className="mb-4 pb-3 border-b border-border flex items-center gap-2">
            <div className="p-1.5 rounded bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400">
              <Zap className="w-4 h-4" />
            </div>
            <h4 className="font-bold text-foreground text-sm">Iniciación (DIY)</h4>
          </div>
          
          <div className="space-y-3 flex-1">
            {lowTicketOffers.length > 0 ? (
              lowTicketOffers.map(offer => (
                <OfferCard 
                  key={offer.offerId} 
                  offer={offer} 
                  currency={currency} 
                  colorTheme="blue"
                  onMetricClick={onMetricClick} 
                />
              ))
            ) : (
              <div className="h-full flex items-center justify-center py-6">
                <span className="text-xs text-muted-foreground italic">Sin ventas en este nivel</span>
              </div>
            )}
          </div>
        </div>

        {/* Col 2: Transformación (DWY) */}
        <div className="bg-card rounded-xl border border-indigo-200 dark:border-indigo-900/50 p-4 shadow-sm flex flex-col relative">
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-indigo-400 to-purple-400 rounded-t-xl"></div>
          <div className="mb-4 pb-3 border-b border-border flex items-center gap-2">
            <div className="p-1.5 rounded bg-indigo-50 text-indigo-600 dark:bg-indigo-900/30 dark:text-indigo-400">
              <Rocket className="w-4 h-4" />
            </div>
            <h4 className="font-bold text-foreground text-sm">Transformación (DWY)</h4>
          </div>
          
          <div className="space-y-3 flex-1">
            {midTicketOffers.length > 0 ? (
              midTicketOffers.map(offer => (
                <OfferCard 
                  key={offer.offerId} 
                  offer={offer} 
                  currency={currency} 
                  colorTheme="indigo"
                  onMetricClick={onMetricClick} 
                />
              ))
            ) : (
              <div className="h-full flex items-center justify-center py-6">
                <span className="text-xs text-muted-foreground italic">Sin ventas en este nivel</span>
              </div>
            )}
          </div>
        </div>

        {/* Col 3: Delegación (DFY) */}
        <div className="bg-card rounded-xl border border-border p-4 shadow-sm flex flex-col">
          <div className="mb-4 pb-3 border-b border-border flex items-center gap-2">
            <div className="p-1.5 rounded bg-amber-50 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400">
              <Briefcase className="w-4 h-4" />
            </div>
            <h4 className="font-bold text-foreground text-sm">Delegación (DFY / Corp)</h4>
          </div>
          
          <div className="space-y-3 flex-1">
            {highTicketOffers.length > 0 ? (
              highTicketOffers.map(offer => (
                <OfferCard 
                  key={offer.offerId} 
                  offer={offer} 
                  currency={currency} 
                  colorTheme="amber"
                  onMetricClick={onMetricClick} 
                />
              ))
            ) : (
              <div className="h-full flex items-center justify-center py-6">
                <span className="text-xs text-muted-foreground italic">Sin ventas en este nivel</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Fila Inferior: Recurrencia (Expansión) */}
      <div className="mt-6 bg-slate-800 dark:bg-slate-900 rounded-xl p-4 flex flex-col md:flex-row gap-6 items-center justify-between text-white shadow-md border border-slate-700">
        <div className="flex items-center gap-4 md:w-1/3">
          <div className="p-2.5 bg-emerald-500/20 rounded-full text-emerald-400 flex-shrink-0">
            <RefreshCw className="w-6 h-6" />
          </div>
          <div>
            <h4 className="font-bold text-lg leading-tight text-white">Ingreso Recurrente (MRR)</h4>
            <p className="text-xs text-slate-400 mt-0.5">Suscripciones y retainers (Expansión)</p>
          </div>
        </div>
        
        <div className="flex-1 flex flex-col gap-3 w-full md:w-auto px-0 md:px-6 md:border-x md:border-slate-700">
          {recurrenteOffers.length > 0 ? (
            recurrenteOffers.map(offer => {
              const shopifyCount = offer.sourceBreakdown?.SHOPIFY || offer.salesCount;
              return (
                <div 
                  key={offer.offerId}
                  className="bg-slate-700/50 dark:bg-slate-800/80 rounded p-3 flex justify-between items-center hover:bg-slate-700/80 transition-colors cursor-pointer"
                  onClick={() => {
                    if (onMetricClick) {
                      onMetricClick({
                        stageId: 'VENTAS',
                        channelSlug: offer.offerId,
                        metricName: 'revenue',
                        currentValue: offer.totalRevenue,
                        currency: currency,
                      });
                    }
                  }}
                >
                  <div>
                    <span className="text-sm font-medium text-slate-200">{offer.publicName}</span>
                    <p className="text-[10px] text-slate-400 mt-1">
                      Vía: <span className="text-blue-300">Shopify ({shopifyCount})</span>
                    </p>
                  </div>
                  <span className="font-bold text-emerald-400">{formatMoney(offer.totalRevenue, currency)}</span>
                </div>
              );
            })
          ) : (
            <div className="text-center py-2">
              <span className="text-xs text-slate-400 italic">Sin ingresos recurrentes</span>
            </div>
          )}
        </div>
        
        <div className="text-right md:w-1/4">
          <div className="text-2xl font-black text-emerald-400">{formatCompactMoney(totalMrr, currency)}</div>
          <p className="text-xs text-slate-400 mt-1">{totalMrrSubs} Suscripciones Activas</p>
        </div>
      </div>

    </div>
  );
}
