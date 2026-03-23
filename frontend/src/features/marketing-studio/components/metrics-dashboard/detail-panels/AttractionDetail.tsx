'use client';

import { useState } from 'react';
import { useAttractionDetail } from '../../../hooks/useAttractionDetail';
import { useMetaInitialLoad } from '../../../hooks/useMetaInitialLoad';
import { ChannelGroupCard } from '../channel-widgets/ChannelGroupCard';
import { ActionPanel } from '../action-widgets/ActionPanel';
import DetailSkeleton from '../ui/DetailSkeleton';
import DetailEmpty from '../ui/DetailEmpty';
import DetailError from '../ui/DetailError';
import type { MetricClickData, StageSummary } from '../../../types/metrics';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Settings, Download, Loader2, CheckCircle2 } from 'lucide-react';

const ATRACCION_STAGE: StageSummary = {
  id: 'ATRACCION',
  order: 0,
  label: 'Atraccion',
  description: 'Trafico y alcance de canales de marketing',
  mainKpi: { label: 'visitantes', value: 0 },
  secondaryKpi: { label: 'canales activos', value: 0 },
  hasDetail: true,
};

function formatLastUpdated(isoDate: string): string {
  const d = new Date(isoDate);
  return d.toLocaleDateString('es-ES', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  }) + ', ' + d.toLocaleTimeString('es-ES', {
    hour: '2-digit',
    minute: '2-digit',
  });
}

interface AttractionDetailProps {
  /** Callback when user clicks a metric value to open the action sidebar */
  onMetricClick?: (metric: MetricClickData) => void;
  /** Callback when user clicks "Configurar" on an unconnected channel */
  onConfigure?: (slug: string, name: string) => void;
}

export function AttractionDetail({ onMetricClick, onConfigure }: AttractionDetailProps) {
  const { data, isLoading, error, refetch } = useAttractionDetail();
  const { trigger: triggerLoad, isLoading: isLoadingMeta, result: loadResult, error: loadError } = useMetaInitialLoad();
  const [isPanelOpen, setIsPanelOpen] = useState(false);

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
    return <DetailEmpty stage={ATRACCION_STAGE} />;
  }

  // Compute header KPIs from group totals
  const allGroups = [data.organicSocial, data.ga4Search, data.paid, data.outbound];
  const totalVisitors = allGroups.reduce((sum, g) => sum + (g.totals.visitors ?? g.totals.totalVisitors ?? 0), 0);
  const totalReach = allGroups.reduce((sum, g) => sum + (g.totals.reach ?? 0), 0);
  const totalSpend = allGroups.reduce((sum, g) => sum + (g.totals.spend ?? 0), 0);
  const connectedChannels = allGroups.flatMap(g => g.channels.filter(c => c.connected)).length;

  return (
    <div className="space-y-4 animate-fade-in">
      {/* Header & Timestamp */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold tracking-tight">Detalle: Atracción</h2>
        {data.lastUpdated && (
          <span className="text-xs text-muted-foreground italic bg-muted/30 px-2 py-1 rounded-md">
            Actualizado: {formatLastUpdated(data.lastUpdated)}
          </span>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column (Main Content) - 66% */}
        <div className="lg:col-span-2 space-y-8">
          
          {/* Header KPIs — 3 independent cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Card className="shadow-sm hover:shadow-md transition-shadow">
              <CardContent className="p-4 flex flex-col">
                <span className="text-[10px] text-muted-foreground uppercase tracking-wide font-semibold">VISITANTES TOTALES</span>
                <span className="text-2xl font-bold tabular-nums mt-1 text-primary">
                  {totalVisitors > 0 ? totalVisitors.toLocaleString('es-ES') : '---'}
                </span>
              </CardContent>
            </Card>
            <Card className="shadow-sm hover:shadow-md transition-shadow">
              <CardContent className="p-4 flex flex-col">
                <span className="text-[10px] text-muted-foreground uppercase tracking-wide font-semibold">ALCANCE TOTAL</span>
                <span className="text-2xl font-bold tabular-nums mt-1">
                  {totalReach > 0 ? totalReach.toLocaleString('es-ES') : '---'}
                </span>
              </CardContent>
            </Card>
            <Card className="shadow-sm hover:shadow-md transition-shadow">
              <CardContent className="p-4 flex flex-col">
                <span className="text-[10px] text-muted-foreground uppercase tracking-wide font-semibold">
                  {totalSpend > 0 ? 'GASTO TOTAL' : 'CANALES ACTIVOS'}
                </span>
                <span className="text-2xl font-bold tabular-nums mt-1">
                  {totalSpend > 0
                    ? `$${totalSpend.toLocaleString('es-ES', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`
                    : `${connectedChannels}`}
                </span>
              </CardContent>
            </Card>
          </div>

          {/* Channel Groups - Vertical Stack of Cards */}
          <div className="space-y-6">
            
            <ChannelGroupCard
              title="Publicidad Pagada"
              totals={data.paid.totals}
              channels={data.paid.channels}
              groupType="paid"
              stageId="ATRACCION"
              onMetricClick={onMetricClick}
            />
            <ChannelGroupCard
              title="Trabajo Orgánico"
              totals={data.organicSocial.totals}
              channels={data.organicSocial.channels}
              groupType="organic_social"
              stageId="ATRACCION"
              onMetricClick={onMetricClick}
            />
            <ChannelGroupCard
              title="Busquedas en Google"
              totals={data.ga4Search.totals}
              channels={data.ga4Search.channels}
              groupType="ga4_search"
              stageId="ATRACCION"
              onMetricClick={onMetricClick}
            />
            <ChannelGroupCard
              title="Contacto Directo"
              totals={data.outbound.totals}
              channels={data.outbound.channels}
              groupType="outbound"
              stageId="ATRACCION"
              onMetricClick={onMetricClick}
            />
            {data.available && data.available.channels.length > 0 && (
              <ChannelGroupCard
                title="Canales Disponibles"
                totals={{}}
                channels={data.available.channels}
                groupType="available"
                stageId="ATRACCION"
                onMetricClick={onMetricClick}
                onConfigure={onConfigure}
              />
            )}
          </div>
        </div>

        {/* Right Column (Sidebar) - 33% */}
        <div className="space-y-6">
          <Button
            variant="default"
            className="w-full"
            onClick={() => triggerLoad(30)}
            disabled={isLoadingMeta}
          >
            {isLoadingMeta ? (
              <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Cargando datos Meta...</>
            ) : loadResult ? (
              <><CheckCircle2 className="mr-2 h-4 w-4" />Datos Meta cargados</>
            ) : (
              <><Download className="mr-2 h-4 w-4" />Cargar datos Meta</>
            )}
          </Button>
          {loadResult && (
            <p className="text-xs text-muted-foreground">
              {loadResult.loaded_days} días cargados, {loadResult.skipped_days} ya existían
            </p>
          )}
          {loadError && (
            <p className="text-xs text-destructive">
              {loadError instanceof Error ? loadError.message : 'Error al cargar datos'}
            </p>
          )}
          <Button
            variant="outline"
            className="w-full"
            onClick={() => setIsPanelOpen(true)}
          >
            <Settings className="mr-2 h-4 w-4" />
            Gestionar Atracción
          </Button>
          <ActionPanel
            isOpen={isPanelOpen}
            onClose={() => setIsPanelOpen(false)}
          />
        </div>
      </div>
    </div>
  );
}
