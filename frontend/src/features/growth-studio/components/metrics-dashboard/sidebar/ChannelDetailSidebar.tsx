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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { cn } from '@/lib/utils';
import { formatMoney } from '@/lib/format-money';
import { useTenantLocale } from '@/features/tenant/context/tenant-locale-context';
import { formatTenantDate } from '@/lib/format-date';
import type { ChannelMetric, MetricValue } from '../../../types/metrics';
import { getChannelIcon, getChannelColor } from '../../../lib/channelIcons';
import { METRIC_LABELS } from '../../../lib/metric-labels';
import { connectionsApi, type ChannelInfoResponse } from '@/lib/api/connections';
import { useGrowthStudioContext } from '../context/GrowthStudioContext';
import { useSyncChannel } from '../../../hooks/useSyncChannel';
import { MetaAdsOverviewPanel } from './meta-ads/MetaAdsOverviewPanel';
import { IgOrganicOverviewPanel } from './ig-organic/IgOrganicOverviewPanel';
import { YouTubeOverviewPanel } from './youtube-organic/YouTubeOverviewPanel';
import { YouTubeTopVideosList } from './youtube/YouTubeTopVideosList';
import { YouTubeTrafficSourcesChart } from './youtube/YouTubeTrafficSourcesChart';
import { YouTubeDemographicsChart } from './youtube/YouTubeDemographicsChart';
import { MailOverviewPanel } from './mail/MailOverviewPanel';
import { WebsiteOverviewPanel } from './website/WebsiteOverviewPanel';

/** Section groupings for channels with many metrics. */
const CHANNEL_METRIC_SECTIONS: Record<string, Array<{ title: string; metrics: string[] }>> = {
  'ig-organic': [
    { title: 'Visibilidad', metrics: ['reach', 'ig_views', 'ig_followers_count', 'ig_follows_and_unfollows', 'ig_media_count'] },
    { title: 'Engagement', metrics: ['total_interactions', 'ig_likes', 'ig_comments', 'ig_shares', 'ig_saves', 'ig_replies', 'ig_reposts'] },
    { title: 'Perfil', metrics: ['ig_accounts_engaged', 'ig_profile_links_taps'] },
    { title: 'Demografía', metrics: ['ig_follower_demographics', 'ig_engaged_audience_demographics'] },
  ],
  'yt-organic': [
    { title: 'Alcance', metrics: ['views', 'avg_view_percentage'] },
    { title: 'Engagement', metrics: ['engagement', 'comments', 'shares'] },
    { title: 'Audiencia', metrics: ['subscribers_gained', 'subscribers_lost'] },
    { title: 'Retención', metrics: ['watch_time_minutes', 'avg_view_duration'] },
    { title: 'Conversión', metrics: ['card_clicks', 'card_click_rate', 'end_screen_clicks', 'end_screen_click_rate'] },
  ],
  'meta-ads': [
    { title: 'Rendimiento', metrics: ['reach', 'impressions', 'clicks', 'meta_inline_link_clicks', 'meta_outbound_clicks', 'meta_post_engagement', 'meta_landing_page_views'] },
    { title: 'Costos', metrics: ['spend', 'cpc', 'cpm', 'meta_cpp', 'frequency', 'meta_cost_per_link_click', 'meta_cost_per_outbound_click'] },
    { title: 'Conversiones', metrics: ['conversions', 'meta_leads', 'meta_add_to_cart', 'meta_initiate_checkout', 'meta_registrations', 'meta_view_content', 'meta_conversations_started'] },
    { title: 'Valor & ROAS', metrics: ['meta_conversion_value', 'meta_purchase_roas', 'meta_cost_per_purchase', 'meta_cost_per_lead'] },
    { title: 'Video', metrics: ['meta_video_views', 'meta_video_p25', 'meta_video_p50', 'meta_video_p75', 'meta_video_p100', 'meta_video_30sec', 'meta_video_avg_watch_time'] },
    { title: 'Demografía', metrics: ['meta_reach_by_age', 'meta_spend_by_age', 'meta_impressions_by_age', 'meta_reach_by_gender', 'meta_spend_by_gender', 'meta_impressions_by_gender'] },
    { title: 'Plataforma', metrics: ['meta_reach_by_placement', 'meta_spend_by_placement', 'meta_impressions_by_placement'] },
  ],
};

function formatNumber(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1000) return `${(n / 1000).toFixed(n >= 10000 ? 0 : 1)}k`;
  return n.toLocaleString('es-ES');
}

function formatCurrency(n: number, currency?: string, fallback = 'USD'): string {
  return formatMoney(n, currency || fallback);
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
  initialTab?: string | null;
}

export default function ChannelDetailSidebar({ isOpen, onClose, channel, initialTab }: ChannelDetailSidebarProps) {
  const { timezone, currency: tenantCurrency } = useTenantLocale();
  const { handleOpenExpandedDashboard } = useGrowthStudioContext();
  const { getToken } = useAuth();
  const { sync, isSyncing, cooldownMinutes } = useSyncChannel(channel?.slug ?? '');
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

  // Meta Ads: Wider sidebar with dedicated overview panel
  if (channel.slug === 'meta-ads') {
    return (
      <DetailPanel open={isOpen} onClose={onClose} size="lg">
        <MetaAdsOverviewPanel
          channel={channel}
          onClose={onClose}
          onExpand={() => handleOpenExpandedDashboard('meta-ads')}
          onExpandToTab={() => handleOpenExpandedDashboard('meta-ads')}
          initialTab={initialTab}
        />
      </DetailPanel>
    );
  }

  // IG Organic: Wider sidebar with dedicated overview panel
  if (channel.slug === 'ig-organic') {
    return (
      <DetailPanel open={isOpen} onClose={onClose} size="lg">
        <IgOrganicOverviewPanel
          channel={channel}
          onClose={onClose}
          onExpand={() => handleOpenExpandedDashboard('ig-organic')}
          initialTab={initialTab}
        />
      </DetailPanel>
    );
  }

  // YouTube Organic: Wider sidebar with dedicated overview panel
  if (channel.slug === 'yt-organic') {
    return (
      <DetailPanel open={isOpen} onClose={onClose} size="lg">
        <YouTubeOverviewPanel
          channel={channel}
          onClose={onClose}
          onExpand={() => handleOpenExpandedDashboard('yt-organic')}
          initialTab={initialTab}
        />
      </DetailPanel>
    );
  }

  // Website: Wider sidebar with dedicated overview panel
  if (channel.slug === 'website-total') {
    return (
      <DetailPanel open={isOpen} onClose={onClose} size="lg">
        <WebsiteOverviewPanel
          channel={channel}
          onClose={onClose}
          onExpand={() => handleOpenExpandedDashboard('website-total')}
          initialTab={initialTab}
        />
      </DetailPanel>
    );
  }

  // Email Marketing: Wider sidebar with dedicated overview panel
  if (channel.slug === 'email-nurture' || channel.slug.startsWith('email-')) {
    return (
      <DetailPanel open={isOpen} onClose={onClose} size="lg">
        <MailOverviewPanel
          channel={channel}
          onClose={onClose}
          onExpand={() => handleOpenExpandedDashboard('email-nurture')}
          initialTab={initialTab}
        />
      </DetailPanel>
    );
  }

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
                          {formatTenantDate(info.data_range.min_date, timezone, 'd MMM')}
                          {' — '}
                          {formatTenantDate(info.data_range.max_date, timezone, 'd MMM yyyy')}
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
                {(() => {
                  const sections = CHANNEL_METRIC_SECTIONS[channel.slug];
                  const metricsByName = Object.fromEntries(channel.metrics.map((m: MetricValue) => [m.name, m]));

                  const renderMetric = (m: MetricValue) => {
                    const label = METRIC_LABELS[m.name] ?? m.name;

                    // Demographics: render as key-value breakdown
                    if (m.unit === 'json' && m.extra?.breakdowns) {
                      const breakdowns = m.extra.breakdowns as Array<{ dimension_values: string[]; value: number }>;
                      const sorted = Array.isArray(breakdowns)
                        ? [...breakdowns].sort((a, b) => (b.value ?? 0) - (a.value ?? 0)).slice(0, 5)
                        : [];
                      const maxVal = sorted.length > 0 ? Math.max(...sorted.map(b => b.value ?? 0), 1) : 1;

                      return (
                        <div key={m.name} className="space-y-1.5">
                          <span className="text-sm text-muted-foreground">{label}</span>
                          {sorted.length > 0 ? (
                            <div className="space-y-1">
                              {sorted.map((b, i) => {
                                const dimLabel = (b.dimension_values ?? []).join(', ') || `#${i + 1}`;
                                const pct = ((b.value ?? 0) / maxVal) * 100;
                                return (
                                  <div key={dimLabel} className="flex items-center gap-2">
                                    <span className="text-xs text-muted-foreground w-24 truncate" title={dimLabel}>{dimLabel}</span>
                                    <div className="flex-1 h-2 bg-muted/50 rounded-full overflow-hidden">
                                      <div className="h-full bg-primary/40 rounded-full" style={{ width: `${pct}%` }} />
                                    </div>
                                    <span className="text-xs font-medium tabular-nums w-8 text-right">{b.value ?? 0}</span>
                                  </div>
                                );
                              })}
                            </div>
                          ) : (
                            <span className="text-xs text-muted-foreground">Sin datos demográficos</span>
                          )}
                        </div>
                      );
                    }

                    const isCurrency = m.unit === 'currency';
                    const formatted = isCurrency
                      ? formatCurrency(m.value, m.currency, tenantCurrency)
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
                  };

                  const renderSections = () => {
                    if (!sections) {
                      return (
                        <section>
                          <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-widest mb-3">
                            Métricas Actuales
                          </h3>
                          <div className="space-y-2">
                            {channel.metrics.map(renderMetric)}
                          </div>
                        </section>
                      );
                    }
                    return sections.map((section) => {
                      const sectionMetrics = section.metrics
                        .map(name => metricsByName[name])
                        .filter((m): m is MetricValue => m !== undefined);
                      if (sectionMetrics.length === 0) return null;
                      return (
                        <section key={section.title} className="mt-4">
                          <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-widest mb-3">
                            {section.title}
                          </h3>
                          <div className="space-y-2">
                            {sectionMetrics.map(renderMetric)}
                          </div>
                        </section>
                      );
                    });
                  };

                  // YouTube: Tabbed layout with Métricas / Videos / Audiencia
                  if (channel.slug === 'yt-organic') {
                    return (
                      <Tabs defaultValue={initialTab ?? 'metricas'} className="mt-2">
                        <TabsList className="w-full">
                          <TabsTrigger value="metricas" className="flex-1 text-xs">Métricas</TabsTrigger>
                          <TabsTrigger value="videos" className="flex-1 text-xs">Videos</TabsTrigger>
                          <TabsTrigger value="audiencia" className="flex-1 text-xs">Audiencia</TabsTrigger>
                        </TabsList>
                        <TabsContent value="metricas" className="mt-3">
                          {renderSections()}
                        </TabsContent>
                        <TabsContent value="videos" className="mt-3 space-y-4">
                          <section>
                            <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-widest mb-3">
                              Top Videos
                            </h3>
                            <YouTubeTopVideosList enabled={isOpen} />
                          </section>
                          <Separator />
                          <section>
                            <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-widest mb-3">
                              Fuentes de Tráfico
                            </h3>
                            <YouTubeTrafficSourcesChart enabled={isOpen} />
                          </section>
                        </TabsContent>
                        <TabsContent value="audiencia" className="mt-3">
                          <YouTubeDemographicsChart enabled={isOpen} />
                        </TabsContent>
                      </Tabs>
                    );
                  }

                  return renderSections();
                })()}
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
              <Button
                variant="outline"
                size="sm"
                className="w-full justify-start gap-2"
                onClick={() => sync()}
                disabled={isSyncing || cooldownMinutes > 0}
              >
                <RefreshCw className={cn('h-3.5 w-3.5', isSyncing && 'animate-spin')} />
                {isSyncing ? 'Sincronizando…' : cooldownMinutes > 0 ? `Disponible en ${Math.ceil(cooldownMinutes)} min` : 'Sincronizar ahora'}
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
