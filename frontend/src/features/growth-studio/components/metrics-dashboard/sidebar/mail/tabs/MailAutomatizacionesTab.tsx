"use client";

import React, { useMemo, useState } from "react";
import { Bot, ChevronRight, Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

import { useMailAutomations } from "../../../../../hooks/useMailDashboard";
import type {
  AutomationStep,
  EmailAutomation,
  EmailAutomationsData,
} from "../../../../../types/mail-types";
import type { MetaAdsPeriod } from "../../../../../types/metrics";
import { computeHealthScore } from "../../../../../utils/automation-health";
import {
  AUTOMATION_METRIC_INFO,
  type MetricInfo,
} from "../../../../../utils/automation-metric-info";
import { ChartSection } from "../../shared/ChartSection";
import { AutomationPipeline } from "../components/AutomationPipeline";
import { AutomationStepSidebar } from "../components/AutomationStepSidebar";
import { MetricInfoTooltip } from "../components/MetricInfoTooltip";

interface MailAutomatizacionesTabProps {
  period: MetaAdsPeriod;
}

const TYPE_LABELS: Record<string, { label: string; className: string }> = {
  welcome: { label: "Bienvenida", className: "bg-blue-500/10 text-blue-500" },
  nurture: { label: "Nutrición", className: "bg-purple-500/10 text-purple-500" },
  reengagement: {
    label: "Re-engagement",
    className: "bg-amber-500/10 text-amber-500",
  },
  post_compra: {
    label: "Post-compra",
    className: "bg-emerald-500/10 text-emerald-500",
  },
  workflow: {
    label: "Workflow",
    className: "bg-slate-500/10 text-muted-foreground",
  },
};

const FILTER_OPTIONS: Array<{ value: string; label: string }> = [
  { value: "all", label: "Todas" },
  { value: "welcome", label: "Bienvenida" },
  { value: "nurture", label: "Nutrición" },
  { value: "workflow", label: "Workflow" },
];

export function MailAutomatizacionesTab({ period }: MailAutomatizacionesTabProps) {
  const { data, isLoading } = useMailAutomations(period);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [activeFilter, setActiveFilter] = useState<string>("all");
  const [selectedStep, setSelectedStep] = useState<AutomationStep | null>(null);
  const [selectedAutomation, setSelectedAutomation] = useState<EmailAutomation | null>(null);

  const filteredAutomations = useMemo(() => {
    if (!data) return [];
    if (activeFilter === "all") return data.automations;
    return data.automations.filter((a) => a.automationType === activeFilter);
  }, [data, activeFilter]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!data || data.automations.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 py-24">
        <div className="flex h-16 w-16 items-center justify-center rounded-full bg-amber-500/10">
          <Bot className="h-8 w-8 text-amber-500" />
        </div>
        <div className="text-center">
          <h3 className="text-lg font-semibold">Sin automatizaciones</h3>
          <p className="mt-1 max-w-sm text-sm text-muted-foreground">
            Las automatizaciones se activarán cuando configures secuencias de email en tu proveedor.
          </p>
        </div>
      </div>
    );
  }

  const handleRowToggle = (automationId: string) => {
    setExpandedId(expandedId === automationId ? null : automationId);
  };

  const handleStepClick = (step: AutomationStep, automation: EmailAutomation) => {
    setSelectedStep(step);
    setSelectedAutomation(automation);
  };

  const handleStepSidebarClose = () => {
    setSelectedStep(null);
    setSelectedAutomation(null);
  };

  const previousStepForSelected =
    selectedStep && selectedAutomation
      ? findPreviousEmailStep(selectedAutomation.steps, selectedStep.stepId)
      : null;

  return (
    <>
      <div className="space-y-6 max-w-[1280px] mx-auto">
        {/* KPI row */}
        <ChartSection slug="kpis-automatizaciones">
          <KpiRow data={data} />
        </ChartSection>

        {/* Table with accordion */}
        <ChartSection slug="tabla-automatizaciones">
          <div className="rounded-lg border bg-card overflow-hidden">
            {/* Header bar */}
            <div className="flex items-center justify-between px-5 py-4 border-b">
              <h3 className="text-sm font-semibold">Detalle por Automatización</h3>
              <div className="flex gap-1.5">
                {FILTER_OPTIONS.map((opt) => (
                  <Button
                    key={opt.value}
                    size="sm"
                    variant={activeFilter === opt.value ? "default" : "outline"}
                    onClick={() => setActiveFilter(opt.value)}
                    className="h-7 rounded-full px-3 text-[11px]"
                  >
                    {opt.label}
                  </Button>
                ))}
              </div>
            </div>

            {/* Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead className="border-b">
                  <tr className="text-muted-foreground">
                    <th className="w-7 py-3 px-3" />
                    <TableHeader label="Automatización" info={null} />
                    <TableHeader
                      label="Ingresados"
                      info={AUTOMATION_METRIC_INFO.ingresados}
                      center
                    />
                    <TableHeader
                      label="Completaron"
                      info={AUTOMATION_METRIC_INFO.completaron}
                      center
                    />
                    <TableHeader label="Open Rate" info={AUTOMATION_METRIC_INFO.openRate} center />
                    <TableHeader
                      label="Click Rate"
                      info={AUTOMATION_METRIC_INFO.clickRate}
                      center
                    />
                    <TableHeader label="CTOR" info={AUTOMATION_METRIC_INFO.ctor} center />
                    <TableHeader label="Unsubs" info={AUTOMATION_METRIC_INFO.unsubs} center />
                    <TableHeader label="Salud" info={AUTOMATION_METRIC_INFO.salud} center />
                  </tr>
                </thead>
                <tbody>
                  {filteredAutomations.map((auto) => {
                    const isExpanded = expandedId === auto.automationId;
                    const healthScore = computeHealthScore(auto);
                    const typeInfo = TYPE_LABELS[auto.automationType] ?? TYPE_LABELS.workflow;
                    const completionPct = auto.completionRate.toFixed(0);

                    return (
                      <React.Fragment key={auto.automationId}>
                        <tr
                          onClick={() => handleRowToggle(auto.automationId)}
                          className={cn(
                            "border-b border-border/40 cursor-pointer transition-colors hover:bg-primary/[0.03]",
                            isExpanded && "bg-primary/[0.05]",
                          )}
                        >
                          <td className="py-3 px-3">
                            <ChevronRight
                              className={cn(
                                "h-3.5 w-3.5 text-muted-foreground transition-transform",
                                isExpanded && "rotate-90",
                              )}
                            />
                          </td>
                          <td className="py-3 px-3">
                            <div className="text-xs font-medium max-w-[260px] truncate">
                              {auto.name}
                            </div>
                            <div className="mt-0.5 flex items-center gap-1.5 text-[10px] text-muted-foreground">
                              <span
                                className={cn(
                                  "rounded-full px-2 py-0.5 font-semibold",
                                  typeInfo.className,
                                )}
                              >
                                {typeInfo.label}
                              </span>
                              <span>·</span>
                              <span>
                                {auto.steps.filter((s) => s.type === "email").length} emails
                              </span>
                              <span>·</span>
                              <span
                                className={cn(
                                  "inline-flex items-center gap-1",
                                  auto.status === "active"
                                    ? "text-emerald-500"
                                    : "text-muted-foreground",
                                )}
                              >
                                <span
                                  className={cn(
                                    "h-1.5 w-1.5 rounded-full",
                                    auto.status === "active"
                                      ? "bg-emerald-500"
                                      : "bg-muted-foreground",
                                  )}
                                />
                                {auto.status === "active" ? "Activa" : "Pausada"}
                              </span>
                            </div>
                          </td>
                          <td className="py-3 px-3 text-center tabular-nums">
                            {auto.activeSubscribers}
                          </td>
                          <td className="py-3 px-3 text-center tabular-nums">
                            {auto.completed}{" "}
                            <span className="text-[10px] text-muted-foreground">
                              ({completionPct}%)
                            </span>
                          </td>
                          <td
                            className={cn(
                              "py-3 px-3 text-center font-semibold tabular-nums",
                              rateClass(auto.openRate, 50, 30),
                            )}
                          >
                            {auto.openRate.toFixed(1)}%
                          </td>
                          <td
                            className={cn(
                              "py-3 px-3 text-center font-semibold tabular-nums",
                              rateClass(auto.clickRate, 5, 2),
                            )}
                          >
                            {auto.clickRate.toFixed(1)}%
                          </td>
                          <td
                            className={cn(
                              "py-3 px-3 text-center tabular-nums",
                              rateClass(auto.clickToOpenRate, 15, 8),
                            )}
                          >
                            {auto.clickToOpenRate.toFixed(1)}%
                          </td>
                          <td
                            className={cn(
                              "py-3 px-3 text-center tabular-nums",
                              auto.unsubscribes === 0
                                ? "text-emerald-500"
                                : auto.unsubscribes <= 3
                                  ? "text-amber-500"
                                  : "text-red-500",
                            )}
                          >
                            {auto.unsubscribes}
                          </td>
                          <td className="py-3 px-3">
                            <HealthBar score={healthScore} />
                          </td>
                        </tr>

                        {isExpanded && (
                          <tr className="bg-muted/10">
                            <td colSpan={9} className="px-5 py-5">
                              <AutomationPipeline
                                steps={auto.steps}
                                onStepClick={(step) => handleStepClick(step, auto)}
                              />
                            </td>
                          </tr>
                        )}
                      </React.Fragment>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </ChartSection>
      </div>

      {/* Sidebar */}
      <AutomationStepSidebar
        step={selectedStep}
        automationName={selectedAutomation?.name ?? ""}
        totalSteps={selectedAutomation?.steps.filter((s) => s.type === "email").length ?? 0}
        previousStep={previousStepForSelected}
        onClose={handleStepSidebarClose}
      />
    </>
  );
}

// ─── Sub-components ─────────────────────────────────────────────────

function TableHeader({
  label,
  info,
  center = false,
}: {
  label: string;
  info: MetricInfo | null;
  center?: boolean;
}) {
  return (
    <th
      className={cn(
        "py-3 px-3 font-medium text-[10px] uppercase tracking-wide whitespace-nowrap",
        center ? "text-center" : "text-left",
      )}
    >
      <span className="inline-flex items-center gap-1">
        {label}
        {info && <MetricInfoTooltip info={info} side="bottom" />}
      </span>
    </th>
  );
}

function HealthBar({ score }: { score: number }) {
  const color =
    score >= 70
      ? "bg-emerald-500"
      : score >= 40
        ? "bg-amber-500"
        : score > 0
          ? "bg-red-500"
          : "bg-muted-foreground";

  const textColor =
    score >= 70
      ? "text-emerald-500"
      : score >= 40
        ? "text-amber-500"
        : score > 0
          ? "text-red-500"
          : "text-muted-foreground";

  return (
    <div className="flex items-center gap-2 justify-center">
      <div className="h-1.5 w-12 overflow-hidden rounded-full bg-muted/30">
        <div
          className={cn("h-full rounded-full transition-all", color)}
          style={{ width: `${score}%` }}
        />
      </div>
      <span className={cn("text-xs font-bold tabular-nums", textColor)}>{score || "—"}</span>
    </div>
  );
}

function KpiRow({ data }: { data: EmailAutomationsData }) {
  const totalIngresados = data.automations.reduce((sum, a) => sum + a.activeSubscribers, 0);
  const totalSent = data.automations.reduce((sum, a) => sum + a.emailsSent, 0);
  const avgOpen =
    totalSent > 0
      ? data.automations.reduce((sum, a) => sum + a.openRate * a.emailsSent, 0) / totalSent
      : 0;
  const avgClick =
    totalSent > 0
      ? data.automations.reduce((sum, a) => sum + a.clickRate * a.emailsSent, 0) / totalSent
      : 0;
  const avgHealth =
    data.automations.length > 0
      ? data.automations.reduce((sum, a) => sum + computeHealthScore(a), 0) /
        data.automations.length
      : 0;

  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
      <KpiCard
        label="Ingresados Totales"
        value={String(totalIngresados)}
        info={AUTOMATION_METRIC_INFO.ingresados}
      />
      <KpiCard
        label="Open Rate Promedio"
        value={`${avgOpen.toFixed(1)}%`}
        info={AUTOMATION_METRIC_INFO.openRate}
        valueColor={rateClass(avgOpen, 50, 30)}
      />
      <KpiCard
        label="Click Rate Promedio"
        value={`${avgClick.toFixed(1)}%`}
        info={AUTOMATION_METRIC_INFO.clickRate}
        valueColor={rateClass(avgClick, 5, 2)}
      />
      <KpiCard
        label="Salud General"
        value={`${Math.round(avgHealth)}`}
        suffix="/100"
        info={AUTOMATION_METRIC_INFO.salud}
        valueColor={
          avgHealth >= 70 ? "text-emerald-500" : avgHealth >= 40 ? "text-amber-500" : "text-red-500"
        }
      />
    </div>
  );
}

function KpiCard({
  label,
  value,
  suffix,
  info,
  valueColor,
}: {
  label: string;
  value: string;
  suffix?: string;
  info: MetricInfo;
  valueColor?: string;
}) {
  return (
    <div className="rounded-lg border bg-card px-4 py-3">
      <div className="flex items-center gap-1 text-[10px] uppercase tracking-wide text-muted-foreground">
        {label}
        <MetricInfoTooltip info={info} iconSize="xs" />
      </div>
      <p className={cn("mt-1 text-xl font-bold tabular-nums", valueColor)}>
        {value}
        {suffix && <span className="text-sm font-normal text-muted-foreground">{suffix}</span>}
      </p>
    </div>
  );
}

// ─── Helpers ────────────────────────────────────────────────────────

function rateClass(value: number, goodThreshold: number, midThreshold: number) {
  if (value >= goodThreshold) return "text-emerald-500";
  if (value >= midThreshold) return "text-amber-500";
  return "text-red-500";
}

function findPreviousEmailStep(
  steps: AutomationStep[],
  currentStepId: string,
): AutomationStep | null {
  const idx = steps.findIndex((s) => s.stepId === currentStepId);
  if (idx <= 0) return null;
  for (let i = idx - 1; i >= 0; i--) {
    if (steps[i].type === "email") return steps[i];
  }
  return null;
}
