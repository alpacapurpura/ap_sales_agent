'use client';

import React from 'react';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import type { ChannelMetric } from '../../../types/metrics';
import { useTenantLocale } from '@/features/tenant/context/tenant-locale-context';
import { formatTenantDate } from '@/lib/format-date';
import { getChannelIcon } from '../../../lib/channelIcons';

/** Convert hex color to rgba for backgrounds. */
function hexToRgba(hex: string, alpha: number): string {
  if (hex.startsWith('hsl')) return hex;
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r},${g},${b},${alpha})`;
}

export interface ChannelRowHeaderProps {
  channel: ChannelMetric;
  /** Pre-resolved channel icon component (from getChannelIcon) */
  icon?: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  /** Pre-resolved channel color hex (from getChannelColor) */
  iconColor: string;
  /** Bottleneck badge severity for abandoned-cart channels */
  abandonmentBadge: 'warning' | 'critical' | null;
  /** No-show badge severity for meeting-booked channels */
  noShowBadge: 'warning' | 'critical' | null;
}

export const ChannelRowHeader = React.memo(function ChannelRowHeader({
  channel,
  icon,
  iconColor,
  abandonmentBadge,
  noShowBadge,
}: ChannelRowHeaderProps) {
  const ResolvedIcon = icon ?? getChannelIcon(channel.slug);
  const { timezone } = useTenantLocale();
  return (
    <div className="flex items-center gap-3 min-w-0">
      <div
        className={cn(
          'flex items-center justify-center w-8 h-8 rounded-lg shrink-0 transition-transform duration-100 group-hover:scale-105',
        )}
        style={{ backgroundColor: hexToRgba(iconColor, 0.12) }}
      >
        {React.createElement(ResolvedIcon, {
          className: 'w-4 h-4',
          style: { color: iconColor },
          'aria-hidden': true,
        })}
      </div>
      <div className="min-w-0">
        <div className="flex items-center gap-2">
          <p className="text-sm font-medium truncate">{channel.name}</p>
          {/* Connected dot */}
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shrink-0" title="Conectado" />
          {channel.stale && (
            <Badge variant="outline" className="border-yellow-500/50 text-yellow-600 dark:text-yellow-400 text-[10px] py-0">
              Desactualizado
            </Badge>
          )}
          {!channel.stale && channel.errorMessage?.startsWith('Parcial') && (
            <Badge variant="outline" className="border-orange-500/50 text-orange-600 dark:text-orange-400 text-[10px] py-0" title={channel.errorMessage}>
              Parcial
            </Badge>
          )}
          {abandonmentBadge === 'warning' && (
            <Badge variant="outline" className="border-yellow-500/50 text-yellow-600 dark:text-yellow-400 text-[10px] py-0">
              Alerta
            </Badge>
          )}
          {abandonmentBadge === 'critical' && (
            <Badge variant="outline" className="border-red-500/50 text-red-600 dark:text-red-400 text-[10px] py-0">
              Critico
            </Badge>
          )}
          {noShowBadge === 'warning' && (
            <Badge variant="outline" className="border-yellow-500/50 text-yellow-600 dark:text-yellow-400 text-[10px] py-0">
              Alerta
            </Badge>
          )}
          {noShowBadge === 'critical' && (
            <Badge variant="outline" className="border-red-500/50 text-red-600 dark:text-red-400 text-[10px] py-0">
              Critico
            </Badge>
          )}
        </div>
        <p className="text-[11px] text-muted-foreground truncate">
          {channel.sourceDisplayName
            ? `${channel.sourceLabel} · ${channel.sourceDisplayName}`
            : channel.sourceLabel}
        </p>
        {channel.lastUpdated && (
          <p className={`text-[10px] ${channel.stale ? 'text-yellow-600 dark:text-yellow-400' : 'text-muted-foreground'}`}>
            Última sync: {formatTenantDate(channel.lastUpdated, timezone, 'd MMM, HH:mm')}
          </p>
        )}
      </div>
    </div>
  );
});
