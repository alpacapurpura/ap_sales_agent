'use client';

import type { CSSProperties } from 'react';
import { useAuth } from '@clerk/nextjs';
import { useQuery } from '@tanstack/react-query';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { ExternalLink, Package, PlusCircle, RefreshCw, Settings, ShoppingBag, TrendingUp, Users } from 'lucide-react';
import type { MetricClickData, StageId } from '../../../types/metrics';
import { getChannelColor, getChannelIcon } from '../../../lib/channelIcons';
import { METRIC_LABELS } from '../../../lib/metric-labels';
import { getOfferProductsDetail } from '../../../api/product-mapping-api';
import type { OfferProductDetail } from '../../../api/product-mapping-api';

interface SidebarContentProps {
  /** The metric that was clicked; null if sidebar was opened without context */
  metric: MetricClickData | null;
  /** Stage context determines which specialized content adapter to render */
  stageId: StageId | null;
}

// ─── Stage label mapping ───────────────────────────────────────────────────────

const STAGE_NAMES: Record<StageId, string> = {
  ATRACCION_CAPTURA: 'Atraccion & Captura',
  ATRACCION: 'Atraccion',
  CAPTURA: 'Captura',
  NUTRICION_OPORTUNIDAD: 'Nutricion & Oportunidad',
  NUTRICION: 'Nutricion',
  OPORTUNIDAD: 'Oportunidad',
  VENTAS: 'Ventas',
  ADOPCION: 'Adopción',
  EXPANSION: 'Expansión',
  EVANGELIZACION: 'Evangelización',
  EXPANSION_EVANGELIZACION: 'Expansión & Evangelización',
};

// ─── Shared placeholders ───────────────────────────────────────────────────────

function ProximamenteBadge() {
  return (
    <Badge variant="secondary" className="text-[10px] px-1.5 py-0 h-4 mr-1">
      Pronto
    </Badge>
  );
}

interface ActionButtonsProps {
  stageId: StageId | null;
  channelSlug?: string;
}

function ActionButtons({ stageId, channelSlug }: ActionButtonsProps) {
  const stageName = stageId ? STAGE_NAMES[stageId] : 'esta etapa';

  return (
    <div className="space-y-2">
      <p className="text-xs font-medium text-muted-foreground uppercase tracking-widest">
        Acciones disponibles
      </p>

      <Button
        variant="outline"
        size="sm"
        className="w-full justify-start gap-2"
        disabled
      >
        <PlusCircle className="h-3.5 w-3.5 flex-shrink-0" />
        <ProximamenteBadge />
        Crear campana para {stageName}
      </Button>

      <Button
        variant="outline"
        size="sm"
        className="w-full justify-start gap-2"
        disabled
      >
        <Settings className="h-3.5 w-3.5 flex-shrink-0" />
        <ProximamenteBadge />
        Editar configuracion{channelSlug ? ` de ${channelSlug}` : ''}
      </Button>

      <Button
        variant="outline"
        size="sm"
        className="w-full justify-start gap-2"
        disabled
      >
        <ExternalLink className="h-3.5 w-3.5 flex-shrink-0" />
        <ProximamenteBadge />
        Ver historial detallado
      </Button>
    </div>
  );
}

// Channel icon wrapper (avoids creating components during render)
/* eslint-disable react-hooks/static-components -- dynamic icon from registry */
function ChannelIconInline({ slug, className, style }: { slug: string; className?: string; style?: CSSProperties }) {
  const Icon = getChannelIcon(slug);
  return <Icon className={className} style={style} />;
}
/* eslint-enable react-hooks/static-components */

interface ChannelInfoCardProps {
  channelSlug: string;
}

function ChannelInfoCard({ channelSlug }: ChannelInfoCardProps) {
  const iconColor = getChannelColor(channelSlug);

  return (
    <Card className="border-muted">
      <CardContent className="py-3 px-4 space-y-2">
        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
          Canal
        </p>
        <div className="flex items-center gap-2">
          <ChannelIconInline slug={channelSlug} className="w-4 h-4 flex-shrink-0" style={{ color: iconColor }} />
          <span className="text-sm font-mono">{channelSlug}</span>
        </div>
        <div className="space-y-1">
          <Button
            variant="outline"
            size="sm"
            className="w-full justify-start gap-2 text-xs"
            disabled
          >
            <ProximamenteBadge />
            Ver detalles de campanas
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

// ─── Stage-specific content adapters ──────────────────────────────────────────

function AttractionMetricDetail({ metric }: { metric: MetricClickData }) {
  const hasMetrics = metric.channelMetrics && metric.channelMetrics.length > 0;

  return (
    <div className="space-y-4">
      <div className="rounded-md bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800 p-3">
        <p className="text-xs text-blue-700 dark:text-blue-300 font-medium">
          Atraccion — Trafico y alcance de canales organicos y pagados
        </p>
        <p className="text-xs text-muted-foreground mt-1">
          Esta metrica mide el volumen de personas que llegan a tu ecosistema a traves de {metric.channelName || metric.channelSlug}.
        </p>
      </div>

      {hasMetrics && (
        <div className="space-y-2">
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-widest">
            Métricas del Canal
          </p>
          <div className="grid grid-cols-2 gap-2">
            {metric.channelMetrics?.map((m, idx) => (
              <Card key={idx} className="border-muted bg-card shadow-sm">
                <CardContent className="p-3 flex flex-col items-center justify-center text-center">
                  <span className="text-xl font-bold text-foreground">
                    {m.currency ? '$' : ''}{m.value.toLocaleString('es-ES')}{m.unit || ''}
                  </span>
                  <span className="text-[10px] text-muted-foreground mt-1">
                    {METRIC_LABELS[m.name] || m.name}
                  </span>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      <Card className="border-dashed">
        <CardContent className="py-3 px-4">
          <p className="text-xs text-muted-foreground font-medium mb-2">Detalles de campana</p>
          <p className="text-xs text-muted-foreground italic">
            Detalles de campanas por canal — proxima version
          </p>
        </CardContent>
      </Card>
      <ActionButtons stageId="ATRACCION" channelSlug={metric.channelSlug} />
      <ChannelInfoCard channelSlug={metric.channelSlug} />
    </div>
  );
}

function CaptureMetricDetail({ metric }: { metric: MetricClickData }) {
  const hasMetrics = metric.channelMetrics && metric.channelMetrics.length > 0;

  return (
    <div className="space-y-4">
      <div className="rounded-md bg-purple-50 dark:bg-purple-950/20 border border-purple-200 dark:border-purple-800 p-3">
        <p className="text-xs text-purple-700 dark:text-purple-300 font-medium">
          Captura — Leads generados desde formularios y agentes conversacionales
        </p>
        <p className="text-xs text-muted-foreground mt-1">
          Esta metrica mide cuantos visitantes se convirtieron en contactos capturados via {metric.channelName || metric.channelSlug}.
        </p>
      </div>

      {hasMetrics && (
        <div className="space-y-2">
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-widest">
            Métricas del Canal
          </p>
          <div className="grid grid-cols-2 gap-2">
            {metric.channelMetrics?.map((m, idx) => (
              <Card key={idx} className="border-muted bg-card shadow-sm">
                <CardContent className="p-3 flex flex-col items-center justify-center text-center">
                  <span className="text-xl font-bold text-foreground">
                    {m.currency ? '$' : ''}{m.value.toLocaleString('es-ES')}{m.unit || ''}
                  </span>
                  <span className="text-[10px] text-muted-foreground mt-1">
                    {METRIC_LABELS[m.name] || m.name}
                  </span>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      <Card className="border-dashed">
        <CardContent className="py-3 px-4">
          <p className="text-xs text-muted-foreground font-medium mb-2">Leads por fuente</p>
          <p className="text-xs text-muted-foreground italic">
            Detalle de leads por formulario — proxima version
          </p>
        </CardContent>
      </Card>
      <ActionButtons stageId="CAPTURA" channelSlug={metric.channelSlug} />
      <ChannelInfoCard channelSlug={metric.channelSlug} />
    </div>
  );
}

function NurtureMetricDetail({ metric }: { metric: MetricClickData }) {
  const hasMetrics = metric.channelMetrics && metric.channelMetrics.length > 0;
  
  return (
    <div className="space-y-4">
      <div className="rounded-md bg-pink-50 dark:bg-pink-950/20 border border-pink-200 dark:border-pink-800 p-3">
        <p className="text-xs text-pink-700 dark:text-pink-300 font-medium">
          Nutricion — MQLs calificados por retargeting y automatizaciones
        </p>
        <p className="text-xs text-muted-foreground mt-1">
          Esta metrica mide leads que alcanzaron calificacion de marketing (MQL) via {metric.channelName || metric.channelSlug}.
        </p>
      </div>
      
      {hasMetrics && (
        <div className="space-y-2">
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-widest">
            Métricas del Canal
          </p>
          <div className="grid grid-cols-2 gap-2">
            {metric.channelMetrics?.map((m, idx) => (
              <Card key={idx} className="border-muted bg-card shadow-sm">
                <CardContent className="p-3 flex flex-col items-center justify-center text-center">
                  <span className="text-xl font-bold text-foreground">
                    {m.currency ? '$' : ''}{m.value.toLocaleString('es-ES')}{m.unit || ''}
                  </span>
                  <span className="text-[10px] text-muted-foreground mt-1">
                    {METRIC_LABELS[m.name] || m.name}
                  </span>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      <Card className="border-dashed">
        <CardContent className="py-3 px-4">
          <p className="text-xs text-muted-foreground font-medium mb-2">Campanas de retargeting</p>
          <p className="text-xs text-muted-foreground italic">
            Detalle de campanas — proxima version
          </p>
        </CardContent>
      </Card>
      <ActionButtons stageId="NUTRICION" channelSlug={metric.channelSlug} />
      <ChannelInfoCard channelSlug={metric.channelSlug} />
    </div>
  );
}

function OpportunityMetricDetail({ metric }: { metric: MetricClickData }) {
  const hasMetrics = metric.channelMetrics && metric.channelMetrics.length > 0;

  return (
    <div className="space-y-4">
      <div className="rounded-md bg-orange-50 dark:bg-orange-950/20 border border-orange-200 dark:border-orange-800 p-3">
        <p className="text-xs text-orange-700 dark:text-orange-300 font-medium">
          Oportunidad — SQLs listos para decision de compra
        </p>
        <p className="text-xs text-muted-foreground mt-1">
          Esta metrica mide leads que llegaron a checkout o calificacion via {metric.channelName || metric.channelSlug}.
        </p>
      </div>

      {hasMetrics && (
        <div className="space-y-2">
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-widest">
            Métricas del Canal
          </p>
          <div className="grid grid-cols-2 gap-2">
            {metric.channelMetrics?.map((m, idx) => (
              <Card key={idx} className="border-muted bg-card shadow-sm">
                <CardContent className="p-3 flex flex-col items-center justify-center text-center">
                  <span className="text-xl font-bold text-foreground">
                    {m.currency ? '$' : ''}{m.value.toLocaleString('es-ES')}{m.unit || ''}
                  </span>
                  <span className="text-[10px] text-muted-foreground mt-1">
                    {METRIC_LABELS[m.name] || m.name}
                  </span>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      <Card className="border-dashed">
        <CardContent className="py-3 px-4">
          <p className="text-xs text-muted-foreground font-medium mb-2">Detalle de checkout</p>
          <p className="text-xs text-muted-foreground italic">
            Detalles de oportunidades — proxima version
          </p>
        </CardContent>
      </Card>
      <ActionButtons stageId="OPORTUNIDAD" channelSlug={metric.channelSlug} />
      <ChannelInfoCard channelSlug={metric.channelSlug} />
    </div>
  );
}

function SalesBreakdownRow({ label, value, currency, isMoney = true }: { label: string; value: number; currency?: string; isMoney?: boolean }) {
  const formatted = isMoney && currency
    ? new Intl.NumberFormat('es-MX', { style: 'currency', currency, minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(value)
    : value.toLocaleString('es-ES');
  return (
    <div className="flex justify-between items-center py-1.5">
      <span className="text-xs text-muted-foreground">{label}</span>
      <span className="text-xs font-semibold text-foreground">{formatted}</span>
    </div>
  );
}

function SalesRateBadge({ label, value }: { label: string; value: number }) {
  const color = value > 20 ? 'text-red-600 dark:text-red-400' : value > 10 ? 'text-amber-600 dark:text-amber-400' : 'text-green-600 dark:text-green-400';
  return (
    <div className="flex justify-between items-center py-1">
      <span className="text-xs text-muted-foreground">{label}</span>
      <span className={`text-xs font-bold ${color}`}>{value.toFixed(1)}%</span>
    </div>
  );
}

function RevenueMetricDetail({ metric }: { metric: MetricClickData }) {
  const d = metric.extraData || {};
  const currency = metric.currency || 'USD';
  const grossRevenue = d.totalRevenue || 0;
  const netSales = d.netSales || 0;
  const orderCount = d.sqls || 0; // using sqls as proxy if order_count not separate
  const discountRate = orderCount > 0 ? ((d.discountUsageCount || 0) / orderCount * 100) : 0;
  const refundRate = orderCount > 0 ? ((d.refundCount || 0) / orderCount * 100) : 0;
  const netRatio = grossRevenue > 0 ? (netSales / grossRevenue * 100) : 100;

  return (
    <div className="space-y-4">
      <div className="rounded-md bg-green-50 dark:bg-green-950/20 border border-green-200 dark:border-green-800 p-3">
        <p className="text-xs text-green-700 dark:text-green-300 font-medium">
          Revenue — Desglose de ingresos
        </p>
        <p className="text-xs text-muted-foreground mt-1">
          Analisis detallado de ingresos brutos vs netos del periodo.
        </p>
      </div>

      {/* Net vs Gross */}
      <Card className="border-muted">
        <CardContent className="py-3 px-4 space-y-2">
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-widest">Ingresos Brutos vs Netos</p>
          <div className="flex items-center gap-3 mt-2">
            <div className="flex-1">
              <div className="h-2 rounded-full bg-muted overflow-hidden">
                <div className="h-full rounded-full bg-emerald-500" style={{ width: `${Math.min(netRatio, 100)}%` }} />
              </div>
            </div>
            <span className="text-xs font-bold text-emerald-600 dark:text-emerald-400">{netRatio.toFixed(1)}%</span>
          </div>
          <div className="flex justify-between text-[10px] text-muted-foreground mt-1">
            <span>Neto: {new Intl.NumberFormat('es-MX', { style: 'currency', currency, minimumFractionDigits: 0 }).format(netSales)}</span>
            <span>Bruto: {new Intl.NumberFormat('es-MX', { style: 'currency', currency, minimumFractionDigits: 0 }).format(grossRevenue)}</span>
          </div>
        </CardContent>
      </Card>

      {/* Breakdown */}
      <Card className="border-muted">
        <CardContent className="py-3 px-4">
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-widest mb-2">Desglose</p>
          <SalesBreakdownRow label="Descuentos" value={d.totalDiscounts || 0} currency={currency} />
          <SalesBreakdownRow label="Impuestos recaudados" value={d.totalTax || 0} currency={currency} />
          <SalesBreakdownRow label="Ingresos por envio" value={d.shippingRevenue || 0} currency={currency} />
          <SalesBreakdownRow label="Reembolsos" value={d.refundAmount || 0} currency={currency} />
          <Separator className="my-2" />
          <SalesRateBadge label="Tasa de descuento" value={discountRate} />
          <SalesRateBadge label="Tasa de devolucion" value={refundRate} />
        </CardContent>
      </Card>
      <ActionButtons stageId="VENTAS" channelSlug={metric.channelSlug} />
    </div>
  );
}

function CustomersMetricDetail({ metric }: { metric: MetricClickData }) {
  const d = metric.extraData || {};
  const newCustomers = d.newCustomers || 0;
  const repeatCustomers = d.repeatCustomers || 0;
  const repeatRate = newCustomers > 0 ? (repeatCustomers / newCustomers * 100) : 0;
  const currency = metric.currency || 'USD';
  const cac = d.cac || 0;

  return (
    <div className="space-y-4">
      <div className="rounded-md bg-green-50 dark:bg-green-950/20 border border-green-200 dark:border-green-800 p-3">
        <p className="text-xs text-green-700 dark:text-green-300 font-medium">
          Clientes — Nuevos vs recurrentes
        </p>
        <p className="text-xs text-muted-foreground mt-1">
          Analisis de la base de clientes del periodo.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-2">
        <Card className="border-muted bg-card shadow-sm">
          <CardContent className="p-3 flex flex-col items-center justify-center text-center">
            <span className="text-2xl font-bold text-foreground">{newCustomers.toLocaleString('es-ES')}</span>
            <span className="text-[10px] text-muted-foreground mt-1">Nuevos</span>
          </CardContent>
        </Card>
        <Card className="border-muted bg-card shadow-sm">
          <CardContent className="p-3 flex flex-col items-center justify-center text-center">
            <span className="text-2xl font-bold text-foreground">{repeatCustomers.toLocaleString('es-ES')}</span>
            <span className="text-[10px] text-muted-foreground mt-1">Recurrentes</span>
          </CardContent>
        </Card>
      </div>

      <Card className="border-muted">
        <CardContent className="py-3 px-4">
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-widest mb-2">Indicadores</p>
          <SalesBreakdownRow label="Tasa de recompra" value={repeatRate} isMoney={false} />
          <SalesBreakdownRow label="CAC promedio" value={cac} currency={currency} />
          {d.totalRevenue > 0 && newCustomers > 0 && (
            <SalesBreakdownRow label="Ticket promedio" value={d.totalRevenue / newCustomers} currency={currency} />
          )}
        </CardContent>
      </Card>
      <ActionButtons stageId="VENTAS" channelSlug={metric.channelSlug} />
    </div>
  );
}

function PipelineMetricDetail({ metric }: { metric: MetricClickData }) {
  const d = metric.extraData || {};
  const sqls = d.sqls || 0;
  const newCustomers = d.newCustomers || 0;
  const conversionRate = d.conversionRate || 0;

  return (
    <div className="space-y-4">
      <div className="rounded-md bg-green-50 dark:bg-green-950/20 border border-green-200 dark:border-green-800 p-3">
        <p className="text-xs text-green-700 dark:text-green-300 font-medium">
          Pipeline — Oportunidades a ventas
        </p>
        <p className="text-xs text-muted-foreground mt-1">
          Detalle de conversion del pipeline de ventas.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-2">
        <Card className="border-muted bg-card shadow-sm">
          <CardContent className="p-3 flex flex-col items-center justify-center text-center">
            <span className="text-2xl font-bold text-foreground">{sqls.toLocaleString('es-ES')}</span>
            <span className="text-[10px] text-muted-foreground mt-1">SQLs (Oportunidades)</span>
          </CardContent>
        </Card>
        <Card className="border-muted bg-card shadow-sm">
          <CardContent className="p-3 flex flex-col items-center justify-center text-center">
            <span className="text-2xl font-bold text-emerald-600 dark:text-emerald-500">{newCustomers.toLocaleString('es-ES')}</span>
            <span className="text-[10px] text-muted-foreground mt-1">Convertidos</span>
          </CardContent>
        </Card>
      </div>

      <Card className="border-muted">
        <CardContent className="py-3 px-4">
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-widest mb-2">Conversion</p>
          <div className="flex items-center gap-3 mt-1">
            <div className="flex-1">
              <div className="h-2 rounded-full bg-muted overflow-hidden">
                <div className="h-full rounded-full bg-emerald-500" style={{ width: `${Math.min(conversionRate, 100)}%` }} />
              </div>
            </div>
            <span className="text-xs font-bold text-emerald-600 dark:text-emerald-400">{conversionRate.toFixed(1)}%</span>
          </div>
          <p className="text-[10px] text-muted-foreground mt-2">
            {sqls - newCustomers > 0 ? `${(sqls - newCustomers).toLocaleString('es-ES')} oportunidades no convertidas` : 'Todas las oportunidades convertidas'}
          </p>
        </CardContent>
      </Card>
      <ActionButtons stageId="VENTAS" channelSlug={metric.channelSlug} />
    </div>
  );
}

function OfferRevenueDetail({ offerId, currency }: { offerId: string; currency: string }) {
  const { getToken } = useAuth();

  const { data, isLoading, error } = useQuery<OfferProductDetail>({
    queryKey: ['offer-products-detail', offerId],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error('No auth token');
      return getOfferProductsDetail(token, offerId);
    },
    staleTime: 2 * 60 * 1000,
  });

  if (isLoading) {
    return (
      <div className="space-y-3 animate-pulse">
        <div className="h-4 bg-muted rounded w-3/4" />
        <div className="h-20 bg-muted rounded" />
        <div className="h-20 bg-muted rounded" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="text-xs text-muted-foreground italic py-4 text-center">
        No se pudo cargar el detalle de la oferta.
      </div>
    );
  }

  const fmt = (value: number, cur?: string) =>
    new Intl.NumberFormat('es-MX', {
      style: 'currency',
      currency: cur || currency || 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);

  const archetypeLabels: Record<string, string> = {
    producto: 'Producto',
    programa: 'Programa',
    servicio: 'Servicio',
    membresia: 'Membresía',
    experiencia: 'Experiencia',
  };

  const sources = Object.entries(data.source_breakdown || {});
  const maxWeeklyRevenue = Math.max(...(data.weekly_revenue.map(w => w.revenue)), 1);

  return (
    <div className="space-y-4">
      {/* Section 1: Summary */}
      <div className="rounded-md bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-800 p-3">
        <p className="text-sm font-semibold text-emerald-800 dark:text-emerald-200">
          {data.offer_name || 'Oferta'}
        </p>
        {data.offer_type && (
          <Badge variant="secondary" className="mt-1 text-[10px]">
            {archetypeLabels[data.offer_type] || data.offer_type}
          </Badge>
        )}
      </div>

      <div className="grid grid-cols-2 gap-2">
        <Card className="border-muted bg-card shadow-sm">
          <CardContent className="p-3 flex flex-col items-center justify-center text-center">
            <ShoppingBag className="w-4 h-4 text-emerald-500 mb-1" />
            <span className="text-lg font-bold text-foreground">{fmt(data.total_revenue, data.currency)}</span>
            <span className="text-[10px] text-muted-foreground">Revenue Total</span>
          </CardContent>
        </Card>
        <Card className="border-muted bg-card shadow-sm">
          <CardContent className="p-3 flex flex-col items-center justify-center text-center">
            <Package className="w-4 h-4 text-blue-500 mb-1" />
            <span className="text-lg font-bold text-foreground">{data.sales_count}</span>
            <span className="text-[10px] text-muted-foreground">Ventas</span>
          </CardContent>
        </Card>
        <Card className="border-muted bg-card shadow-sm">
          <CardContent className="p-3 flex flex-col items-center justify-center text-center">
            <Users className="w-4 h-4 text-purple-500 mb-1" />
            <span className="text-lg font-bold text-foreground">{data.unique_customers}</span>
            <span className="text-[10px] text-muted-foreground">Clientes</span>
          </CardContent>
        </Card>
        <Card className="border-muted bg-card shadow-sm">
          <CardContent className="p-3 flex flex-col items-center justify-center text-center">
            <RefreshCw className="w-4 h-4 text-amber-500 mb-1" />
            <span className="text-lg font-bold text-foreground">{data.repeat_rate}%</span>
            <span className="text-[10px] text-muted-foreground">Recompra</span>
          </CardContent>
        </Card>
      </div>

      {/* Date range */}
      {(data.first_sale || data.last_sale) && (
        <p className="text-[10px] text-muted-foreground text-center">
          {data.first_sale && `Primera venta: ${new Date(data.first_sale).toLocaleDateString('es-MX')}`}
          {data.first_sale && data.last_sale && ' — '}
          {data.last_sale && `Última: ${new Date(data.last_sale).toLocaleDateString('es-MX')}`}
        </p>
      )}

      {/* Section 2: Weekly sparkline */}
      {data.weekly_revenue.length > 1 && (
        <Card className="border-muted">
          <CardContent className="py-3 px-4">
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-widest mb-2">
              Revenue Semanal (12 sem)
            </p>
            <div className="flex items-end gap-1 h-12">
              {data.weekly_revenue.map((w, i) => (
                <div
                  key={i}
                  className="flex-1 bg-emerald-400 dark:bg-emerald-600 rounded-t transition-all hover:bg-emerald-500"
                  style={{ height: `${Math.max((w.revenue / maxWeeklyRevenue) * 100, 4)}%` }}
                  title={`${w.week}: ${fmt(w.revenue, data.currency)}`}
                />
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Section 3: Source breakdown */}
      {sources.length > 0 && (
        <Card className="border-muted">
          <CardContent className="py-3 px-4">
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-widest mb-2">
              Ventas por Fuente
            </p>
            <div className="flex flex-wrap gap-1.5">
              {sources.map(([src, count]) => {
                let badgeClass = 'bg-slate-100 text-slate-700 border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700';
                if (src === 'SHOPIFY') badgeClass = 'bg-blue-50 text-blue-700 border-blue-100 dark:bg-blue-900/30 dark:text-blue-300 dark:border-blue-800';
                else if (src === 'AGENT') badgeClass = 'bg-purple-50 text-purple-700 border-purple-100 dark:bg-purple-900/30 dark:text-purple-300 dark:border-purple-800';
                return (
                  <span key={src} className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium border ${badgeClass}`}>
                    {src}: {count}
                  </span>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Section 4: Mapped products */}
      <div>
        <p className="text-xs font-medium text-muted-foreground uppercase tracking-widest mb-2">
          Productos Asociados (Shopify)
        </p>
        {data.products.length > 0 ? (
          <div className="space-y-2">
            {data.products.map((p) => (
              <Card key={p.external_id} className="border-muted">
                <CardContent className="py-3 px-4">
                  <p className="text-sm font-medium truncate">{p.external_name || `#${p.external_id}`}</p>
                  <div className="mt-2 space-y-1.5">
                    {/* Revenue bar */}
                    <div className="flex items-center gap-2">
                      <div className="flex-1">
                        <div className="h-1.5 rounded-full bg-muted overflow-hidden">
                          <div
                            className="h-full rounded-full bg-emerald-500"
                            style={{ width: `${Math.min(p.pct_of_total, 100)}%` }}
                          />
                        </div>
                      </div>
                      <span className="text-[10px] font-semibold text-emerald-600 dark:text-emerald-400 shrink-0">
                        {p.pct_of_total.toFixed(1)}%
                      </span>
                    </div>
                    <div className="grid grid-cols-3 gap-2 text-center">
                      <div>
                        <p className="text-xs font-bold">{fmt(p.total_revenue, p.currency || data.currency)}</p>
                        <p className="text-[9px] text-muted-foreground">Revenue</p>
                      </div>
                      <div>
                        <p className="text-xs font-bold">{p.quantity_sold}</p>
                        <p className="text-[9px] text-muted-foreground">Unidades</p>
                      </div>
                      <div>
                        <p className="text-xs font-bold">{p.transaction_count}</p>
                        <p className="text-[9px] text-muted-foreground">Transacciones</p>
                      </div>
                    </div>
                    <p className="text-[9px] text-muted-foreground text-center">
                      Precio prom: {fmt(p.avg_unit_price, p.currency || data.currency)}
                    </p>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <Card className="border-dashed">
            <CardContent className="py-3 px-4">
              <p className="text-xs text-muted-foreground italic">
                Las ventas de esta oferta provienen de {sources.map(([s]) => s).join(', ') || 'fuentes directas'}. No tiene productos Shopify asociados.
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}

function SalesMetricDetail({ metric }: { metric: MetricClickData }) {
  // Route to specialized detail based on metricName
  switch (metric.metricName) {
    case 'offer_detail':
      return <OfferRevenueDetail offerId={metric.channelSlug} currency={metric.currency || 'USD'} />;
    case 'revenue':
      return <RevenueMetricDetail metric={metric} />;
    case 'customers':
      return <CustomersMetricDetail metric={metric} />;
    case 'pipeline':
      return <PipelineMetricDetail metric={metric} />;
    default:
      return (
        <div className="space-y-4">
          <div className="rounded-md bg-green-50 dark:bg-green-950/20 border border-green-200 dark:border-green-800 p-3">
            <p className="text-xs text-green-700 dark:text-green-300 font-medium">
              Ventas — Revenue y clientes nuevos por oferta
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              Esta metrica mide el impacto economico de tu oferta en el periodo actual.
            </p>
          </div>
          <ActionButtons stageId="VENTAS" channelSlug={metric.channelSlug} />
        </div>
      );
  }
}

function AdoptionMetricDetail({ metric }: { metric: MetricClickData }) {
  return (
    <div className="space-y-4">
      <div className="rounded-md bg-cyan-50 dark:bg-cyan-950/20 border border-cyan-200 dark:border-cyan-800 p-3">
        <p className="text-xs text-cyan-700 dark:text-cyan-300 font-medium">
          Adopcion — Salud y activacion de clientes existentes
        </p>
        <p className="text-xs text-muted-foreground mt-1">
          Esta metrica mide el porcentaje de clientes que estan usando activamente tu producto/servicio.
        </p>
      </div>
      <Card className="border-dashed">
        <CardContent className="py-3 px-4">
          <p className="text-xs text-muted-foreground font-medium mb-2">Detalle de activacion por oferta</p>
          <p className="text-xs text-muted-foreground italic">
            Historial de activacion — proxima version
          </p>
        </CardContent>
      </Card>
      <ActionButtons stageId="ADOPCION" channelSlug={metric.channelSlug} />
    </div>
  );
}

function ExpansionMetricDetail({ metric }: { metric: MetricClickData }) {
  let title = 'Expansion — Ingreso recurrente, upsell y cancelaciones';
  let desc = 'Esta metrica refleja el movimiento neto de MRR en el periodo actual.';
  let analysisTitle = 'Análisis de oportunidad';
  let analysisDesc = 'La inteligencia del sistema ha detectado que existe una gran oportunidad de optimización realizando acciones de retención o upsell.';
  
  if (metric.metricName === 'retencion') {
    title = 'Optimizar Retención';
    desc = 'Mantén la fidelidad de tus clientes activos.';
    analysisDesc = 'Enviar correo de agradecimiento y contenido exclusivo a los retenidos para asegurar el próximo mes.';
  } else if (metric.metricName === 'crecimiento') {
    title = 'Lanzar Campaña de Upsell';
    desc = 'Aumenta el LTV ofreciendo productos de mayor valor.';
    analysisDesc = 'Lanzar un correo promocional automatizado a la base de clientes actuales para ofrecer este producto adicional.';
  } else if (metric.metricName === 'cancelaciones') {
    title = 'Entrevistas de Salida';
    desc = 'Descubre por qué tus clientes están cancelando.';
    analysisDesc = 'Configurar un flujo automático por WhatsApp con la IA para preguntar por qué cancelaron y ofrecer un downsell.';
  }

  return (
    <div className="space-y-4">
      <div className="rounded-md bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 p-3">
        <p className="text-xs text-amber-700 dark:text-amber-300 font-medium">
          {title}
        </p>
        <p className="text-xs text-muted-foreground mt-1">
          {desc}
        </p>
      </div>

      <div className="bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-100 dark:border-emerald-900/50 rounded-lg p-4">
        <h4 className="text-sm font-semibold text-emerald-900 dark:text-emerald-200 border-b border-emerald-200 dark:border-emerald-800 pb-2 mb-2 flex items-center">
          <TrendingUp className="w-4 h-4 mr-1" /> {analysisTitle}
        </h4>
        <p className="text-xs text-slate-600 dark:text-slate-400 mb-4">
          {analysisDesc}
        </p>
      </div>

      <ActionButtons stageId="EXPANSION" channelSlug={metric.channelSlug} />
    </div>
  );
}

function EvangelizationMetricDetail({ metric }: { metric: MetricClickData }) {
  let title = 'Evangelizacion — K-Factor, referidos y NPS';
  let desc = 'Esta metrica mide el impacto viral de tus clientes mas satisfechos.';
  let analysisTitle = 'Análisis de oportunidad';
  let analysisDesc = 'Identifica a tus promotores para generar referidos y contenido UGC.';
  
  if (metric.metricName === 'setup_nps') {
    title = 'Configurar NPS';
    desc = 'Aún no tienes información de referidos.';
    analysisDesc = 'Lanza tu primera encuesta NPS a tus clientes activos para conocer su satisfacción.';
  } else if (metric.metricName === 'promotores') {
    title = 'Solicitar Testimonios';
    desc = 'Aprovecha la alta satisfacción de tus clientes.';
    analysisDesc = 'Envía un flujo automático por WhatsApp pidiendo un video testimonio a cambio de un bonus.';
  } else if (metric.metricName === 'ugc_count') {
    title = 'Aprovechar UGC';
    desc = 'Utiliza el contenido generado por tus usuarios.';
    analysisDesc = 'Recopila estas menciones y reseñas en redes para inyectarlas en tus Ads de retargeting.';
  } else if (metric.metricName === 'conversions') {
    title = 'Optimizar Referidos';
    desc = 'Mejora el rendimiento de tus enlaces compartidos.';
    analysisDesc = 'Mejora la recompensa por referir. Ofrece comisión recurrente para subir el K-Factor a más de 1.0.';
  } else if (metric.metricName === 'count') {
    title = 'Obtener Candidatos / Activar Evangelistas';
    desc = 'Invita a tus promotores a unirse al programa de referidos.';
    analysisDesc = 'La IA puede invitarles a unirse al programa de referidos de forma automatizada.';
  }

  return (
    <div className="space-y-4">
      <div className="rounded-md bg-fuchsia-50 dark:bg-fuchsia-950/20 border border-fuchsia-200 dark:border-fuchsia-800 p-3">
        <p className="text-xs text-fuchsia-700 dark:text-fuchsia-300 font-medium">
          {title}
        </p>
        <p className="text-xs text-muted-foreground mt-1">
          {desc}
        </p>
      </div>

      <div className="bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-100 dark:border-emerald-900/50 rounded-lg p-4">
        <h4 className="text-sm font-semibold text-emerald-900 dark:text-emerald-200 border-b border-emerald-200 dark:border-emerald-800 pb-2 mb-2 flex items-center">
          <TrendingUp className="w-4 h-4 mr-1" /> {analysisTitle}
        </h4>
        <p className="text-xs text-slate-600 dark:text-slate-400 mb-4">
          {analysisDesc}
        </p>
      </div>

      <ActionButtons stageId="EVANGELIZACION" channelSlug={metric.channelSlug} />
    </div>
  );
}

function DefaultMetricDetail({ metric }: { metric: MetricClickData }) {
  return (
    <div className="space-y-4">
      <Card className="border-dashed">
        <CardContent className="py-3 px-4">
          <p className="text-xs text-muted-foreground font-medium mb-2">Informacion de la metrica</p>
          <p className="text-xs text-muted-foreground italic">
            Detalles adicionales — proxima version
          </p>
        </CardContent>
      </Card>
      <ActionButtons stageId={null} channelSlug={metric.channelSlug} />
      {metric.channelSlug && <ChannelInfoCard channelSlug={metric.channelSlug} />}
    </div>
  );
}

// ─── Main polymorphic component ────────────────────────────────────────────────

/**
 * SidebarContent — Polymorphic content adapter for MetricSidebar.
 *
 * Renders stage-specific metric context (description, campaign placeholders,
 * action CTAs, channel info) based on the stageId of the clicked metric.
 *
 * Architecture: Each stage has its own detail component (AttractionMetricDetail,
 * CaptureMetricDetail, etc.) that can be enriched independently as backend APIs
 * grow. This component acts as the switch/router.
 */
export function SidebarContent({ metric, stageId }: SidebarContentProps) {
  if (!metric || !stageId) {
    return (
      <div className="text-sm text-muted-foreground py-4 text-center">
        Selecciona una metrica para ver el detalle.
      </div>
    );
  }

  const metricLabel = METRIC_LABELS[metric.metricName] ?? metric.metricName;

  return (
    <div className="space-y-4">
      {/* Metric context header */}
      <div className="space-y-1">
        <p className="text-xs uppercase tracking-widest text-muted-foreground font-medium">
          {metric.channelName ? 'Canal' : 'Metrica'}
        </p>
        <p className="text-sm font-semibold">{metric.channelName || metricLabel}</p>
        <p className="text-xs text-muted-foreground">
          {metric.channelName ? `Metrica principal: ${metricLabel}` : `Canal: ${metric.channelSlug}`} &mdash; Etapa: {STAGE_NAMES[stageId]}
        </p>
      </div>

      <Separator />

      {/* Stage-specific content */}
      {(() => {
        switch (stageId) {
          case 'ATRACCION':
            return <AttractionMetricDetail metric={metric} />;
          case 'CAPTURA':
            return <CaptureMetricDetail metric={metric} />;
          case 'NUTRICION':
            return <NurtureMetricDetail metric={metric} />;
          case 'OPORTUNIDAD':
            return <OpportunityMetricDetail metric={metric} />;
          case 'VENTAS':
            return <SalesMetricDetail metric={metric} />;
          case 'ADOPCION':
            return <AdoptionMetricDetail metric={metric} />;
          case 'EXPANSION':
            return <ExpansionMetricDetail metric={metric} />;
          case 'EVANGELIZACION':
            return <EvangelizationMetricDetail metric={metric} />;
          default:
            return <DefaultMetricDetail metric={metric} />;
        }
      })()}
    </div>
  );
}
