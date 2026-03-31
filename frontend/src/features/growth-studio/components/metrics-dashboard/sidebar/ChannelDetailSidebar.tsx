'use client';

import { useEffect, useState } from 'react';
import { useAuth } from '@clerk/nextjs';
import {
  RefreshCw,
  Settings,
  Unplug,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Calendar,
  Database,
  Clock,
} from 'lucide-react';
import {
  DetailPanel,
  DetailPanelHeader,
  DetailPanelTitle,
  DetailPanelClose,
} from '@/components/ui/detail-panel';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { cn } from '@/lib/utils';
import type { ChannelMetric, MetricValue } from '../../../types/metrics';
import { getChannelIcon, getChannelColor } from '../../../lib/channelIcons';
import { connectionsApi, type ChannelInfoResponse } from '@/lib/api/connections';

/** Metric name -> Spanish label. */
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
  impressions: 'Impresiones',
  bounceRate: 'Tasa de Rebote',
  engagedSessions: 'Sesiones Activas',
  newUsers: 'Nuevos Usuarios',
  screenPageViews: 'Vistas de Página',
  ctr: 'CTR',
  cpm: 'CPM',
  cpc: 'CPC',
  frequency: 'Frecuencia',
};

function formatNumber(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1000) return `${(n / 1000).toFixed(n >= 10000 ? 0 : 1)}k`;
  return n.toLocaleString('es-ES');
}

function formatCurrency(n: number, currency?: string): string {
  const symbol = currency === 'USD' || !currency ? '$' : currency;
  return `${symbol}${n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function hexToRgba(hex: string, alpha: number): string {
  if (hex.startsWith('hsl')) return hex;
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r},${g},${b},${alpha})`;
}

function timeAgo(isoDate: string): string {
  const now = Date.now();
  const then = new Date(isoDate).getTime();
  const diff = now - then;
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `hace ${mins}m`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `hace ${hours}h`;
  const days = Math.floor(hours / 24);
  return `hace ${days}d`;
}

interface ChannelDetailSidebarProps {
  isOpen: boolean;
  onClose: () => void;
  channel: ChannelMetric | null;
}

export default function ChannelDetailSidebar({ isOpen, onClose, channel }: ChannelDetailSidebarProps) {
  const { getToken } = useAuth();
  const [info, setInfo] = useState<ChannelInfoResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const providerName = channel?.providerName;

  useEffect(() => {
    if (!isOpen || !providerName) {
      setInfo(null);
      return;
    }

    let cancelled = false;
    async function fetchInfo() {
      setLoading(true);
      setError(null);
      try {
        const token = await getToken();
        if (!token || cancelled) return;
        const data = await connectionsApi.getChannelInfo(providerName!, token);
        if (!cancelled) setInfo(data);
      } catch (e: unknown) {
        if (!cancelled) setError(e instanceof Error ? e.message : 'Error cargando info');
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchInfo();
    return () => { cancelled = true; };
  }, [isOpen, providerName, getToken]);

  if (!channel) return null;

  const Icon = getChannelIcon(channel.slug);
  const iconColor = getChannelColor(channel.slug);

  return (
    <DetailPanel open={isOpen} onClose={onClose}>
      <DetailPanelHeader className="flex flex-row items-start justify-between pr-6">
        <div className="flex items-center gap-3">
          <div
            className="flex items-center justify-center w-10 h-10 rounded-lg shrink-0"
            style={{ backgroundColor: hexToRgba(iconColor, 0.12) }}
          >
            <Icon className="w-5 h-5" style={{ color: iconColor }} />
          </div>
          <div className="space-y-0.5">
            <DetailPanelTitle className="text-base font-semibold leading-tight">
              {channel.name}
            </DetailPanelTitle>
            <p className="text-xs text-muted-foreground">
              {channel.subSources && channel.subSources.length > 1
                ? channel.subSources.map((s) => s.name).join(' + ')
                : channel.sourceDisplayName
                  ? `${channel.sourceLabel} · ${channel.sourceDisplayName}`
                  : channel.sourceLabel}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {channel.connected && (
            <Badge variant="outline" className="border-emerald-500/50 text-emerald-600 dark:text-emerald-400 text-[10px]">
              <CheckCircle2 className="w-3 h-3 mr-1" />
              Conectado
            </Badge>
          )}
          <DetailPanelClose onClose={onClose} className="flex-shrink-0" />
        </div>
      </DetailPanelHeader>

      <div className="px-6 pb-6">
        <Separator className="my-4" />

        {loading && (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            <span className="ml-2 text-sm text-muted-foreground">Cargando detalles...</span>
          </div>
        )}

        {error && (
          <div className="flex items-center gap-2 py-4 text-sm text-red-500">
            <AlertCircle className="h-4 w-4" />
            {error}
          </div>
        )}

        {!loading && !error && (
          <div className="space-y-5">
            {/* Connection Details */}
            {info && info.is_connected && (
              <section>
                <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-widest mb-3">
                  Detalles de Conexión
                </h3>
                <div className="space-y-2 text-sm">
                  {info.display_name && (
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Nombre</span>
                      <span className="font-medium">{info.display_name}</span>
                    </div>
                  )}
                  {info.account_name && info.account_name !== info.display_name && (
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Cuenta</span>
                      <span className="font-medium">{info.account_name}</span>
                    </div>
                  )}
                  {/* Provider-specific details */}
                  {Object.entries(info.details).map(([key, val]) => {
                    if (!val || key === 'granted_permissions' || key === 'statistics') return null;
                    if (typeof val === 'boolean') {
                      return (
                        <div key={key} className="flex justify-between">
                          <span className="text-muted-foreground">{key.replace(/_/g, ' ')}</span>
                          <Badge variant={val ? 'default' : 'secondary'} className="text-[10px]">
                            {val ? 'Sí' : 'No'}
                          </Badge>
                        </div>
                      );
                    }
                    return (
                      <div key={key} className="flex justify-between">
                        <span className="text-muted-foreground capitalize">{key.replace(/_/g, ' ')}</span>
                        <span className="font-mono text-xs">{String(val)}</span>
                      </div>
                    );
                  })}
                  {/* YouTube statistics */}
                  {info.details.statistics && typeof info.details.statistics === 'object' && (
                    <div className="mt-2 grid grid-cols-3 gap-2">
                      {Object.entries(info.details.statistics as Record<string, string>).map(([k, v]) => (
                        <div key={k} className="text-center p-2 rounded-md bg-muted/50">
                          <p className="text-xs font-semibold tabular-nums">{Number(v).toLocaleString('es-ES')}</p>
                          <p className="text-[10px] text-muted-foreground capitalize">{k.replace('Count', '')}</p>
                        </div>
                      ))}
                    </div>
                  )}
                  {!info.is_configured && (
                    <div className="flex items-center gap-2 text-amber-600 dark:text-amber-400 mt-1">
                      <AlertCircle className="h-3.5 w-3.5" />
                      <span className="text-xs">Requiere configuración adicional</span>
                    </div>
                  )}
                </div>
              </section>
            )}

            {/* Meta children */}
            {info && info.children && info.children.length > 0 && (
              <>
                <Separator />
                <section>
                  <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-widest mb-3">
                    Activos
                  </h3>
                  <div className="space-y-1.5">
                    {info.children.map((child, idx) => (
                      <div
                        key={`${child.channel_type}-${child.asset_id}-${idx}`}
                        className="flex items-center justify-between py-1.5 px-2 rounded-md bg-muted/30 text-sm"
                      >
                        <div className="flex items-center gap-2 min-w-0">
                          <span className={cn(
                            'w-1.5 h-1.5 rounded-full shrink-0',
                            child.is_active ? 'bg-emerald-400' : 'bg-gray-400',
                          )} />
                          <span className="truncate">{child.name || child.asset_id}</span>
                        </div>
                        <span className="text-[10px] text-muted-foreground uppercase shrink-0">
                          {(child.channel_type as string).replace('_', ' ')}
                        </span>
                      </div>
                    ))}
                  </div>
                </section>
              </>
            )}

            {/* Data Freshness */}
            {info && (info.last_extraction || info.data_range) && (
              <>
                <Separator />
                <section>
                  <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-widest mb-3">
                    Datos
                  </h3>
                  <div className="space-y-2 text-sm">
                    {info.last_extraction && (
                      <>
                        <div className="flex justify-between items-center">
                          <span className="text-muted-foreground flex items-center gap-1.5">
                            <Clock className="h-3.5 w-3.5" />
                            Última sincronización
                          </span>
                          <div className="flex items-center gap-1.5">
                            <span className="font-medium">
                              {info.last_extraction.completed_at
                                ? timeAgo(info.last_extraction.completed_at)
                                : 'En progreso'}
                            </span>
                            {info.last_extraction.status === 'success' && (
                              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
                            )}
                            {info.last_extraction.status === 'failed' && (
                              <AlertCircle className="h-3.5 w-3.5 text-red-500" />
                            )}
                          </div>
                        </div>
                        {info.last_extraction.metrics_count != null && info.last_extraction.metrics_count > 0 && (
                          <div className="flex justify-between">
                            <span className="text-muted-foreground flex items-center gap-1.5">
                              <Database className="h-3.5 w-3.5" />
                              Métricas cargadas
                            </span>
                            <span className="font-medium">{info.last_extraction.metrics_count}</span>
                          </div>
                        )}
                        {info.last_extraction.error && (
                          <div className="text-xs text-red-500 bg-red-50 dark:bg-red-950/20 p-2 rounded-md">
                            {info.last_extraction.error}
                          </div>
                        )}
                      </>
                    )}
                    {info.data_range && (
                      <div className="flex justify-between items-center">
                        <span className="text-muted-foreground flex items-center gap-1.5">
                          <Calendar className="h-3.5 w-3.5" />
                          Rango de datos
                        </span>
                        <span className="font-medium text-xs">
                          {new Date(info.data_range.min_date).toLocaleDateString('es-ES', { day: 'numeric', month: 'short' })}
                          {' — '}
                          {new Date(info.data_range.max_date).toLocaleDateString('es-ES', { day: 'numeric', month: 'short', year: 'numeric' })}
                        </span>
                      </div>
                    )}
                  </div>
                </section>
              </>
            )}

            {/* Sub-source breakdown (unified channels like IG DM = Meta + ManyChat) */}
            {channel.subSources && channel.subSources.length > 1 && (
              <>
                <Separator />
                <section>
                  <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-widest mb-3">
                    Fuentes de Datos
                  </h3>
                  <div className="space-y-1.5">
                    {channel.subSources.map((src, idx) => (
                      <div
                        key={src.name}
                        className="flex items-center justify-between py-2 px-3 rounded-md bg-muted/30 text-sm"
                      >
                        <div className="flex items-center gap-2">
                          <span className={cn(
                            'w-2 h-2 rounded-full shrink-0',
                            idx === 0 ? 'bg-blue-400' : 'bg-violet-400',
                          )} />
                          <span className="font-medium">{src.name}</span>
                        </div>
                        <div className="flex items-center gap-3 text-xs">
                          <span className="tabular-nums">{formatNumber(src.leads)} leads</span>
                          {src.conversations > 0 && (
                            <span className="text-muted-foreground tabular-nums">{formatNumber(src.conversations)} conv</span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </section>
              </>
            )}

            {/* All Metrics */}
            {channel.metrics && channel.metrics.length > 0 && (
              <>
                <Separator />
                <section>
                  <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-widest mb-3">
                    Métricas Actuales
                  </h3>
                  <div className="space-y-2">
                    {channel.metrics.map((m: MetricValue) => {
                      const label = METRIC_LABELS[m.name] ?? m.name;
                      const isCurrency = m.unit === 'currency';
                      const formatted = isCurrency
                        ? formatCurrency(m.value, m.currency)
                        : formatNumber(m.value);

                      return (
                        <div key={m.name} className="space-y-1">
                          <div className="flex items-center justify-between">
                            <span className="text-sm text-muted-foreground">{label}</span>
                            <span className="text-sm font-semibold tabular-nums">{formatted}</span>
                          </div>
                          {m.breakdown && Object.keys(m.breakdown).length > 0 && (
                            <div className="flex gap-2 pl-2">
                              {Object.entries(m.breakdown).filter(([, v]) => v > 0).map(([key, val]) => (
                                <span key={key} className="text-[10px] text-muted-foreground">
                                  {key} {formatNumber(val)}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </section>
              </>
            )}

            {/* Trend placeholder */}
            <Separator />
            <section>
              <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-widest mb-3">
                Tendencia
              </h3>
              <div className="h-16 rounded-md bg-muted/50 flex items-center justify-center">
                <span className="text-xs text-muted-foreground">
                  Gráfica de tendencia — próxima versión
                </span>
              </div>
            </section>

            {/* Actions */}
            <Separator />
            <section className="space-y-2">
              <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-widest mb-3">
                Acciones
              </h3>
              <Button variant="outline" size="sm" className="w-full justify-start gap-2" disabled>
                <RefreshCw className="h-3.5 w-3.5" />
                Sincronizar ahora
                <Badge variant="secondary" className="text-[10px] px-1.5 py-0 ml-auto">Pronto</Badge>
              </Button>
              <Button variant="outline" size="sm" className="w-full justify-start gap-2" disabled>
                <Settings className="h-3.5 w-3.5" />
                Configurar
                <Badge variant="secondary" className="text-[10px] px-1.5 py-0 ml-auto">Pronto</Badge>
              </Button>
              <Button variant="outline" size="sm" className="w-full justify-start gap-2 text-red-500 hover:text-red-600" disabled>
                <Unplug className="h-3.5 w-3.5" />
                Desconectar
                <Badge variant="secondary" className="text-[10px] px-1.5 py-0 ml-auto">Pronto</Badge>
              </Button>
            </section>
          </div>
        )}
      </div>
    </DetailPanel>
  );
}
