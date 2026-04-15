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

import { diagnoseStep } from "../../../../../utils/automation-health";
import {
  AUTOMATION_METRIC_INFO,
  type MetricInfo,
} from "../../../../../utils/automation-metric-info";

import { MetricInfoTooltip } from "./MetricInfoTooltip";

import type { AutomationStep } from "../../../../../types/mail-types";

interface AutomationStepSidebarProps {
  step: AutomationStep | null;
  automationName: string;
  totalSteps: number;
  previousStep: AutomationStep | null;
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
 * DetailPanel sidebar showing deep-dive metrics for a single email step
 * within an automation. Includes metrics grid, benchmark comparison,
 * preview link, AI diagnosis, and email metadata.
 */
export function AutomationStepSidebar({
  step,
  automationName,
  totalSteps,
  previousStep,
  onClose,
}: AutomationStepSidebarProps) {
  const isOpen = step !== null;

  return (
    <DetailPanel open={isOpen} onClose={onClose} size="md">
      {step && (
        <>
          <DetailPanelHeader>
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0 flex-1">
                <DetailPanelTitle className="truncate">
                  {step.subject || "(sin asunto)"}
                </DetailPanelTitle>
                <p className="mt-0.5 text-xs text-muted-foreground">
                  Email {step.stepNumber} de {totalSteps} · {automationName}
                </p>
              </div>
              <DetailPanelClose onClose={onClose} />
            </div>
          </DetailPanelHeader>

          <div className="px-6 pb-6">
            <Separator className="my-4" />
            <MetricsSection step={step} />
            <Separator className="my-5" />
            <BenchmarksSection step={step} />
            {step.previewUrl && (
              <>
                <Separator className="my-5" />
                <PreviewSection step={step} />
              </>
            )}
            <Separator className="my-5" />
            <DiagnosisSection step={step} previousStep={previousStep} />
            <Separator className="my-5" />
            <DetailsSection step={step} totalSteps={totalSteps} />
          </div>
        </>
      )}
    </DetailPanel>
  );
}

// ─── Sections ───────────────────────────────────────────────────────

function MetricsSection({ step }: { step: AutomationStep }) {
  const ctor = step.uniqueOpens > 0 ? (step.uniqueClicks / step.uniqueOpens) * 100 : 0;

  const openClass = colorForRate(step.openRate, 50, 30);
  const clickClass = colorForRate(step.clickRate, 5, 2);
  const ctorClass = colorForRate(ctor, 15, 8);

  return (
    <section>
      <h4 className="mb-3 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
        Métricas de este email
      </h4>
      <div className="grid grid-cols-3 gap-2">
        <MetricBox
          value={String(step.emailsSent)}
          label="Enviados"
          info={AUTOMATION_METRIC_INFO.enviados}
        />
        <MetricBox
          value={String(step.uniqueOpens)}
          label="Abiertos"
          info={AUTOMATION_METRIC_INFO.abiertos}
        />
        <MetricBox
          value={String(step.uniqueClicks)}
          label="Clicks"
          info={AUTOMATION_METRIC_INFO.clicks}
        />
        <MetricBox
          value={`${step.openRate.toFixed(1)}%`}
          label="Open Rate"
          valueClass={openClass}
          info={AUTOMATION_METRIC_INFO.openRate}
        />
        <MetricBox
          value={`${step.clickRate.toFixed(1)}%`}
          label="Click Rate"
          valueClass={clickClass}
          info={AUTOMATION_METRIC_INFO.clickRate}
        />
        <MetricBox
          value={`${ctor.toFixed(1)}%`}
          label="CTOR"
          valueClass={ctorClass}
          info={AUTOMATION_METRIC_INFO.ctor}
        />
      </div>
    </section>
  );
}

function BenchmarksSection({ step }: { step: AutomationStep }) {
  const ctor = step.uniqueOpens > 0 ? (step.uniqueClicks / step.uniqueOpens) * 100 : 0;
  const unsubRate = step.emailsSent > 0 ? (step.unsubscribes / step.emailsSent) * 100 : 0;
  const bounceRate = step.emailsSent > 0 ? (step.bounces / step.emailsSent) * 100 : 0;

  const bouncesInfo: MetricInfo = {
    title: "Rebotes",
    description:
      "Promedio industria: 0.58%. Rebotes altos = lista desactualizada o emails inválidos. Afecta la reputación del dominio.",
  };

  const rows = [
    {
      label: "Open Rate",
      value: step.openRate,
      benchmark: BENCHMARKS.openRate,
      suffix: "%",
      higherBetter: true,
      info: AUTOMATION_METRIC_INFO.openRate,
    },
    {
      label: "Click Rate",
      value: step.clickRate,
      benchmark: BENCHMARKS.clickRate,
      suffix: "%",
      higherBetter: true,
      info: AUTOMATION_METRIC_INFO.clickRate,
    },
    {
      label: "CTOR",
      value: ctor,
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
      value: bounceRate,
      benchmark: BENCHMARKS.bounceRate,
      suffix: "%",
      higherBetter: false,
      info: bouncesInfo,
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

function PreviewSection({ step }: { step: AutomationStep }) {
  return (
    <section>
      <h4 className="mb-3 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
        Vista previa del email
      </h4>
      <div className="rounded-lg border bg-card overflow-hidden">
        {step.screenshotUrl ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={step.screenshotUrl}
            alt={`Vista previa de ${step.subject ?? "email"}`}
            className="w-full object-cover max-h-[320px]"
          />
        ) : (
          <div className="flex h-32 items-center justify-center bg-muted/10 text-xs text-muted-foreground">
            Sin vista previa disponible
          </div>
        )}
        <div className="flex items-center justify-between border-t px-3 py-2">
          <a
            href={step.previewUrl ?? "#"}
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

function DiagnosisSection({
  step,
  previousStep,
}: {
  step: AutomationStep;
  previousStep: AutomationStep | null;
}) {
  const insights = diagnoseStep(step, previousStep ?? undefined);
  const hasIssues = insights.length > 0;

  return (
    <section>
      <h4 className="mb-3 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
        Diagnóstico Inteligente
      </h4>
      <div className="rounded-lg border border-primary/20 bg-primary/5 px-4 py-3">
        <h5 className="mb-2 flex items-center gap-1.5 text-[11px] font-semibold text-primary">
          <Sparkles className="h-3 w-3" />
          Análisis de este email
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
            Este email tiene performance saludable. Considera replicar su estructura (subject, tono,
            CTA) en otros emails de la secuencia.
          </p>
        )}
      </div>
    </section>
  );
}

function DetailsSection({ step, totalSteps }: { step: AutomationStep; totalSteps: number }) {
  return (
    <section>
      <h4 className="mb-3 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
        Detalles del email
      </h4>
      <div className="rounded-lg border bg-card p-3.5 space-y-2">
        <DetailRow label="Subject" value={step.subject ?? "—"} />
        <DetailRow label="De" value={step.fromName ?? "—"} />
        <DetailRow label="Posición" value={`${step.stepNumber} de ${totalSteps}`} />
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
