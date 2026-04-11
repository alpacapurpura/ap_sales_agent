'use client';

import { useMemo, useState } from 'react';
import { Loader2 } from 'lucide-react';

import { TooltipProvider } from '@/components/ui/tooltip';
import { ChartSection } from '../../shared/ChartSection';
import { MetaAdsMiniFunnel } from '../MetaAdsMiniFunnel';
import { InversionChart } from '../InversionChart';
import { MetaAdsHealthCheckPanel } from '../MetaAdsHealthCheckPanel';
import { OfferSegmenter } from '../OfferSegmenter';
import type { OfferSegmenterSelection } from '../OfferSegmenter';
import { UnassignedBanner } from '../UnassignedBanner';
import {
  useMetaHealthCheck,
  useMetricsByOffer,
} from '../../../../../api/offer-association-api';
import { useTenantLocale } from '@/features/tenant/context/tenant-locale-context';
import type {
  ChannelDashboardData,
  CampaignPerformanceData,
  MetaAdsDashboardTab,
  MetaAdsPeriod,
} from '../../../../../types/metrics';
import { ResumenKpiCard } from '../components/ResumenKpiCard';
import { useResumenViewData } from '../hooks/useResumenViewData';

interface ResumenTabProps {
  data: ChannelDashboardData | undefined;
  isLoading: boolean;
  campaignData?: CampaignPerformanceData;
  period?: MetaAdsPeriod;
  onNavigateToTab?: (tab: MetaAdsDashboardTab) => void;
  onAssignCampaigns?: () => void;
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function ResumenTab({
  data,
  isLoading,
  campaignData,
  period = '30d',
  onNavigateToTab,
  onAssignCampaigns,
}: ResumenTabProps) {
  const { currency: tenantCurrency } = useTenantLocale();
  const [selectedOfferId, setSelectedOfferId] =
    useState<OfferSegmenterSelection>('all');

  const { data: healthCheck, isLoading: isHealthLoading } = useMetaHealthCheck();
  const { data: metricsByOffer } = useMetricsByOffer(period);

  const unassignedCount = healthCheck?.unassignedTargets.length ?? 0;
  const hasUnassigned = unassignedCount > 0;
  const hasBranding = (metricsByOffer?.brandingOnly.targetCount ?? 0) > 0;

  // Lookup map externalId → campaign name so each performance recommendation
  // can render a "Campaña: X" context badge inside the health panel.
  const campaignNameById = useMemo<Record<string, string>>(() => {
    const map: Record<string, string> = {};
    campaignData?.campaigns.forEach(c => {
      map[c.externalId] = c.name;
    });
    return map;
  }, [campaignData?.campaigns]);

  const handleAssignClick = () => {
    if (onAssignCampaigns) {
      onAssignCampaigns();
    } else {
      onNavigateToTab?.('campanas');
    }
  };

  const viewData = useResumenViewData({
    metricsByOffer,
    channelData: data,
    selectedOfferId,
    tenantCurrency,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="py-24 text-center text-sm text-muted-foreground">
        No hay datos disponibles
      </div>
    );
  }

  const hasTimeSeries = viewData.timeSeries.some(
    ts => ts.metricName === 'spend' && ts.dataPoints.length > 0,
  );

  return (
    <TooltipProvider delayDuration={250}>
      <div className="space-y-6">
        {/* Live region for screen readers — announces the active filter */}
        <span role="status" aria-live="polite" className="sr-only">
          {viewData.contextLabel
            ? `Filtro activo: ${viewData.contextLabel}. Mostrando ${viewData.kpis.length} métricas.`
            : ''}
        </span>

        {/* Health Check panel — structural diagnostic + campaign recommendations */}
        <ChartSection slug="health-check">
          <MetaAdsHealthCheckPanel
            data={healthCheck}
            isLoading={isHealthLoading}
            onAssignClick={handleAssignClick}
            campaignRecommendations={campaignData?.recommendations}
            campaignNameById={campaignNameById}
            onRecommendationAction={() => onNavigateToTab?.('campanas')}
          />
        </ChartSection>

        {/* Unassigned banner (persistent prompt to assign) */}
        {hasUnassigned && (
          <UnassignedBanner count={unassignedCount} onAssignClick={handleAssignClick} />
        )}

        {/* Segmenter + KPI grid — conceptually one block, tighter spacing */}
        {metricsByOffer && metricsByOffer.offers.length > 0 && (
          <section className="space-y-5">
            <ChartSection slug="segmentador-offers">
              <div className="space-y-2">
                <p className="text-[10px] text-muted-foreground uppercase tracking-wider">
                  Filtrar por offer
                </p>
                <OfferSegmenter
                  offers={metricsByOffer.offers}
                  selectedOfferId={selectedOfferId}
                  onSelect={setSelectedOfferId}
                  hasUnassigned={hasUnassigned}
                  hasBranding={hasBranding}
                />
                {viewData.filter !== 'all' && viewData.contextLabel && (
                  <p className="text-[11px] text-muted-foreground">{viewData.contextLabel}</p>
                )}
              </div>
            </ChartSection>

            <ChartSection slug="kpis">
              <div
                role="group"
                aria-label="Resumen de métricas"
                className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2.5"
              >
                {viewData.kpis.map(card => (
                  <ResumenKpiCard
                    key={card.key}
                    card={card}
                    onCtaClick={handleAssignClick}
                  />
                ))}
              </div>
            </ChartSection>
          </section>
        )}

        {/* Fallback: no offers at all — still render the channel-level KPI summary
            using the "all" builder with empty offers. The hook handles the empty
            state and returns kpis: [] in that case, so we skip the grid entirely. */}

        {/* Inversión y Retorno — full width */}
        {hasTimeSeries && (
          <ChartSection slug="inversion-vs-resultados">
            <InversionChart
              timeSeries={viewData.timeSeries}
              filter={viewData.filter}
              offerName={
                viewData.filter === 'offer' && typeof selectedOfferId === 'string'
                  ? metricsByOffer?.offers.find(o => o.offerId === selectedOfferId)?.offerName
                  : undefined
              }
            />
          </ChartSection>
        )}

        {/* Embudo de conversión — separate section */}
        <ChartSection slug="embudo">
          <div className="rounded-lg border bg-card p-5 space-y-3">
            <h3 className="text-sm font-medium">Embudo de conversión</h3>
            <MetaAdsMiniFunnel steps={viewData.funnel} filter={viewData.filter} />
          </div>
        </ChartSection>
      </div>
    </TooltipProvider>
  );
}
