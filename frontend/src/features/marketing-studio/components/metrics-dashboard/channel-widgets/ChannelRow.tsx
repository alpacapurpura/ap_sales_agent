'use client';

import type { ChannelMetric } from '../../../types/metrics';
import { ConnectionBadge } from './ConnectionBadge';

const CHANNEL_ICONS: Record<string, string> = {
  'ig-organic': '📸',
  'yt-organic': '▶️',
  'fb-organic': '👤',
  'tiktok-organic': '🎵',
  'linkedin-organic': '💼',
  'google-organic': '🔍',
  'direct': '🔗',
  'ai-search-organic': '🤖',
  'meta-ads': '📢',
  'google-ads': '🎯',
  'tiktok-ads': '🎵',
  'yt-ads': '▶️',
  'cold-contact': '📞',
};

function formatNumber(n: number): string {
  if (n >= 1000) return `${(n / 1000).toFixed(n >= 10000 ? 0 : 1)}k`;
  return n.toLocaleString();
}

function formatCurrency(n: number): string {
  return `$${n.toLocaleString()}`;
}

interface ChannelRowProps {
  channel: ChannelMetric;
}

export function ChannelRow({ channel }: ChannelRowProps) {
  return (
    <div className="flex items-center justify-between py-2 px-3 rounded-md hover:bg-muted/50 transition-colors">
      <div className="flex items-center gap-3 min-w-0">
        <span className="text-lg shrink-0">{CHANNEL_ICONS[channel.slug] ?? '📊'}</span>
        <div className="min-w-0">
          <p className="text-sm font-medium truncate">{channel.name}</p>
          <p className="text-xs text-muted-foreground truncate">{channel.sourceLabel}</p>
        </div>
      </div>

      <div className="flex items-center gap-4 shrink-0">
        <span className="text-sm font-semibold tabular-nums">{formatNumber(channel.value)}</span>
        {channel.cost !== undefined && (
          <span className="text-xs text-muted-foreground tabular-nums">{formatCurrency(channel.cost)}</span>
        )}
        <ConnectionBadge connected={channel.connected} />
      </div>
    </div>
  );
}
