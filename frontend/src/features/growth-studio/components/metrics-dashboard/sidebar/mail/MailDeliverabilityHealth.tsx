"use client";

import { ShieldCheck, ShieldAlert, ShieldX } from "lucide-react";

import { cn } from "@/lib/utils";

import type { MetricKpiData } from "../../../../types/metrics";

interface MailDeliverabilityHealthProps {
  kpis: MetricKpiData[];
}

type HealthLevel = "healthy" | "warning" | "critical";

function computeHealthLevel(kpis: MetricKpiData[]): {
  level: HealthLevel;
  score: number;
  details: string;
} {
  const bounceRate = kpis.find((k) => k.metricName === "bounce_rate")?.currentValue ?? 0;
  const spamReports = kpis.find((k) => k.metricName === "spam_reports")?.currentValue ?? 0;
  const unsubRate = kpis.find((k) => k.metricName === "unsubscribe_rate")?.currentValue ?? 0;
  const emailsSent = kpis.find((k) => k.metricName === "emails_sent")?.currentValue ?? 0;

  const spamRate = emailsSent > 0 ? (spamReports / emailsSent) * 100 : 0;

  let score = 100;
  if (bounceRate > 5) score -= 40;
  else if (bounceRate > 2) score -= 20;
  else if (bounceRate > 0.7) score -= 10;

  if (spamRate > 0.1) score -= 30;
  else if (spamRate > 0.05) score -= 15;

  if (unsubRate > 0.5) score -= 30;
  else if (unsubRate > 0.2) score -= 15;
  else if (unsubRate > 0.1) score -= 5;

  score = Math.max(0, score);

  const parts: string[] = [];
  if (bounceRate > 2) parts.push(`rebote ${bounceRate.toFixed(1)}%`);
  if (spamRate > 0.05) parts.push(`spam ${spamRate.toFixed(2)}%`);
  if (unsubRate > 0.2) parts.push(`desuscripción ${unsubRate.toFixed(1)}%`);

  const details = parts.length > 0 ? parts.join(", ") : "Todos los indicadores normales";

  if (score >= 70) return { level: "healthy", score, details };
  if (score >= 40) return { level: "warning", score, details };
  return { level: "critical", score, details };
}

const HEALTH_CONFIG: Record<
  HealthLevel,
  { icon: typeof ShieldCheck; label: string; color: string; bg: string; border: string }
> = {
  healthy: {
    icon: ShieldCheck,
    label: "Saludable",
    color: "text-emerald-600",
    bg: "bg-emerald-50 dark:bg-emerald-950/30",
    border: "border-emerald-200 dark:border-emerald-900",
  },
  warning: {
    icon: ShieldAlert,
    label: "Atención",
    color: "text-amber-600",
    bg: "bg-amber-50 dark:bg-amber-950/30",
    border: "border-amber-200 dark:border-amber-900",
  },
  critical: {
    icon: ShieldX,
    label: "Crítico",
    color: "text-red-600",
    bg: "bg-red-50 dark:bg-red-950/30",
    border: "border-red-200 dark:border-red-900",
  },
};

export function MailDeliverabilityHealth({ kpis }: MailDeliverabilityHealthProps) {
  const { level, score, details } = computeHealthLevel(kpis);
  const config = HEALTH_CONFIG[level];
  const Icon = config.icon;

  return (
    <div className={cn("rounded-lg border p-4", config.bg, config.border)}>
      <div className="flex items-center gap-3">
        <div className={cn("flex h-10 w-10 items-center justify-center rounded-full", config.bg)}>
          <Icon className={cn("h-5 w-5", config.color)} />
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className={cn("text-sm font-semibold", config.color)}>{config.label}</span>
            <span className="text-xs text-muted-foreground">({score}/100)</span>
          </div>
          <p className="text-xs text-muted-foreground mt-0.5">{details}</p>
        </div>
      </div>
    </div>
  );
}
