"use client";

import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import type { ChannelMetric, GroupType, MetricClickData, StageId } from "../../../types/metrics";
import { formatMoney } from "@/lib/format-money";
import { ChannelRow } from "./ChannelRow";

interface ChannelGroupProps {
  title: string;
  totals: Record<string, number>;
  channels: ChannelMetric[];
  groupType: GroupType;
  defaultOpen?: boolean;
  /** Stage context forwarded to ChannelRow for MetricClickData */
  stageId?: StageId;
  /** Callback forwarded to ChannelRow when user clicks a metric value */
  onMetricClick?: (metric: MetricClickData) => void;
  /** Callback forwarded to ChannelRow when the entire connected channel row is clicked */
  onChannelClick?: (channel: ChannelMetric) => void;
  /** Callback forwarded to ChannelRow when user clicks "Configurar" */
  onConfigure?: (slug: string, name: string) => void;
}

function formatNumber(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1000) return `${(n / 1000).toFixed(n >= 10000 ? 0 : 1)}k`;
  return n.toLocaleString();
}

function fmtCurrency(n: number, currency: string): string {
  return formatMoney(n, currency, { fractionDigits: 2 });
}

export function buildSummary(
  groupType: GroupType,
  totals: Record<string, number>,
  channelCount: number,
  currency = "USD",
): string {
  switch (groupType) {
    case "organic_social":
      return `Alcance: ${formatNumber(totals.reach ?? 0)} | Engagement: ${formatNumber(totals.engagement ?? 0)}`;
    case "ga4_search":
      return `Sesiones: ${formatNumber(totals.sessions ?? 0)} | Usuarios: ${formatNumber(totals.users ?? 0)}`;
    case "paid":
      return `Alcance: ${formatNumber(totals.reach ?? 0)} | Clicks: ${formatNumber(totals.clicks ?? 0)} | Conversiones: ${formatNumber(totals.conversions ?? 0)} | Gasto: ${fmtCurrency(totals.spend ?? 0, currency)}`;
    case "outbound":
      return `Contactos: ${formatNumber(totals.contacts ?? 0)} | Respuestas: ${formatNumber(totals.responses ?? 0)}`;
    case "web_infrastructure":
    case "ai_agent": {
      const leads = formatNumber(totals.leads ?? 0);
      const cpl =
        totals.cost && totals.leads
          ? formatMoney(totals.cost / totals.leads, currency, { fractionDigits: 2 })
          : "---";
      const conv = totals.conversion_rate?.toFixed(1) ?? "0";
      return `Leads: ${leads} | Costo por Lead: ${cpl} | Conversión: ${conv}%`;
    }
    case "retargeting": {
      const costPerMql = totals.cost_per_mql;
      const costStr =
        costPerMql != null
          ? ` | Costo/MQL: ${formatMoney(costPerMql, currency, { fractionDigits: 2 })}`
          : "";
      return `Alcance: ${formatNumber(totals.reach ?? 0)} | Clicks: ${formatNumber(totals.clicks ?? 0)} | Gasto: ${fmtCurrency(totals.spend ?? 0, currency)}${costStr}`;
    }
    case "automation": {
      const costPerMql = totals.cost_per_mql;
      const costStr =
        costPerMql != null
          ? ` | Costo/MQL: ${formatMoney(costPerMql, currency, { fractionDigits: 2 })}`
          : "";
      return `Emails: ${formatNumber(totals.emails_sent ?? 0)} | Apertura: ${(totals.open_rate ?? 0).toFixed(1)}% | Click Rate: ${(totals.click_rate ?? 0).toFixed(1)}%${costStr}`;
    }
    case "checkout": {
      const abandonRate = totals.abandonment_rate;
      const abandonStr = abandonRate != null ? ` | Tasa Abandono: ${abandonRate.toFixed(1)}%` : "";
      return `Checkouts: ${formatNumber(totals.count ?? 0)} | Abandonos: ${formatNumber(totals.abandoned ?? 0)} | Valor: ${fmtCurrency(totals.value ?? 0, currency)}${abandonStr}`;
    }
    case "payment_links": {
      return `Links: ${formatNumber(totals.count ?? 0)} | Valor: ${fmtCurrency(totals.value ?? 0, currency)}`;
    }
    case "qualification": {
      const attended = totals.attendance_rate;
      const attendStr = attended != null ? ` | Asistencia: ${attended.toFixed(1)}%` : "";
      return `Reuniones: ${formatNumber(totals.booked ?? 0)} | Completadas: ${formatNumber(totals.completed ?? 0)} | No-show: ${formatNumber(totals.no_show ?? 0)}${attendStr}`;
    }
    case "available":
      return `${channelCount} canales por configurar`;
    default:
      return "";
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

export function ChannelGroup({
  title,
  totals,
  channels,
  groupType,
  defaultOpen = true,
  stageId,
  onMetricClick,
  onChannelClick,
  onConfigure,
}: ChannelGroupProps) {
  const currency = extractCurrency(channels);
  const summary = buildSummary(groupType, totals, channels.length, currency);

  return (
    <Accordion type="single" collapsible defaultValue={defaultOpen ? "group" : undefined}>
      <AccordionItem value="group" className="border-none">
        <AccordionTrigger className="hover:no-underline py-3">
          <div className="flex flex-col items-start gap-0.5">
            <span className="text-sm font-semibold">{title}</span>
            <span className="text-xs text-muted-foreground">{summary}</span>
          </div>
        </AccordionTrigger>
        <AccordionContent>
          <div className="space-y-1">
            {channels.map((ch) => (
              <ChannelRow
                key={ch.slug}
                channel={ch}
                stageId={stageId}
                onMetricClick={onMetricClick}
                onChannelClick={onChannelClick}
              />
            ))}
          </div>
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  );
}
