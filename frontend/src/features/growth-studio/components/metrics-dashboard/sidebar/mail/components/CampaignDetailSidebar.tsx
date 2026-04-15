"use client";

import { ExternalLink, Sparkles } from "lucide-react";

import {
  DetailPanel,
  DetailPanelHeader,
  DetailPanelTitle,
  DetailPanelClose,
} from "@/components/ui/detail-panel";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";

import {
  AUTOMATION_METRIC_INFO,
  type MetricInfo,
} from "../../../../../utils/automation-metric-info";
import { diagnoseCampaign } from "../../../../../utils/campaign-health";

import { MetricInfoTooltip } from "./MetricInfoTooltip";

import type { EmailCampaign } from "../../../../../types/mail-types";

interface CampaignDetailSidebarProps {
  campaign: EmailCampaign | null;
  onClose: () => void;
}

// Industry benchmarks (source: Mailchimp/GetResponse 2025)
const BENCHMARKS = {
  openRate: 21.5,
  clickRate: 2.3,
  ctor: 10.5,
  unsubRate: 0.26,
  bounceRate: 0.58,
};

/**
 * DetailPanel sidebar showing deep-dive metrics for a single email campaign.
 * Mirrors the automation step sidebar but without step context (no previous
 * step, no sequence position) and adds bounce rate diagnosis.
 */
export function CampaignDetailSidebar({ campaign, onClose }: CampaignDetailSidebarProps) {
  const isOpen = campaign !== null;

  return (
    <DetailPanel open={isOpen} onClose={onClose} size="md">
      {campaign && (
        <>
          <DetailPanelHeader>
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0 flex-1">
                <DetailPanelTitle className="truncate">
                  {campaign.campaignSubject || campaign.campaignName}
                </DetailPanelTitle>
                <p className="mt-0.5 text-xs text-muted-foreground truncate">
                  {campaign.campaignName}
                  {campaign.sentDate && (
                    <>
                      {" · "}
                      {new Date(campaign.sentDate).toLocaleDateString("es", {
                        day: "numeric",
                        month: "short",
                        year: "numeric",
                      })}
                    </>
                  )}
                </p>
              </div>
              <DetailPanelClose onClose={onClose} />
            </div>
          </DetailPanelHeader>

          <div className="px-6 pb-6">
            <Separator className="my-4" />
            <MetricsSection campaign={campaign} />
            <Separator className="my-5" />
            <BenchmarksSection campaign={campaign} />
            {campaign.previewUrl && (
              <>
                <Separator className="my-5" />
                <PreviewSection campaign={campaign} />
              </>
            )}
            <Separator className="my-5" />
            <DiagnosisSection campaign={campaign} />
            <Separator className="my-5" />
            <DetailsSection campaign={campaign} />
          </div>
        </>
      )}
    </DetailPanel>
  );
}

// ─── Sections ───────────────────────────────────────────────────────

function MetricsSection({ campaign }: { campaign: EmailCampaign }) {
  const openClass = colorForRate(campaign.openRate, 50, 30);
  const clickClass = colorForRate(campaign.clickRate, 5, 2);
  const ctorClass = colorForRate(campaign.clickToOpenRate, 15, 8);

  return (
    <section>
      <h4 className="mb-3 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
        Métricas de esta campaña
      </h4>
      <div className="grid grid-cols-3 gap-2">
        <MetricBox
          value={String(campaign.emailsSent)}
          label="Enviados"
          info={AUTOMATION_METRIC_INFO.enviados}
        />
        <MetricBox
          value={String(campaign.uniqueOpens)}
          label="Abiertos"
          info={AUTOMATION_METRIC_INFO.abiertos}
        />
        <MetricBox
          value={String(campaign.uniqueClicks)}
          label="Clicks"
          info={AUTOMATION_METRIC_INFO.clicks}
        />
        <MetricBox
          value={`${campaign.openRate.toFixed(1)}%`}
          label="Open Rate"
          valueClass={openClass}
          info={AUTOMATION_METRIC_INFO.openRate}
        />
        <MetricBox
          value={`${campaign.clickRate.toFixed(1)}%`}
          label="Click Rate"
          valueClass={clickClass}
          info={AUTOMATION_METRIC_INFO.clickRate}
        />
        <MetricBox
          value={`${campaign.clickToOpenRate.toFixed(1)}%`}
          label="CTOR"
          valueClass={ctorClass}
          info={AUTOMATION_METRIC_INFO.ctor}
        />
      </div>
    </section>
  );
}

function BenchmarksSection({ campaign }: { campaign: EmailCampaign }) {
  const unsubRate =
    campaign.emailsSent > 0 ? (campaign.unsubscribes / campaign.emailsSent) * 100 : 0;

  const rows = [
    {
      label: "Open Rate",
      value: campaign.openRate,
      benchmark: BENCHMARKS.openRate,
      suffix: "%",
      higherBetter: true,
      info: AUTOMATION_METRIC_INFO.openRate,
    },
    {
      label: "Click Rate",
      value: campaign.clickRate,
      benchmark: BENCHMARKS.clickRate,
      suffix: "%",
      higherBetter: true,
      info: AUTOMATION_METRIC_INFO.clickRate,
    },
    {
      label: "CTOR",
      value: campaign.clickToOpenRate,
      benchmark: BENCHMARKS.ctor,
      suffix: "%",
      higherBetter: true,
      info: AUTOMATION_METRIC_INFO.ctor,
    },
    {
      label: "Desuscripciones",
      value: unsubRate,
      benchmark: BENCHMARKS.unsubRate,
      suffix: "%",
      higherBetter: false,
      info: AUTOMATION_METRIC_INFO.unsubs,
    },
    {
      label: "Rebotes",
      value: campaign.bounceRate,
      benchmark: BENCHMARKS.bounceRate,
      suffix: "%",
      higherBetter: false,
      info: AUTOMATION_METRIC_INFO.bounces,
    },
  ];

  return (
    <section>
      <h4 className="mb-3 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
        vs Benchmarks de la Industria
      </h4>
      <div className="rounded-lg border bg-card p-3.5 space-y-2">
        {rows.map((row) => {
          const isBetter = row.higherBetter
            ? row.value >= row.benchmark
            : row.value <= row.benchmark;
          return (
            <div
              key={row.label}
              className="flex items-center justify-between text-xs border-b border-border/30 pb-2 last:border-0 last:pb-0"
            >
              <span className="flex items-center gap-1 text-muted-foreground">
                {row.label}
                <MetricInfoTooltip info={row.info} iconSize="xs" />
              </span>
              <span
                className={cn(
                  "font-semibold tabular-nums",
                  isBetter ? "text-emerald-500" : "text-amber-500",
                )}
              >
                {row.value.toFixed(1)}
                {row.suffix}{" "}
                <span className="text-[10px] font-normal text-muted-foreground">
                  vs {row.benchmark}
                  {row.suffix}
                </span>
              </span>
            </div>
          );
        })}
      </div>
    </section>
  );
}

function PreviewSection({ campaign }: { campaign: EmailCampaign }) {
  return (
    <section>
      <h4 className="mb-3 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
        Vista previa del email
      </h4>
      <div className="rounded-lg border bg-card overflow-hidden">
        {campaign.screenshotUrl ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={campaign.screenshotUrl}
            alt={`Vista previa de ${campaign.campaignSubject ?? "email"}`}
            className="w-full object-cover max-h-[320px]"
          />
        ) : (
          <div className="flex h-32 items-center justify-center bg-muted/10 text-xs text-muted-foreground">
            Sin vista previa disponible
          </div>
        )}
        <div className="flex items-center justify-between border-t px-3 py-2">
          <a
            href={campaign.previewUrl ?? "#"}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 text-[11px] text-primary hover:underline"
          >
            <ExternalLink className="h-3 w-3" />
            Ver email completo en MailerLite
          </a>
        </div>
      </div>
    </section>
  );
}

function DiagnosisSection({ campaign }: { campaign: EmailCampaign }) {
  const insights = diagnoseCampaign(campaign);
  const hasIssues = insights.length > 0;

  return (
    <section>
      <h4 className="mb-3 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
        Diagnóstico Inteligente
      </h4>
      <div className="rounded-lg border border-primary/20 bg-primary/5 px-4 py-3">
        <h5 className="mb-2 flex items-center gap-1.5 text-[11px] font-semibold text-primary">
          <Sparkles className="h-3 w-3" />
          Análisis de esta campaña
        </h5>
        {hasIssues ? (
          <ul className="space-y-1.5">
            {insights.map((insight, i) => (
              <li key={i} className="pl-4 text-xs text-muted-foreground leading-relaxed relative">
                <span className="absolute left-0 text-primary">→</span>
                {insight}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-xs text-muted-foreground">
            Esta campaña tiene performance saludable. Considera replicar su estructura (subject,
            tono, CTA) en futuras campañas.
          </p>
        )}
      </div>
    </section>
  );
}

function DetailsSection({ campaign }: { campaign: EmailCampaign }) {
  return (
    <section>
      <h4 className="mb-3 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
        Detalles de la campaña
      </h4>
      <div className="rounded-lg border bg-card p-3.5 space-y-2">
        <DetailRow label="Subject" value={campaign.campaignSubject ?? "—"} />
        <DetailRow label="Nombre" value={campaign.campaignName} />
        <DetailRow label="Tipo" value={campaign.campaignType} />
        {campaign.sentDate && (
          <DetailRow
            label="Fecha de envío"
            value={new Date(campaign.sentDate).toLocaleDateString("es", {
              day: "numeric",
              month: "long",
              year: "numeric",
            })}
          />
        )}
      </div>
    </section>
  );
}

// ─── Reusable bits ──────────────────────────────────────────────────

function MetricBox({
  value,
  label,
  valueClass,
  info,
}: {
  value: string;
  label: string;
  valueClass?: string;
  info: MetricInfo;
}) {
  return (
    <div className="rounded-lg border bg-card px-3 py-2.5 text-center">
      <p className={cn("text-lg font-bold tabular-nums", valueClass)}>{value}</p>
      <div className="flex items-center justify-center gap-1 text-[10px] text-muted-foreground">
        {label}
        <MetricInfoTooltip info={info} iconSize="xs" />
      </div>
    </div>
  );
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between text-xs border-b border-border/30 pb-2 last:border-0 last:pb-0">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium text-foreground truncate max-w-[60%] text-right">{value}</span>
    </div>
  );
}

function colorForRate(value: number, goodThreshold: number, midThreshold: number) {
  if (value >= goodThreshold) return "text-emerald-500";
  if (value >= midThreshold) return "text-amber-500";
  return "text-red-500";
}
