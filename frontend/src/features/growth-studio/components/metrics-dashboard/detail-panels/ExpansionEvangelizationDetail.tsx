'use client';

import React, { useState, useMemo, useCallback } from 'react';
import { useExpansionDetail, useEvangelizationDetail } from '../../../hooks/useStageDetail';
import DetailSkeleton from '../ui/DetailSkeleton';
import DetailError from '../ui/DetailError';
import type { MetricClickData } from '../../../types/metrics';
import {
  BarChart2,
  DollarSign,
  Users,
  AlertTriangle,
  Lightbulb,
  TrendingUp,
  ShieldCheck,
  Repeat,
  UserMinus,
  ArrowUpRight,
  BookOpen,
  Megaphone,
  Smile,
  Star,
  Camera,
  Link,
  UserPlus
} from 'lucide-react';
import { formatMoney } from '@/lib/format-money';

interface ExpansionEvangelizationDetailProps {
  onMetricClick?: (metric: MetricClickData) => void;
  onConfigure?: (slug: string, name: string) => void;
}

export const ExpansionEvangelizationDetail = React.memo(function ExpansionEvangelizationDetail({ onMetricClick, onConfigure }: ExpansionEvangelizationDetailProps) {
  const { data: expData, isLoading: expLoading, error: expError, refetch: refetchExp } = useExpansionDetail();
  const { data: evaData, isLoading: evaLoading, error: evaError, refetch: refetchEva } = useEvangelizationDetail();

  const { avgLtv, actives, netMrr, expansionCount, expansionRate, churnRate } = useMemo(() => ({
    avgLtv: expData?.headerKpis.avgLtv || 0,
    actives: expData?.miniFunnel.sourceValue || 0,
    netMrr: expData?.headerKpis.netMrr || 0,
    expansionCount: expData?.miniFunnel.targetValue || 0,
    expansionRate: expData?.miniFunnel.conversionRate || 0,
    churnRate: expData?.headerKpis.churnRatePct || 0,
  }), [expData]);

  const { kFactor, referralConversions, npsScore, referralRevenue } = useMemo(() => ({
    kFactor: evaData?.headerKpis.kFactor || 0,
    referralConversions: evaData?.headerKpis.referralConversions || 0,
    npsScore: evaData?.headerKpis.npsScore ?? null,
    referralRevenue: evaData?.headerKpis.referralRevenue || 0,
  }), [evaData]);

  const handleMetricClick = useCallback((stageId: 'EXPANSION' | 'EVANGELIZACION', channelSlug: string, metricName: string, val: number, channelName?: string) => {
    if (onMetricClick) {
      onMetricClick({
        stageId,
        channelSlug,
        channelName,
        metricName,
        currentValue: val,
      });
    }
  }, [onMetricClick]);

  if (expLoading || evaLoading) {
    return (
      <DetailSkeleton isLoading>
        <></>
      </DetailSkeleton>
    );
  }

  if (expError || evaError) {
    return (
      <DetailError
        error={expError instanceof Error ? expError : (evaError instanceof Error ? evaError : new Error('Error desconocido'))}
        onRetry={() => {
          void refetchExp();
          void refetchEva();
        }}
        lastData={expData || evaData}
      />
    );
  }

  if (!expData || !evaData) return null;

  // Formatters
  const formatNum = (num: number) => num.toLocaleString('es-ES');
  const fmtMoney = (num: number, currency: string) =>
    formatMoney(num, currency, { fractionDigits: 0 });

  return (
    <div className="space-y-8 animate-fade-in block">
      {/* VISIÓN GLOBAL: FUNNEL UNIFICADO */}
      <div className="bg-card rounded-xl p-6 shadow-sm border border-border relative overflow-hidden">
        <h2 className="text-lg font-semibold mb-6 flex items-center text-foreground/90">
          <BarChart2 className="w-5 h-5 mr-2 text-emerald-600" /> Ciclo de Vida del Cliente
        </h2>
        
        <div className="relative mb-6">
          {/* Líneas conectoras */}
          <div className="hidden md:block absolute w-[10%] h-[2px] bg-gradient-to-r from-emerald-200 to-emerald-400 dark:from-emerald-900 dark:to-emerald-700 top-[40%] left-[20%] z-0"></div>
          <div className="hidden md:block absolute w-[10%] h-[2px] bg-gradient-to-r from-emerald-400 to-purple-400 dark:from-emerald-700 dark:to-purple-700 top-[40%] left-[45%] z-0"></div>
          <div className="hidden md:block absolute w-[10%] h-[2px] bg-gradient-to-r from-purple-400 to-purple-600 dark:from-purple-700 dark:to-purple-500 top-[40%] left-[70%] z-0"></div>
          
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 relative z-10 w-full mb-6">
            {/* Bloque 1: Base de Clientes */}
            <div className="bg-background p-5 rounded-lg border border-border shadow-sm flex flex-col items-center justify-center relative">
              <span className="text-[10px] text-muted-foreground font-bold uppercase mb-1">Valor Promedio Por Cliente</span>
              <span className="text-3xl font-black text-foreground">{fmtMoney(avgLtv, expData.headerKpis.currency)}</span>
              <span className="text-xs text-muted-foreground mt-1">Activos: {formatNum(actives)}</span>
            </div>

            {/* Bloque 2: Expansión */}
            <div className="bg-background p-5 rounded-lg border border-emerald-500/20 shadow-sm flex flex-col items-center justify-center relative ring-1 ring-emerald-500/10">
              <span className="text-[10px] text-emerald-600 dark:text-emerald-500 font-bold uppercase mb-1">Ingreso Recurrente Neto</span>
              <span className="text-4xl font-black text-emerald-600 dark:text-emerald-500">{fmtMoney(netMrr, expData.headerKpis.currency)}</span>
              <span className="text-xs text-emerald-600/80 dark:text-emerald-500/80 mt-1 font-medium">Expansión: {formatNum(expansionCount)}</span>
              <span className="mt-3 text-[10px] text-muted-foreground text-center">
                Tasa de Expansión: {expansionRate.toFixed(1)}%
              </span>
            </div>

            {/* Bloque 3: Satisfacción */}
            <div className="flex flex-col items-center justify-center relative">
              <div className="w-16 h-16 rounded-full bg-gradient-to-br from-emerald-400 to-purple-500 text-white flex items-center justify-center shadow-md border-4 border-background">
                <span className="font-bold text-lg">{churnRate.toFixed(1)}%</span>
              </div>
              <span className="text-[10px] text-muted-foreground font-bold uppercase mt-3 text-center">Tasa de Cancelación</span>
            </div>

            {/* Bloque 4: Evangelistas */}
            <div className="bg-purple-950 dark:bg-purple-950/50 p-5 rounded-lg border border-purple-900 shadow-md flex flex-col items-center justify-center relative text-white">
              <span className="text-[10px] text-purple-300 dark:text-purple-400 font-bold uppercase mb-1">Efecto Viral</span>
              <span className="text-4xl font-black text-white">{kFactor.toFixed(2)}</span>
              <span className="text-xs text-purple-200 dark:text-purple-300 mt-1">K-Factor</span>
              <span className="mt-3 text-xs text-emerald-400 dark:text-emerald-500 font-medium">
                <Users className="w-3 h-3 mr-1 inline" /> {evaData.miniFunnel.conversionRate.toFixed(1)}% Conversión
              </span>
            </div>
          </div>

          {/* Alertas */}
          {evaData.candidatos.length === 0 && (evaData.npsSummary.npsScore === null || evaData.npsSummary.totalResponses === 0) && (
            <div className="bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-900/50 rounded-lg p-3 flex gap-3 text-red-900 dark:text-red-200 items-center shadow-sm mb-4">
              <AlertTriangle className="w-5 h-5 text-red-500 flex-shrink-0" />
              <div className="flex-1">
                <p className="text-sm font-medium"><strong>Alerta Detectada:</strong> Aún no tienes información de referidos. Configura encuestas NPS para conocer a tus promotores.</p>
              </div>
              <button 
                className="text-xs bg-red-100 hover:bg-red-200 dark:bg-red-900 dark:hover:bg-red-800 text-red-700 dark:text-red-300 px-3 py-1.5 rounded-md font-medium transition-colors"
                onClick={() => handleMetricClick('EVANGELIZACION', 'nps', 'setup_nps', 0, 'NPS Setup')}
              >
                Configurar NPS
              </button>
            </div>
          )}

          {/* Banner Motivacional */}
          <div className="bg-gradient-to-r from-emerald-50 to-purple-50 dark:from-emerald-950/20 dark:to-purple-950/20 border border-emerald-100 dark:border-emerald-900/50 rounded-lg p-3 flex gap-3 text-emerald-900 dark:text-emerald-200 items-center shadow-sm">
            <Lightbulb className="w-5 h-5 text-emerald-600 flex-shrink-0" />
            <p className="text-sm font-medium">
              <strong>Entiende tus números:</strong> <em>Expansión</em> mide cuánto valor extra extraes de tus clientes actuales (Upsells/Retención), y <em>Evangelización</em> mide cuántos clientes nuevos llegan recomendados por ellos. Haz clic en las métricas para accionar.
            </p>
          </div>
        </div>
      </div>

      {/* Detail Split Columns */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
        
        {/* COLUMNA EXPANSIÓN */}
        <div className="space-y-6">
          <div className="border-b border-border pb-2">
            <h3 className="font-semibold text-lg flex items-center text-foreground/90">
              <TrendingUp className="w-5 h-5 mr-2 text-emerald-600" /> Expansión (LTV & Retención)
            </h3>
            <p className="text-xs text-muted-foreground mt-1">Métricas de salud de tu base de clientes y ventas adicionales.</p>
          </div>
          
          {/* Retención y Churn */}
          <div className="bg-card rounded-lg border border-border shadow-sm overflow-hidden border-l-4 border-l-emerald-500 hover:border-l-emerald-400 transition-colors">
            <div className="bg-muted/50 px-4 py-3 border-b border-border flex justify-between items-center">
              <span className="font-medium text-sm flex items-center text-foreground/90"><ShieldCheck className="w-4 h-4 text-emerald-600 mr-2" /> Retención de Suscripciones</span>
              <div className="flex gap-4 text-xs font-medium">
                <span className="text-muted-foreground">{formatNum(expData.retencion.totalCount)} Renovaciones</span>
              </div>
            </div>
            <div className="p-4 grid grid-cols-1 gap-2">
              {expData.retencion.offers.map((offer) => (
                <div key={offer.offerId} className="border border-border rounded-md p-3 flex justify-between items-center bg-card hover:border-emerald-300 dark:hover:border-emerald-700 transition-colors cursor-pointer group" onClick={() => handleMetricClick('EXPANSION', offer.offerId, 'retencion', offer.count, offer.publicName)}>
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded bg-emerald-100 text-emerald-600 dark:bg-emerald-500/20 dark:text-emerald-400 flex items-center justify-center"><Repeat className="w-4 h-4" /></div>
                    <div>
                      <p className="text-sm font-medium text-foreground">{offer.publicName}</p>
                      <p className="text-[10px] text-emerald-600 dark:text-emerald-500">Tasa de retención: {expData.retencion.ratePct?.toFixed(1) || '100'}%</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-bold text-foreground transition-colors group-hover:text-emerald-600 dark:group-hover:text-emerald-400 underline decoration-dashed underline-offset-4">{formatNum(offer.count)}</p>
                    <p className="text-[10px] text-muted-foreground">transacciones ({formatMoney(offer.revenue, offer.currency)})</p>
                  </div>
                </div>
              ))}
              
              {expData.retencion.offers.length === 0 && (
                <p className="text-xs text-muted-foreground p-2 text-center">Sin transacciones de retención en este periodo</p>
              )}

              {/* Cancelaciones (Churn) */}
              <div className="border border-border rounded-md p-3 flex justify-between items-center bg-card hover:border-red-300 dark:hover:border-red-700 transition-colors cursor-pointer group mt-2" onClick={() => handleMetricClick('EXPANSION', 'churn', 'cancelaciones', expData.cancelaciones.totalCount, 'Cancelaciones')}>
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded bg-red-100 text-red-600 dark:bg-red-500/20 dark:text-red-400 flex items-center justify-center"><UserMinus className="w-4 h-4" /></div>
                  <div>
                    <p className="text-sm font-medium text-foreground">Cancelaciones (Churn)</p>
                    <p className="text-[10px] text-red-500">Tasa de churn: {expData.cancelaciones.ratePct?.toFixed(1) || '0.0'}%</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-bold text-foreground transition-colors group-hover:text-red-600 dark:group-hover:text-red-400 underline decoration-dashed underline-offset-4">{formatNum(expData.cancelaciones.totalCount)}</p>
                  <p className="text-[10px] text-muted-foreground">transacciones (-{formatMoney(expData.cancelaciones.totalRevenue, expData.cancelaciones.currency)})</p>
                </div>
              </div>
            </div>
          </div>

          {/* Crecimiento y Upsells */}
          <div className="bg-card rounded-lg border border-border shadow-sm overflow-hidden border-l-4 border-l-teal-500 hover:border-l-teal-400 transition-colors">
            <div className="bg-muted/50 px-4 py-3 border-b border-border flex justify-between items-center">
              <span className="font-medium text-sm flex items-center text-foreground/90"><ArrowUpRight className="w-4 h-4 text-teal-600 mr-2" /> Crecimiento (Upsells / Cross-sells)</span>
              <div className="flex gap-4 text-xs font-medium">
                <span className="text-teal-600 dark:text-teal-500 font-bold">{formatMoney(expData.crecimiento.totalRevenue, expData.crecimiento.currency)} Extra</span>
              </div>
            </div>
            <div className="p-4 grid grid-cols-1 gap-2">
              {expData.crecimiento.offers.map((offer) => (
                <div key={offer.offerId} className="border border-border rounded-md p-3 flex justify-between items-center bg-card hover:border-teal-300 dark:hover:border-teal-700 transition-colors cursor-pointer group" onClick={() => handleMetricClick('EXPANSION', offer.offerId, 'crecimiento', offer.count, offer.publicName)}>
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded bg-teal-100 text-teal-600 dark:bg-teal-500/20 dark:text-teal-400 flex items-center justify-center"><BookOpen className="w-4 h-4" /></div>
                    <div>
                      <p className="text-sm font-medium text-foreground">{offer.publicName}</p>
                      <p className="text-[10px] text-emerald-600 dark:text-emerald-500">Tasa de expansión: {expData.crecimiento.ratePct?.toFixed(1) || '0'}%</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-bold text-foreground transition-colors group-hover:text-teal-600 dark:group-hover:text-teal-400 underline decoration-dashed underline-offset-4">{formatNum(offer.count)}</p>
                    <p className="text-[10px] text-muted-foreground">transacciones ({formatMoney(offer.revenue, offer.currency)})</p>
                  </div>
                </div>
              ))}
              
              {expData.crecimiento.offers.length === 0 && (
                <p className="text-xs text-muted-foreground p-2 text-center">Sin transacciones de crecimiento en este periodo</p>
              )}
            </div>
          </div>
        </div>

        {/* COLUMNA EVANGELIZACIÓN */}
        <div className="space-y-6">
          <div className="border-b border-border pb-2">
            <h3 className="font-semibold text-lg flex items-center text-foreground/90">
              <Megaphone className="w-5 h-5 mr-2 text-purple-600" /> Evangelización (Referidos)
            </h3>
            <p className="text-xs text-muted-foreground mt-1">El nivel de lealtad que convierte a clientes en tu propio equipo de marketing.</p>
          </div>
          
          {/* Satisfacción y Reseñas */}
          <div className="bg-card rounded-lg border border-border shadow-sm overflow-hidden border-l-4 border-l-indigo-400 hover:border-l-indigo-300 transition-colors">
            <div className="bg-indigo-500/5 px-4 py-3 border-b border-border flex justify-between items-center">
              <span className="font-medium text-sm flex items-center text-foreground/90"><Smile className="w-4 h-4 text-indigo-600 mr-2" /> Satisfacción (NPS & UGC)</span>
              <div className="flex gap-4 text-xs font-medium">
                <span className="text-indigo-600 dark:text-indigo-400 font-bold">{npsScore !== null ? `${npsScore.toFixed(1)} Score` : 'Sin Datos'}</span>
              </div>
            </div>
            <div className="p-4 grid grid-cols-1 gap-2">
              <div className="border border-border rounded-md p-3 flex justify-between items-center bg-card hover:border-indigo-300 dark:hover:border-indigo-700 transition-colors cursor-pointer group" onClick={() => handleMetricClick('EVANGELIZACION', 'nps', 'promotores', evaData.npsSummary.promoterCount, 'Clientes Promotores')}>
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded bg-indigo-100 text-indigo-600 dark:bg-indigo-500/20 dark:text-indigo-400 flex items-center justify-center"><Star className="w-4 h-4" /></div>
                  <div>
                    <p className="text-sm font-medium text-foreground">Clientes Promotores</p>
                    <p className="text-[10px] text-slate-500">{evaData.npsSummary.promoterCount > 0 ? 'Altamente satisfechos' : 'No hay encuestas enviadas aún'}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-bold text-foreground transition-colors group-hover:text-indigo-600 dark:group-hover:text-indigo-400 underline decoration-dashed underline-offset-4">{formatNum(evaData.npsSummary.promoterCount)}</p>
                  <p className="text-[10px] text-muted-foreground">promotores</p>
                </div>
              </div>
              
              <div className="border border-border rounded-md p-3 flex justify-between items-center bg-card hover:border-indigo-300 dark:hover:border-indigo-700 transition-colors cursor-pointer group" onClick={() => handleMetricClick('EVANGELIZACION', 'ugc', 'ugc_count', evaData.ugcCount, 'Contenido UGC')}>
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded bg-indigo-100 text-indigo-600 dark:bg-indigo-500/20 dark:text-indigo-400 flex items-center justify-center"><Camera className="w-4 h-4" /></div>
                  <div>
                    <p className="text-sm font-medium text-foreground">Contenido Generado por Usuario (UGC)</p>
                    <p className="text-[10px] text-slate-500">{evaData.ugcCount > 0 ? 'Menciones en redes y reseñas' : 'No se ha recolectado material'}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-bold text-foreground transition-colors group-hover:text-indigo-600 dark:group-hover:text-indigo-400 underline decoration-dashed underline-offset-4">{formatNum(evaData.ugcCount)}</p>
                  <p className="text-[10px] text-muted-foreground">piezas de contenido</p>
                </div>
              </div>
            </div>
          </div>

          {/* Programa de Referidos */}
          <div className="bg-card rounded-lg border border-border shadow-sm overflow-hidden border-l-4 border-l-purple-500 hover:border-l-purple-400 transition-colors">
            <div className="bg-purple-500/5 px-4 py-3 border-b border-border flex justify-between items-center">
              <span className="font-medium text-sm flex items-center text-foreground/90"><Users className="w-4 h-4 text-purple-600 mr-2" /> Programa de Referidos</span>
              <div className="flex gap-4 text-xs font-medium">
                <span className="text-purple-600 dark:text-purple-400 font-bold">{formatMoney(referralRevenue, evaData.headerKpis.currency)} Ingreso</span>
              </div>
            </div>
            <div className="p-4 grid grid-cols-1 gap-2">
              <div className="border border-border rounded-md p-3 flex justify-between items-center bg-card hover:border-purple-300 dark:hover:border-purple-700 transition-colors cursor-pointer group" onClick={() => handleMetricClick('EVANGELIZACION', 'referrals', 'conversions', referralConversions, 'Enlaces Compartidos')}>
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded bg-purple-100 text-purple-600 dark:bg-purple-500/20 dark:text-purple-400 flex items-center justify-center"><Link className="w-4 h-4" /></div>
                  <div>
                    <p className="text-sm font-medium text-foreground">Enlaces Compartidos</p>
                    <p className="text-[10px] text-slate-500">Tasa de viralidad: {kFactor.toFixed(2)}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-bold text-foreground transition-colors group-hover:text-purple-600 dark:group-hover:text-purple-400 underline decoration-dashed underline-offset-4">{formatNum(referralConversions)}</p>
                  <p className="text-[10px] text-muted-foreground">nuevos clientes</p>
                </div>
              </div>
              
              {/* Candidatos a Evangelistas */}
              <div className="border border-border border-dashed rounded-md p-3 flex justify-between items-center bg-muted/30 hover:bg-muted/60 transition-colors cursor-pointer group" onClick={() => handleMetricClick('EVANGELIZACION', 'candidates', 'count', evaData.candidatos.length, 'Candidatos a Evangelistas')}>
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded bg-slate-200 text-slate-600 dark:bg-slate-800 dark:text-slate-400 flex items-center justify-center"><UserPlus className="w-4 h-4" /></div>
                  <div>
                    <p className="text-sm font-medium text-foreground">Candidatos a Evangelistas</p>
                    <p className="text-[10px] text-amber-600 dark:text-amber-500">{evaData.candidatos.length > 0 ? 'Promotores sin código de referido' : 'Falta identificar promotores (NPS)'}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-bold text-foreground transition-colors group-hover:text-purple-600 dark:group-hover:text-purple-400 underline decoration-dashed underline-offset-4">{formatNum(evaData.candidatos.length)}</p>
                  <p className="text-[10px] text-muted-foreground">potenciales referidores</p>
                </div>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
});