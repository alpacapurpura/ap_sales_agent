'use client';

import { useEvangelizationDetail } from '../../../hooks/useEvangelizationDetail';
import { usePromoteEvangelist } from '../../../hooks/useEvangelizationMutations';
import { MiniFunnel } from '../channel-widgets/MiniFunnel';
import { KpiTooltip } from '../channel-widgets/KpiTooltip';
import { BottleneckBanner } from './BottleneckBanner';
import { EvangelistCard } from '../channel-widgets/EvangelistCard';
import { NpsSummaryCard } from '../channel-widgets/NpsSummaryCard';
import { CandidatosBanner } from '../channel-widgets/CandidatosBanner';
import DetailSkeleton from '../ui/DetailSkeleton';
import DetailEmpty from '../ui/DetailEmpty';
import DetailError from '../ui/DetailError';
import type { MetricClickData, StageSummary } from '../../../types/metrics';

const EVANGELIZACION_STAGE: StageSummary = {
  id: 'EVANGELIZACION',
  order: 7,
  label: 'Evangelizacion',
  description: 'K-Factor, referidos y NPS de clientes',
  mainKpi: { label: 'k-factor', value: 0 },
  secondaryKpi: { label: 'referidos', value: 0 },
  hasDetail: true,
};

function formatLastUpdated(isoDate: string): string {
  const d = new Date(isoDate);
  return d.toLocaleDateString('es-ES', { day: 'numeric', month: 'short', year: 'numeric' })
    + ', ' + d.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' });
}

function formatDualCurrency(amount: number, currency: string, usdAmount: number | null): string {
  const fmt = new Intl.NumberFormat('es-MX', {
    style: 'currency',
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  });
  const main = fmt.format(amount);

  if (currency === 'USD') return main;
  if (usdAmount != null) {
    const usdFmt = new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    });
    return `${main} (~${usdFmt.format(usdAmount)} USD)`;
  }
  return main;
}

interface EvangelizationDetailProps {
  onMetricClick?: (metric: MetricClickData) => void;
}

export function EvangelizationDetail({ onMetricClick }: EvangelizationDetailProps) {
  const { data, isLoading, error, refetch } = useEvangelizationDetail();
  const promote = usePromoteEvangelist();

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
    return <DetailEmpty stage={EVANGELIZACION_STAGE} />;
  }

  // Empty state: no referidos AND no NPS
  if (data.referidos.length === 0 && data.npsSummary.totalResponses === 0 && data.candidatos.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
        <h3 className="text-sm font-semibold">Sin evangelistas activos</h3>
        <p className="text-xs text-muted-foreground mt-2 max-w-md">
          Cuando tus clientes comiencen a referir nuevos prospectos, aqui veras el impacto de boca en boca en tu negocio.
        </p>
      </div>
    );
  }

  const { headerKpis, miniFunnel, referidos, candidatos, npsSummary, bottlenecks } = data;

  const kFactorColor = headerKpis.kFactor >= 1.0
    ? 'text-emerald-600 dark:text-emerald-400'
    : headerKpis.kFactor >= 0.5
      ? 'text-yellow-600 dark:text-yellow-400'
      : 'text-red-600 dark:text-red-400';

  return (
    <div className="space-y-4 animate-fade-in">
      {/* Timestamp */}
      {data.lastUpdated && (
        <p className="text-[10px] text-muted-foreground italic">
          Actualizado: {formatLastUpdated(data.lastUpdated)}
        </p>
      )}

      {/* Primary Header KPIs — responsive 3-column grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <div
          className={`flex flex-col bg-muted/30 rounded-lg p-3 ${onMetricClick ? 'cursor-pointer hover:bg-muted/50 transition-colors duration-100' : ''}`}
          onClick={onMetricClick ? () => onMetricClick({
            stageId: 'EVANGELIZACION',
            channelSlug: 'referidos',
            metricName: 'k_factor',
            currentValue: headerKpis.kFactor,
          }) : undefined}
          role={onMetricClick ? 'button' : undefined}
          tabIndex={onMetricClick ? 0 : undefined}
        >
          <KpiTooltip
            label="K-FACTOR"
            hint="Por cada cliente, cuantos nuevos clientes genera a traves de referidos. Mayor a 1.0 significa crecimiento viral"
          />
          <span className={`text-xl sm:text-2xl font-semibold tabular-nums mt-1 ${kFactorColor}`}>
            {headerKpis.kFactor.toFixed(2)}
          </span>
        </div>
        <div
          className={`flex flex-col bg-muted/30 rounded-lg p-3 ${onMetricClick ? 'cursor-pointer hover:bg-muted/50 transition-colors duration-100' : ''}`}
          onClick={onMetricClick ? () => onMetricClick({
            stageId: 'EVANGELIZACION',
            channelSlug: 'referidos',
            metricName: 'referral_conversions',
            currentValue: headerKpis.referralConversions,
          }) : undefined}
          role={onMetricClick ? 'button' : undefined}
          tabIndex={onMetricClick ? 0 : undefined}
        >
          <KpiTooltip
            label="REFERIDOS CONVERTIDOS"
            hint="Cantidad de ventas que vinieron de un codigo de referido o enlace compartido"
          />
          <span className="text-xl sm:text-2xl font-semibold tabular-nums mt-1">
            {headerKpis.referralConversions.toLocaleString('es-ES')}
          </span>
        </div>
        <div
          className={`flex flex-col bg-muted/30 rounded-lg p-3 ${onMetricClick ? 'cursor-pointer hover:bg-muted/50 transition-colors duration-100' : ''}`}
          onClick={onMetricClick ? () => onMetricClick({
            stageId: 'EVANGELIZACION',
            channelSlug: 'nps',
            metricName: 'nps_score',
            currentValue: headerKpis.npsScore ?? 0,
          }) : undefined}
          role={onMetricClick ? 'button' : undefined}
          tabIndex={onMetricClick ? 0 : undefined}
        >
          <KpiTooltip
            label="NPS SCORE"
            hint="Calificacion de satisfaccion de tus clientes del 0 al 10. Arriba de 8 es excelente"
          />
          <span className="text-xl sm:text-2xl font-semibold tabular-nums mt-1">
            {headerKpis.npsScore?.toFixed(1) ?? '--'}
          </span>
        </div>
      </div>

      {/* Secondary KPIs */}
      <div className="flex items-center gap-4 sm:gap-6 flex-wrap">
        <div className="flex flex-col">
          <KpiTooltip
            label="REVENUE REFERIDO"
            hint="Dinero total generado por ventas atribuidas a referidos"
          />
          <span className="text-sm font-semibold tabular-nums">
            {formatDualCurrency(headerKpis.referralRevenue, headerKpis.currency, headerKpis.referralRevenueUsd)}
          </span>
        </div>
        <div className="flex flex-col">
          <KpiTooltip
            label="EVANGELISTAS ACTIVOS"
            hint="Clientes que tienen un codigo de referido activo y han generado al menos una conversion"
          />
          <span className="text-sm font-semibold tabular-nums">
            {headerKpis.activeEvangelists}
          </span>
        </div>
      </div>

      {/* MiniFunnel */}
      <MiniFunnel data={miniFunnel} />

      {/* Bottleneck Banners */}
      {bottlenecks.length > 0 && (
        <div className="space-y-2">
          {bottlenecks.map((b) => (
            <BottleneckBanner
              key={`${b.type}-${b.metricLabel}`}
              bottleneck={{
                type: b.type as 'abandoned_cart' | 'meeting_no_show',
                metricLabel: b.metricLabel,
                currentRate: b.currentRate,
                severity: b.severity,
                threshold: b.threshold,
                tip: b.tip,
              }}
            />
          ))}
        </div>
      )}

      {/* Group 1: Referidos */}
      <div className="space-y-2">
        <div>
          <h3 className="text-sm font-semibold">Referidos</h3>
          <p className="text-xs text-muted-foreground">Ventas atribuidas a codigos de referido</p>
        </div>
        {referidos.length > 0 ? (
          <div className="space-y-2">
            {referidos.map((e) => (
              <div
                key={e.customerId}
                className={onMetricClick ? 'cursor-pointer hover:opacity-90 transition-opacity duration-100' : ''}
                onClick={onMetricClick ? () => onMetricClick({
                  stageId: 'EVANGELIZACION',
                  channelSlug: `evangelist-${e.customerId}`,
                  metricName: 'revenue_attributed',
                  currentValue: e.revenueAttributed,
                  currency: e.currency,
                }) : undefined}
                role={onMetricClick ? 'button' : undefined}
                tabIndex={onMetricClick ? 0 : undefined}
              >
                <EvangelistCard evangelist={e} />
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-muted-foreground">
            Aun no has promovido evangelistas
          </p>
        )}
      </div>

      {/* Candidatos a Evangelista */}
      <CandidatosBanner
        candidatos={candidatos}
        onPromote={promote.mutate}
        isPromoting={promote.isPending}
      />

      {/* Group 2: Reputacion */}
      <div className="space-y-2">
        <div>
          <h3 className="text-sm font-semibold">Reputacion</h3>
          <p className="text-xs text-muted-foreground">Satisfaccion del cliente y contenido generado</p>
        </div>
        <NpsSummaryCard
          nps={npsSummary}
          ugcCount={data.ugcCount}
          ugcWritten={data.ugcWritten}
          ugcAudio={data.ugcAudio}
        />
      </div>
    </div>
  );
}
