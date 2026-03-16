'use client';

import type { ReactNode } from 'react';
import { X, TrendingUp, Info } from 'lucide-react';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetClose,
} from '@/components/ui/sheet';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import type { MetricClickData } from '../../types/metrics';

interface MetricSidebarProps {
  /** Whether the sidebar sheet is open */
  isOpen: boolean;
  /** Callback to close the sidebar */
  onClose: () => void;
  /** The metric that was clicked to open this sidebar, or null if nothing selected */
  metric: MetricClickData | null;
  /**
   * Optional children rendered below the current-value section.
   * Used to inject SidebarContent (polymorphic per-stage content adapters) from Plan 11-02.
   */
  children?: ReactNode;
}

/**
 * Right-side action sidebar for metric drill-down.
 *
 * Framework component — renders metric name and current value.
 * Per-metric content adapters (SidebarContent) will be added in Plan 11-02.
 * The sidebar uses shadcn Sheet with side="right" and 400px desktop width.
 */
export default function MetricSidebar({ isOpen, onClose, metric, children }: MetricSidebarProps) {
  const hasMetric = metric != null;

  function formatValue(value: number, currency?: string): string {
    if (currency) {
      return new Intl.NumberFormat('es-MX', {
        style: 'currency',
        currency,
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
      }).format(value);
    }
    if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
    if (value >= 1_000) return `${(value / 1_000).toFixed(1)}k`;
    return value.toLocaleString('es-MX');
  }

  return (
    <Sheet open={isOpen} onOpenChange={(open) => { if (!open) onClose(); }}>
      <SheetContent
        side="right"
        className="w-full sm:w-[400px] sm:max-w-[400px] overflow-y-auto"
      >
        <SheetHeader className="flex flex-row items-start justify-between pr-0">
          <div className="space-y-1">
            <SheetTitle className="text-base font-semibold leading-tight">
              {hasMetric
                ? `${metric.channelSlug} — ${metric.metricName} detalle`
                : 'Detalle de metrica'}
            </SheetTitle>
            {hasMetric && (
              <p className="text-xs text-muted-foreground capitalize">
                Etapa: {metric.stageId.toLowerCase()}
              </p>
            )}
          </div>
          <SheetClose asChild>
            <Button variant="ghost" size="icon" className="h-7 w-7 flex-shrink-0">
              <X className="h-4 w-4" />
              <span className="sr-only">Cerrar</span>
            </Button>
          </SheetClose>
        </SheetHeader>

        <Separator className="my-4" />

        {!hasMetric ? (
          <div className="flex flex-col items-center justify-center py-12 text-center gap-3">
            <Info className="h-8 w-8 text-muted-foreground" />
            <p className="text-sm text-muted-foreground">
              Selecciona una metrica para ver el detalle.
            </p>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Current value — large display */}
            <div className="space-y-1">
              <p className="text-xs uppercase tracking-widest text-muted-foreground font-medium">
                Valor actual
              </p>
              <div className="flex items-end gap-2">
                <span className="text-4xl font-bold tabular-nums">
                  {formatValue(metric.currentValue, metric.currency)}
                </span>
                <TrendingUp className="h-5 w-5 text-muted-foreground mb-1" />
              </div>
              {metric.lastUpdated && (
                <p className="text-[10px] text-muted-foreground">
                  Actualizado:{' '}
                  {new Date(metric.lastUpdated).toLocaleDateString('es-ES', {
                    day: 'numeric',
                    month: 'short',
                    year: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </p>
              )}
            </div>

            <Separator />

            {/* Sparkline placeholder — Plan 11-02 TODO */}
            <div className="space-y-2">
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-widest">
                Tendencia
              </p>
              {/* TODO (Plan 11-02): Add sparkline chart using recharts or similar */}
              <div className="h-16 rounded-md bg-muted/50 flex items-center justify-center">
                <span className="text-xs text-muted-foreground">
                  Grafica de tendencia — proxima version
                </span>
              </div>
            </div>

            <Separator />

            {/* Per-stage polymorphic content (SidebarContent injected from MetricsDashboard) */}
            {children ? (
              children
            ) : (
              <>
                {/* Fallback action buttons — shown when no SidebarContent children provided */}
                <div className="space-y-3">
                  <p className="text-xs font-medium text-muted-foreground uppercase tracking-widest">
                    Acciones
                  </p>

                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full justify-start gap-2"
                    disabled
                  >
                    <Badge variant="secondary" className="text-[10px] px-1.5 py-0 mr-1">
                      Pronto
                    </Badge>
                    Crear campana relacionada
                  </Button>

                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full justify-start gap-2"
                    disabled
                  >
                    <Badge variant="secondary" className="text-[10px] px-1.5 py-0 mr-1">
                      Pronto
                    </Badge>
                    Editar configuracion del canal
                  </Button>

                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full justify-start gap-2"
                    disabled
                  >
                    <Badge variant="secondary" className="text-[10px] px-1.5 py-0 mr-1">
                      Pronto
                    </Badge>
                    Ver historial de cambios
                  </Button>
                </div>

                {/* Connection state info */}
                <div className="rounded-md bg-muted/30 p-3 space-y-1">
                  <p className="text-xs text-muted-foreground font-medium">Canal</p>
                  <p className="text-sm font-mono">{metric.channelSlug}</p>
                </div>
              </>
            )}
          </div>
        )}
      </SheetContent>
    </Sheet>
  );
}
