'use client';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { ExternalLink, PlusCircle, Settings } from 'lucide-react';
import type { MetricClickData, StageId } from '../../../types/metrics';
import { getChannelColor, getChannelIcon } from '../../../lib/channelIcons';

interface SidebarContentProps {
  /** The metric that was clicked; null if sidebar was opened without context */
  metric: MetricClickData | null;
  /** Stage context determines which specialized content adapter to render */
  stageId: StageId | null;
}

// ─── Stage label mapping ───────────────────────────────────────────────────────

const STAGE_NAMES: Record<StageId, string> = {
  ATRACCION: 'Atraccion',
  CAPTURA: 'Captura',
  NUTRICION: 'Nutricion',
  OPORTUNIDAD: 'Oportunidad',
  VENTAS: 'Ventas',
  ADOPCION: 'Adopcion',
  EXPANSION: 'Expansion',
  EVANGELIZACION: 'Evangelizacion',
};

const METRIC_LABELS: Record<string, string> = {
  reach: 'Alcance',
  engagement: 'Engagement',
  sessions: 'Sesiones',
  users: 'Usuarios',
  clicks: 'Clicks',
  conversions: 'Conversiones',
  spend: 'Gasto',
  contacts: 'Contactos',
  responses: 'Respuestas',
  leads: 'Leads',
  cost: 'Costo',
  conversion_rate: 'Conversion',
  conversations: 'Conversaciones',
  emails_sent: 'Enviados',
  open_rate: 'Apertura',
  click_rate: 'Clicks por email',
  followups: 'Follow-ups',
  response_rate: 'Tasa de respuesta',
  campaigns: 'Campanas',
  count: 'Cantidad',
  value: 'Valor',
  abandonment_rate: 'Tasa de abandono',
  booked: 'Citas agendadas',
  completed: 'Completadas',
  no_show: 'No-Show',
  rescheduled: 'Reprogramadas',
  attendance_rate: 'Asistencia',
  impressions: 'Impresiones',
  visitors: 'Visitantes',
  total_leads: 'Total Leads',
  total_mqls: 'Total MQLs',
  total_sqls: 'Total SQLs',
  revenue: 'Revenue',
  health_pct: 'Salud del Cliente',
  net_mrr: 'Ingreso Recurrente Neto',
  k_factor: 'K-Factor',
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

interface ChannelInfoCardProps {
  channelSlug: string;
}

function ChannelInfoCard({ channelSlug }: ChannelInfoCardProps) {
  const Icon = getChannelIcon(channelSlug);
  const iconColor = getChannelColor(channelSlug);

  return (
    <Card className="border-muted">
      <CardContent className="py-3 px-4 space-y-2">
        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
          Canal
        </p>
        <div className="flex items-center gap-2">
          <Icon className="w-4 h-4 flex-shrink-0" style={{ color: iconColor }} aria-hidden="true" />
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
  return (
    <div className="space-y-4">
      <div className="rounded-md bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800 p-3">
        <p className="text-xs text-blue-700 dark:text-blue-300 font-medium">
          Atraccion — Trafico y alcance de canales organicos y pagados
        </p>
        <p className="text-xs text-muted-foreground mt-1">
          Esta metrica mide el volumen de personas que llegan a tu ecosistema a traves de {metric.channelSlug}.
        </p>
      </div>
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
  return (
    <div className="space-y-4">
      <div className="rounded-md bg-purple-50 dark:bg-purple-950/20 border border-purple-200 dark:border-purple-800 p-3">
        <p className="text-xs text-purple-700 dark:text-purple-300 font-medium">
          Captura — Leads generados desde formularios y agentes conversacionales
        </p>
        <p className="text-xs text-muted-foreground mt-1">
          Esta metrica mide cuantos visitantes se convirtieron en contactos capturados via {metric.channelSlug}.
        </p>
      </div>
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
  return (
    <div className="space-y-4">
      <div className="rounded-md bg-pink-50 dark:bg-pink-950/20 border border-pink-200 dark:border-pink-800 p-3">
        <p className="text-xs text-pink-700 dark:text-pink-300 font-medium">
          Nutricion — MQLs calificados por retargeting y automatizaciones
        </p>
        <p className="text-xs text-muted-foreground mt-1">
          Esta metrica mide leads que alcanzaron calificacion de marketing (MQL) via {metric.channelSlug}.
        </p>
      </div>
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
  return (
    <div className="space-y-4">
      <div className="rounded-md bg-orange-50 dark:bg-orange-950/20 border border-orange-200 dark:border-orange-800 p-3">
        <p className="text-xs text-orange-700 dark:text-orange-300 font-medium">
          Oportunidad — SQLs listos para decision de compra
        </p>
        <p className="text-xs text-muted-foreground mt-1">
          Esta metrica mide leads que llegaron a checkout o calificacion via {metric.channelSlug}.
        </p>
      </div>
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

function SalesMetricDetail({ metric }: { metric: MetricClickData }) {
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
      <Card className="border-dashed">
        <CardContent className="py-3 px-4">
          <p className="text-xs text-muted-foreground font-medium mb-2">Desglose por oferta</p>
          <p className="text-xs text-muted-foreground italic">
            Detalle de ventas por producto — proxima version
          </p>
        </CardContent>
      </Card>
      <ActionButtons stageId="VENTAS" channelSlug={metric.channelSlug} />
    </div>
  );
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
  return (
    <div className="space-y-4">
      <div className="rounded-md bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 p-3">
        <p className="text-xs text-amber-700 dark:text-amber-300 font-medium">
          Expansion — Ingreso recurrente, upsell y cancelaciones
        </p>
        <p className="text-xs text-muted-foreground mt-1">
          Esta metrica refleja el movimiento neto de MRR en el periodo actual.
        </p>
      </div>
      <Card className="border-dashed">
        <CardContent className="py-3 px-4">
          <p className="text-xs text-muted-foreground font-medium mb-2">Detalle de MRR por producto</p>
          <p className="text-xs text-muted-foreground italic">
            Detalle de expansion — proxima version
          </p>
        </CardContent>
      </Card>
      <ActionButtons stageId="EXPANSION" channelSlug={metric.channelSlug} />
    </div>
  );
}

function EvangelizationMetricDetail({ metric }: { metric: MetricClickData }) {
  return (
    <div className="space-y-4">
      <div className="rounded-md bg-fuchsia-50 dark:bg-fuchsia-950/20 border border-fuchsia-200 dark:border-fuchsia-800 p-3">
        <p className="text-xs text-fuchsia-700 dark:text-fuchsia-300 font-medium">
          Evangelizacion — K-Factor, referidos y NPS
        </p>
        <p className="text-xs text-muted-foreground mt-1">
          Esta metrica mide el impacto viral de tus clientes mas satisfechos.
        </p>
      </div>
      <Card className="border-dashed">
        <CardContent className="py-3 px-4">
          <p className="text-xs text-muted-foreground font-medium mb-2">Detalle de evangelistas</p>
          <p className="text-xs text-muted-foreground italic">
            Historial de referidos — proxima version
          </p>
        </CardContent>
      </Card>
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
          Metrica
        </p>
        <p className="text-sm font-semibold">{metricLabel}</p>
        <p className="text-xs text-muted-foreground">
          Canal: {metric.channelSlug} &mdash; Etapa: {STAGE_NAMES[stageId]}
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
