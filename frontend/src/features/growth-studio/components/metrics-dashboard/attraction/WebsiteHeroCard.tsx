'use client';

import { useMemo } from 'react';
import { Globe, Smartphone, Monitor, Tablet, Search, Share2, Mail, Link2, MousePointerClick, BarChart3, Crosshair, CheckCircle2 } from 'lucide-react';
import type { TrafficGroup, ChannelMetric, MetricValue } from '../../../types/metrics';

interface WebsiteHeroCardProps {
  website: TrafficGroup | undefined;
  onChannelClick?: (channel: ChannelMetric) => void;
}

function getMetricExtra(channels: ChannelMetric[], metricName: string): Record<string, unknown> | undefined {
  for (const ch of channels) {
    const m = ch.metrics.find((metric: MetricValue) => metric.name === metricName);
    if (m?.breakdown) return m.breakdown as Record<string, unknown>;
  }
  return undefined;
}

function formatNum(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1000) return `${(n / 1000).toFixed(1)}K`;
  return n.toLocaleString('es-ES');
}

function formatDuration(seconds: number): string {
  if (seconds < 60) return `${Math.round(seconds)}s`;
  const min = Math.floor(seconds / 60);
  const sec = Math.round(seconds % 60);
  return `${min}m ${sec}s`;
}

const SOURCE_ICONS: Record<string, typeof Search> = {
  'Organic Search': Search,
  'Direct': MousePointerClick,
  'Social': Share2,
  'Email': Mail,
  'Referral': Link2,
};

function MetricCell({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-[10px] text-muted-foreground uppercase tracking-wider">{label}</p>
      <p className="text-lg font-bold text-foreground leading-tight">{value}</p>
    </div>
  );
}

export function WebsiteHeroCard({ website, onChannelClick }: WebsiteHeroCardProps) {
  const totals = website?.totals;
  const channels = website?.channels ?? [];

  const engagementRate = useMemo(() => {
    if (!totals) return 0;
    const sessions = totals.sessions ?? 0;
    const engaged = totals.engagedSessions ?? 0;
    return sessions > 0 ? (engaged / sessions) * 100 : 0;
  }, [totals]);

  const topPages = useMemo(() => {
    if (channels.length === 0) return [];
    const extra = getMetricExtra(channels, 'top_pages');
    if (!extra) return [];
    const pages = (extra as { pages?: { path: string; views: number }[] }).pages;
    return (pages ?? []).slice(0, 3);
  }, [channels]);

  const trafficSources = useMemo(() => {
    if (channels.length === 0) return [];
    const extra = getMetricExtra(channels, 'traffic_sources');
    if (!extra) return [];
    const sources = (extra as { sources?: { channel: string; sessions: number }[] }).sources;
    if (!sources?.length) return [];
    const total = sources.reduce((s, item) => s + item.sessions, 0);
    return sources.slice(0, 5).map(s => ({
      ...s,
      pct: total > 0 ? (s.sessions / total) * 100 : 0,
    }));
  }, [channels]);

  const deviceSplit = useMemo(() => {
    if (channels.length === 0) return null;
    const extra = getMetricExtra(channels, 'device_split');
    if (!extra) return null;
    return extra as { mobile?: number; desktop?: number; tablet?: number };
  }, [channels]);

  // Empty state: no website data sources connected
  if (!website || channels.length === 0) {
    return (
      <div className="bg-card border border-dashed border-border rounded-xl p-5">
        <div className="flex items-center gap-2 mb-3">
          <Globe className="w-5 h-5 text-muted-foreground" />
          <h3 className="text-sm font-semibold text-foreground">Tu Sitio Web</h3>
        </div>
        <p className="text-sm text-muted-foreground mb-4">
          Tu sitio web siempre esta aqui. Conecta Google Analytics o el Meta Pixel para medir tus visitas y optimizar resultados.
        </p>
        <div className="flex flex-wrap gap-2">
          <a href="/settings/connections" className="inline-flex items-center gap-1.5 text-xs font-medium text-primary border border-primary/30 rounded-md px-3 py-1.5 hover:bg-primary/5 transition-colors">
            <BarChart3 className="w-3 h-3" />
            Conectar Google Analytics
          </a>
          <a href="/settings/connections" className="inline-flex items-center gap-1.5 text-xs font-medium text-muted-foreground border border-border rounded-md px-3 py-1.5 hover:bg-muted transition-colors">
            <Crosshair className="w-3 h-3" />
            Instalar Meta Pixel
          </a>
        </div>
      </div>
    );
  }

  const websiteChannel = channels[0];

  // Determine which sources are present
  const hasGA4 = channels.some(ch => ch.slug === 'website-total');
  const hasPixel = channels.some(ch => ch.slug === 'meta-pixel');

  return (
    <div
      className="bg-card border border-border rounded-xl p-5 cursor-pointer hover:border-primary/30 transition-colors"
      onClick={() => websiteChannel && onChannelClick?.(websiteChannel)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && websiteChannel && onChannelClick?.(websiteChannel)}
    >
      {/* Header */}
      <div className="flex items-center gap-2 mb-4">
        <Globe className="w-5 h-5 text-blue-500" />
        <h3 className="text-sm font-semibold text-foreground">Tu Sitio Web</h3>
        <div className="ml-auto flex items-center gap-2">
          {hasGA4 && (
            <span className="inline-flex items-center gap-1 text-[10px] text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/30 px-1.5 py-0.5 rounded">
              <CheckCircle2 className="w-3 h-3" /> GA4
            </span>
          )}
          {hasPixel && (
            <span className="inline-flex items-center gap-1 text-[10px] text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-950/30 px-1.5 py-0.5 rounded">
              <CheckCircle2 className="w-3 h-3" /> Meta Pixel
            </span>
          )}
        </div>
      </div>

      {/* Hero metrics row */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-4 mb-5">
        <MetricCell label="Visitantes" value={formatNum(totals?.users ?? 0)} />
        <MetricCell label="Sesiones" value={formatNum(totals?.sessions ?? 0)} />
        <MetricCell label="Engagement" value={`${engagementRate.toFixed(1)}%`} />
        <MetricCell label="Bounce Rate" value={`${(totals?.bounceRate ?? 0).toFixed(1)}%`} />
        <MetricCell label="Duracion Prom." value={formatDuration(totals?.averageSessionDuration ?? 0)} />
      </div>

      {/* Device split bar */}
      {deviceSplit && (
        <div className="mb-4">
          <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-1.5">Dispositivos</p>
          <div className="flex h-2 rounded-full overflow-hidden bg-muted">
            <div className="bg-blue-500" style={{ width: `${deviceSplit.mobile ?? 0}%` }} title={`Movil ${deviceSplit.mobile ?? 0}%`} />
            <div className="bg-violet-500" style={{ width: `${deviceSplit.desktop ?? 0}%` }} title={`Desktop ${deviceSplit.desktop ?? 0}%`} />
            <div className="bg-amber-500" style={{ width: `${deviceSplit.tablet ?? 0}%` }} title={`Tablet ${deviceSplit.tablet ?? 0}%`} />
          </div>
          <div className="flex gap-3 mt-1">
            <span className="flex items-center gap-1 text-[10px] text-muted-foreground"><Smartphone className="w-3 h-3" /> {deviceSplit.mobile ?? 0}%</span>
            <span className="flex items-center gap-1 text-[10px] text-muted-foreground"><Monitor className="w-3 h-3" /> {deviceSplit.desktop ?? 0}%</span>
            <span className="flex items-center gap-1 text-[10px] text-muted-foreground"><Tablet className="w-3 h-3" /> {deviceSplit.tablet ?? 0}%</span>
          </div>
        </div>
      )}

      {/* Top pages */}
      {topPages.length > 0 && (
        <div className="mb-4">
          <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-1.5">Paginas mas vistas</p>
          <div className="flex flex-wrap gap-2">
            {topPages.map((page) => (
              <span key={page.path} className="text-xs bg-muted px-2 py-1 rounded-md text-foreground">
                {page.path} <span className="text-muted-foreground">({formatNum(page.views)})</span>
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Traffic sources */}
      {trafficSources.length > 0 && (
        <div>
          <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-1.5">Fuentes de trafico</p>
          <div className="space-y-1.5">
            {trafficSources.map((src) => {
              const Icon = SOURCE_ICONS[src.channel] ?? Search;
              return (
                <div key={src.channel} className="flex items-center gap-2">
                  <Icon className="w-3.5 h-3.5 text-muted-foreground shrink-0" />
                  <span className="text-xs text-foreground w-24 truncate">{src.channel}</span>
                  <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden">
                    <div className="h-full bg-blue-500/60 rounded-full" style={{ width: `${src.pct}%` }} />
                  </div>
                  <span className="text-[10px] text-muted-foreground w-8 text-right">{src.pct.toFixed(0)}%</span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
