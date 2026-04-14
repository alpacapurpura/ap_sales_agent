"use client";

import { useState } from "react";
import {
  AlertCircle,
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
} from "lucide-react";

import { cn } from "@/lib/utils";
import type { NoticeSeverity, NoticeTab, NoticesSummary } from "./types";

export type MetaAdsDashboardTab = "resumen" | "campanas" | "creativos" | "audiencia" | "costos";

interface ResumenHealthOverviewProps {
  summary: NoticesSummary;
  /** Navigate to a tab and auto-open its notices panel. */
  onNavigateToTab: (tab: MetaAdsDashboardTab) => void;
  className?: string;
}

const TAB_META: Array<{
  key: NoticeTab;
  label: string;
  routeKey: MetaAdsDashboardTab;
}> = [
  { key: "campanas", label: "Campañas", routeKey: "campanas" },
  { key: "creativos", label: "Creativos", routeKey: "creativos" },
  { key: "audiencia", label: "Audiencia", routeKey: "audiencia" },
  { key: "costos", label: "Costos", routeKey: "costos" },
];

function dominantSeverity(summary: NoticesSummary): NoticeSeverity {
  if (summary.severity.critical > 0) return "critical";
  if (summary.severity.warning > 0) return "warning";
  return "info";
}

function borderClass(sev: NoticeSeverity): string {
  switch (sev) {
    case "critical":
      return "border-red-500/40 bg-red-500/5";
    case "warning":
      return "border-amber-500/30 bg-amber-500/5";
    case "info":
      return "border-blue-500/30 bg-blue-500/5";
  }
}

function iconFor(sev: NoticeSeverity) {
  if (sev === "critical") {
    return <AlertCircle className="h-5 w-5 text-red-500" aria-hidden="true" />;
  }
  if (sev === "warning") {
    return <AlertTriangle className="h-5 w-5 text-amber-500" aria-hidden="true" />;
  }
  return <CheckCircle2 className="h-5 w-5 text-blue-500" aria-hidden="true" />;
}

function severityDotClass(sev: NoticeSeverity): string {
  switch (sev) {
    case "critical":
      return "bg-red-500";
    case "warning":
      return "bg-amber-500";
    case "info":
      return "bg-blue-500";
  }
}

function pluralize(n: number, singular: string, plural: string): string {
  return n === 1 ? singular : plural;
}

function subtitle(summary: NoticesSummary): string {
  const parts: string[] = [];
  if (summary.severity.critical > 0) {
    parts.push(
      `${summary.severity.critical} ${pluralize(summary.severity.critical, "crítica", "críticas")}`,
    );
  }
  if (summary.severity.warning > 0) {
    parts.push(
      `${summary.severity.warning} ${pluralize(summary.severity.warning, "advertencia", "advertencias")}`,
    );
  }
  if (summary.severity.info > 0) {
    parts.push(
      `${summary.severity.info} ${pluralize(summary.severity.info, "recomendación", "recomendaciones")}`,
    );
  }
  return parts.join(" · ");
}

/**
 * Resumen-tab health overview.
 *
 * - Zero notices: celebratory empty state ("Todo en orden").
 * - 1+ notices: collapsible panel with "Tienes N cosas por mejorar" header and,
 *   when expanded, a list of tabs that have pending notices with direct CTAs.
 *
 * The user never clicks a notice directly from Resumen — Resumen is an index,
 * not a list. Clicking a tab CTA navigates to the tab where the notice lives
 * and auto-expands its ImprovementNotesPanel.
 */
export function ResumenHealthOverview({
  summary,
  onNavigateToTab,
  className,
}: ResumenHealthOverviewProps) {
  const [expanded, setExpanded] = useState(false);

  // Empty state — reassure the user everything is fine.
  if (summary.total === 0) {
    return (
      <div
        className={cn("rounded-lg border border-emerald-500/30 bg-emerald-500/5 p-4", className)}
        data-testid="resumen-health-empty"
      >
        <div className="flex items-start gap-3">
          <CheckCircle2 className="h-5 w-5 text-emerald-500 mt-0.5" aria-hidden="true" />
          <div>
            <h3 className="text-sm font-semibold text-emerald-50">Todo en orden</h3>
            <p className="mt-0.5 text-xs text-muted-foreground">
              No detectamos nada urgente en tus campañas activas. Seguí así.
            </p>
          </div>
        </div>
      </div>
    );
  }

  const sev = dominantSeverity(summary);
  const headerTitle = `Tienes ${summary.total} ${pluralize(
    summary.total,
    "cosa por mejorar",
    "cosas por mejorar",
  )}`;
  const tabsWithNotices = TAB_META.filter((meta) => summary.perTabCounts[meta.key] > 0);

  return (
    <div
      className={cn("rounded-lg border p-4", borderClass(sev), className)}
      data-testid="resumen-health-panel"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex min-w-0 items-start gap-3">
          {iconFor(sev)}
          <div className="min-w-0">
            <h3 className="text-sm font-semibold">{headerTitle}</h3>
            <p className="mt-0.5 text-xs text-muted-foreground">
              {subtitle(summary) || "Revisá los detalles en cada pestaña."}
            </p>
          </div>
        </div>
        <button
          type="button"
          onClick={() => setExpanded((v) => !v)}
          aria-label={expanded ? "Ocultar detalle" : "Ver detalle"}
          className="shrink-0 rounded-md p-1 text-muted-foreground hover:text-foreground"
        >
          {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </button>
      </div>

      {expanded && (
        <div className="mt-4 space-y-1.5">
          {tabsWithNotices.map((meta) => {
            const count = summary.perTabCounts[meta.key];
            const maxSev = summary.maxSeverityPerTab[meta.key] ?? "info";
            return (
              <button
                key={meta.key}
                type="button"
                onClick={() => onNavigateToTab(meta.routeKey)}
                className="flex w-full items-center justify-between rounded-md border border-border bg-card px-3 py-2 text-left transition-colors hover:bg-muted"
              >
                <div className="flex items-center gap-2.5">
                  <span
                    className={cn(
                      "inline-block h-2 w-2 shrink-0 rounded-full",
                      severityDotClass(maxSev),
                    )}
                  />
                  <div>
                    <p className="text-sm font-medium">{meta.label}</p>
                    <p className="text-[11px] text-muted-foreground">
                      {count} {pluralize(count, "pendiente", "pendientes")}
                    </p>
                  </div>
                </div>
                <span
                  className="inline-flex items-center gap-1 text-[11px] font-medium text-foreground"
                  aria-label={`Ir a ${meta.label}`}
                >
                  Ir a {meta.label}
                  <ArrowRight className="h-3 w-3" aria-hidden="true" />
                </span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
