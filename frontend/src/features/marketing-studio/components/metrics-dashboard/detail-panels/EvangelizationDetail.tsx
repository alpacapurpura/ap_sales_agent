'use client';

import { Skeleton } from '@/components/ui/skeleton';
import { useEvangelizationDetail } from '../../../hooks/useEvangelizationDetail';
import { usePromoteEvangelist } from '../../../hooks/useEvangelizationMutations';
import { MiniFunnel } from '../channel-widgets/MiniFunnel';
import { KpiTooltip } from '../channel-widgets/KpiTooltip';
import { BottleneckBanner } from './BottleneckBanner';
import { EvangelistCard } from '../channel-widgets/EvangelistCard';
import { NpsSummaryCard } from '../channel-widgets/NpsSummaryCard';
import { CandidatosBanner } from '../channel-widgets/CandidatosBanner';

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

export function EvangelizationDetail() {
  const { data, isLoading, error } = useEvangelizationDetail();
  const promote = usePromoteEvangelist();

  if (isLoading) {
    return (
      <div className="space-y-4 p-4">
        <Skeleton className="h-6 w-48" />
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-6 w-48" />
        <Skeleton className="h-32 w-full" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <p className="p-4 text-sm text-muted-foreground">
        No se pudieron cargar los datos de evangelizacion. Verifica tu conexion e intenta nuevamente.
      </p>
    );
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
    <div className="space-y-2">
      {/* Timestamp */}
      {data.lastUpdated && (
        <p className="text-[10px] text-muted-foreground px-3 pb-1">
          Ultima actualizacion: {formatLastUpdated(data.lastUpdated)}
        </p>
      )}

      {/* Primary Header KPIs (3) */}
      <div className="flex items-center gap-6 px-3 py-2">
        <div className="flex flex-col">
          <KpiTooltip
            label="K-FACTOR"
            hint="Por cada cliente, cuantos nuevos clientes genera a traves de referidos. Mayor a 1.0 significa crecimiento viral"
          />
          <span className={`text-xl font-semibold tabular-nums ${kFactorColor}`}>
            {headerKpis.kFactor.toFixed(2)}
          </span>
        </div>
        <div className="flex flex-col">
          <KpiTooltip
            label="REFERIDOS CONVERTIDOS"
            hint="Cantidad de ventas que vinieron de un codigo de referido o enlace compartido"
          />
          <span className="text-xl font-semibold tabular-nums">
            {headerKpis.referralConversions.toLocaleString('es-ES')}
          </span>
        </div>
        <div className="flex flex-col">
          <KpiTooltip
            label="NPS SCORE"
            hint="Calificacion de satisfaccion de tus clientes del 0 al 10. Arriba de 8 es excelente"
          />
          <span className="text-xl font-semibold tabular-nums">
            {headerKpis.npsScore?.toFixed(1) ?? '--'}
          </span>
        </div>
      </div>

      {/* Secondary Header KPIs (2) */}
      <div className="flex items-center gap-6 px-3">
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
        <div className="space-y-2 px-3">
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
        <div className="px-3">
          <h3 className="text-sm font-semibold">Referidos</h3>
          <p className="text-xs text-muted-foreground">Ventas atribuidas a codigos de referido</p>
        </div>
        {referidos.length > 0 ? (
          <div className="space-y-2 px-3">
            {referidos.map((e) => (
              <EvangelistCard key={e.customerId} evangelist={e} />
            ))}
          </div>
        ) : (
          <p className="text-xs text-muted-foreground px-3">
            Aun no has promovido evangelistas
          </p>
        )}
      </div>

      {/* Candidatos a Evangelista */}
      <div className="px-3">
        <CandidatosBanner
          candidatos={candidatos}
          onPromote={promote.mutate}
          isPromoting={promote.isPending}
        />
      </div>

      {/* Group 2: Reputacion */}
      <div className="space-y-2">
        <div className="px-3">
          <h3 className="text-sm font-semibold">Reputacion</h3>
          <p className="text-xs text-muted-foreground">Satisfaccion del cliente y contenido generado</p>
        </div>
        <div className="px-3">
          <NpsSummaryCard
            nps={npsSummary}
            ugcCount={data.ugcCount}
            ugcWritten={data.ugcWritten}
            ugcAudio={data.ugcAudio}
          />
        </div>
      </div>
    </div>
  );
}
