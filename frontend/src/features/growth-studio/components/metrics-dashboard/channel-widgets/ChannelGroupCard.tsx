"use client";

import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Megaphone, Share2, Search, PhoneOutgoing, PlusCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { formatMoney } from "@/lib/format-money";
import type { ChannelMetric, GroupType, MetricClickData, StageId } from "../../../types/metrics";
import { ChannelRow } from "./ChannelRow";

interface ChannelGroupCardProps {
  title: string;
  totals: Record<string, number>;
  channels: ChannelMetric[];
  groupType: GroupType;
  /** Stage context forwarded to ChannelRow for MetricClickData */
  stageId?: StageId;
  /** Callback forwarded to ChannelRow when user clicks a metric value */
  onMetricClick?: (metric: MetricClickData) => void;
  /** Callback forwarded to ChannelRow when the entire connected channel row is clicked */
  onChannelClick?: (channel: ChannelMetric) => void;
  /** Callback forwarded to ChannelRow when user clicks "Configurar" */
  onConfigure?: (slug: string, name: string) => void;
}

/* ── helpers ──────────────────────────────────────────────────────────── */

function formatNumber(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1000) return `${(n / 1000).toFixed(n >= 10000 ? 0 : 1)}k`;
  return n.toLocaleString();
}

function fmtCurrency(n: number, currency: string): string {
  return formatMoney(n, currency, { fractionDigits: 0 });
}

/** Icon + accent color per group type. */
function getGroupMeta(groupType: GroupType) {
  switch (groupType) {
    case "paid":
      return { Icon: Megaphone, accent: "text-amber-400", bg: "bg-amber-500/10" };
    case "organic_social":
      return { Icon: Share2, accent: "text-violet-400", bg: "bg-violet-500/10" };
    case "ga4_search":
      return { Icon: Search, accent: "text-blue-400", bg: "bg-blue-500/10" };
    case "outbound":
      return { Icon: PhoneOutgoing, accent: "text-emerald-400", bg: "bg-emerald-500/10" };
    case "available":
      return { Icon: PlusCircle, accent: "text-muted-foreground", bg: "bg-muted/30" };
    default:
      return { Icon: Share2, accent: "text-primary", bg: "bg-primary/10" };
  }
}

/** Extract the first available currency code from channel metrics. */
function extractCurrency(channels: ChannelMetric[]): string {
  for (const ch of channels) {
    for (const m of ch.metrics) {
      if (m.currency) return m.currency;
    }
  }
  return "USD";
}

/** Build metric chip data per group type. */
function getMetricChips(groupType: GroupType, totals: Record<string, number>, currency: string) {
  switch (groupType) {
    case "organic_social":
      return [
        {
          label: "Alcance",
          value: formatNumber(totals.reach ?? 0),
          color: "bg-blue-500/15 text-blue-400",
        },
        {
          label: "Engagement",
          value: formatNumber(totals.engagement ?? 0),
          color: "bg-violet-500/15 text-violet-400",
        },
      ];
    case "ga4_search":
      return [
        {
          label: "Sesiones",
          value: formatNumber(totals.sessions ?? 0),
          color: "bg-blue-500/15 text-blue-400",
        },
        {
          label: "Usuarios",
          value: formatNumber(totals.users ?? 0),
          color: "bg-cyan-500/15 text-cyan-400",
        },
      ];
    case "paid":
      return [
        {
          label: "Alcance",
          value: formatNumber(totals.reach ?? 0),
          color: "bg-amber-500/15 text-amber-400",
        },
        {
          label: "Clicks",
          value: formatNumber(totals.clicks ?? 0),
          color: "bg-orange-500/15 text-orange-400",
        },
        {
          label: "Gasto",
          value: fmtCurrency(totals.spend ?? 0, currency),
          color: "bg-red-500/15 text-red-300",
        },
      ];
    case "outbound":
      return [
        {
          label: "Contactos",
          value: formatNumber(totals.contacts ?? 0),
          color: "bg-emerald-500/15 text-emerald-400",
        },
        {
          label: "Respuestas",
          value: formatNumber(totals.responses ?? 0),
          color: "bg-teal-500/15 text-teal-400",
        },
      ];
    case "available":
      return [];
    default:
      return [];
  }
}

/* ── component ────────────────────────────────────────────────────────── */

export function ChannelGroupCard({
  title,
  totals,
  channels,
  groupType,
  stageId,
  onMetricClick,
  onChannelClick,
  onConfigure,
}: ChannelGroupCardProps) {
  const { Icon, accent, bg } = getGroupMeta(groupType);
  const currency = extractCurrency(channels);
  const chips = getMetricChips(groupType, totals, currency);

  const connectedChannels = channels.filter((c) => c.connected);
  const availableChannels = channels.filter((c) => !c.connected);

  const isAvailableGroup = groupType === "available";
  const totalCount = channels.length;
  const connectedCount = connectedChannels.length;

  return (
    <Card className="overflow-hidden border shadow-sm">
      {/* ── Header ─────────────────────────────────────────────────────── */}
      <CardHeader className="py-3 px-4 border-b bg-muted/20">
        <div className="flex items-center justify-between gap-3">
          {/* Left: icon + title + count */}
          <div className="flex items-center gap-3 min-w-0">
            <div className={cn("flex items-center justify-center w-8 h-8 rounded-lg shrink-0", bg)}>
              <Icon className={cn("w-4 h-4", accent)} />
            </div>
            <div className="min-w-0">
              <h3 className="text-sm font-semibold leading-tight truncate">{title}</h3>
              <span className="text-[11px] text-muted-foreground">
                {isAvailableGroup
                  ? `${totalCount} canales por configurar`
                  : connectedCount > 0
                    ? `${totalCount} canal${totalCount !== 1 ? "es" : ""} · ${connectedCount} conectado${connectedCount !== 1 ? "s" : ""}`
                    : `${totalCount} canal${totalCount !== 1 ? "es" : ""}`}
              </span>
            </div>
          </div>

          {/* Right: metric chips */}
          {chips.length > 0 && (
            <div className="flex items-center gap-1.5 shrink-0 flex-wrap justify-end">
              {chips.map((chip) => (
                <span
                  key={chip.label}
                  className={cn(
                    "inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-semibold tabular-nums",
                    chip.color,
                  )}
                >
                  {chip.value}
                  <span className="font-normal opacity-70 text-[10px]">
                    {chip.label.toLowerCase()}
                  </span>
                </span>
              ))}
            </div>
          )}
        </div>
      </CardHeader>

      {/* ── Body ───────────────────────────────────────────────────────── */}
      <CardContent className="p-1.5 bg-card">
        {/* Connected channels */}
        {connectedChannels.length > 0 && (
          <div className="space-y-0.5">
            {connectedChannels.map((ch) => (
              <ChannelRow
                key={ch.slug}
                channel={ch}
                stageId={stageId}
                onMetricClick={onMetricClick}
                onChannelClick={onChannelClick}
              />
            ))}
          </div>
        )}

        {/* Separator between connected and available */}
        {connectedChannels.length > 0 && availableChannels.length > 0 && !isAvailableGroup && (
          <div className="mx-3 my-1.5 border-t border-border/40" />
        )}

        {/* Available / unconnected channels */}
        {availableChannels.length > 0 && (
          <div className="space-y-0.5">
            {!isAvailableGroup && availableChannels.length > 0 && connectedChannels.length > 0 && (
              <span className="block px-3 pt-1 pb-0.5 text-[10px] uppercase tracking-wider text-muted-foreground/60 font-medium">
                Disponibles
              </span>
            )}
            {availableChannels.map((ch) => (
              <ChannelRow
                key={ch.slug}
                channel={ch}
                stageId={stageId}
                onMetricClick={onMetricClick}
                onChannelClick={onChannelClick}
              />
            ))}
          </div>
        )}

        {/* Empty state */}
        {channels.length === 0 && (
          <div className="py-6 text-center">
            <p className="text-sm text-muted-foreground">Sin canales configurados</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
