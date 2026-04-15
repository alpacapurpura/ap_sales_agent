"use client";

import {
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  EyeOff,
} from "lucide-react";
import { useState } from "react";

import { cn } from "@/lib/utils";

import type { ImprovementNotice, NoticeSeverity, SeverityBreakdown } from "./types";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

export interface ImprovementNotesPanelProps {
  /** Notices to render inside this panel. Empty array = panel renders nothing. */
  notices: ImprovementNotice[];
  /** Severity breakdown across the notices (drives the header chip row). */
  severity: SeverityBreakdown;
  /**
   * If true, the panel starts expanded on mount instead of the default
   * (collapsed). Use this when navigating from the Resumen overview with a
   * deep-link so the user does not need to click again.
   */
  forceOpen?: boolean;
  /** Called when the user clicks "Ignorar" on a notice (24h dismiss). */
  onIgnore?: (noticeId: string) => void;
  /** Called when the user clicks "Ver en detalle" to jump to the affected object. */
  onNoticeClick?: (notice: ImprovementNotice) => void;
  /** Optional override for the collapsed-header title. Defaults to "Tienes N cosas por mejorar". */
  headerTitle?: string;
  /** Extra class for the outer wrapper. */
  className?: string;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function dominantSeverity(severity: SeverityBreakdown): NoticeSeverity {
  if (severity.critical > 0) return "critical";
  if (severity.warning > 0) return "warning";
  return "info";
}

function severityBorderClass(sev: NoticeSeverity): string {
  switch (sev) {
    case "critical":
      return "border-red-500/40 bg-red-500/5";
    case "warning":
      return "border-amber-500/30 bg-amber-500/5";
    case "info":
      return "border-blue-500/30 bg-blue-500/5";
  }
}

function severityIcon(sev: NoticeSeverity) {
  if (sev === "critical") {
    return <AlertCircle className="h-5 w-5 text-red-500" aria-hidden="true" />;
  }
  if (sev === "warning") {
    return <AlertTriangle className="h-5 w-5 text-amber-500" aria-hidden="true" />;
  }
  return <CheckCircle2 className="h-5 w-5 text-blue-500" aria-hidden="true" />;
}

function severityLeftBar(sev: NoticeSeverity): string {
  switch (sev) {
    case "critical":
      return "border-l-red-500 bg-red-500/5";
    case "warning":
      return "border-l-amber-500 bg-amber-500/5";
    case "info":
      return "border-l-blue-500 bg-blue-500/5";
  }
}

function pluralize(n: number, singular: string, plural: string): string {
  return n === 1 ? singular : plural;
}

function buildHeaderSubtitle(severity: SeverityBreakdown): string {
  const parts: string[] = [];
  if (severity.critical > 0) {
    parts.push(`${severity.critical} ${pluralize(severity.critical, "crítica", "críticas")}`);
  }
  if (severity.warning > 0) {
    parts.push(`${severity.warning} ${pluralize(severity.warning, "advertencia", "advertencias")}`);
  }
  if (severity.info > 0) {
    parts.push(`${severity.info} ${pluralize(severity.info, "recomendación", "recomendaciones")}`);
  }
  return parts.join(" · ");
}

// ---------------------------------------------------------------------------
// Notice card
// ---------------------------------------------------------------------------

interface NoticeCardProps {
  notice: ImprovementNotice;
  onIgnore?: (id: string) => void;
  onClick?: (notice: ImprovementNotice) => void;
}

function NoticeCard({ notice, onIgnore, onClick }: NoticeCardProps) {
  return (
    <div
      className={cn(
        "rounded-md border border-l-[3px] border-border p-3",
        severityLeftBar(notice.severity),
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-1.5">
            <p className="text-sm font-medium text-foreground">{notice.title}</p>
            {notice.contextLabel && (
              <span className="inline-flex items-center rounded-full bg-muted px-2 py-0.5 text-[10px] font-medium text-muted-foreground">
                {notice.contextLabel}
              </span>
            )}
          </div>
          {notice.body && <p className="mt-0.5 text-[11px] text-muted-foreground">{notice.body}</p>}
        </div>
        <div className="flex shrink-0 items-center gap-1">
          {onClick && (
            <button
              type="button"
              onClick={() => onClick(notice)}
              className="rounded-md border border-border bg-background px-2.5 py-1 text-[11px] font-medium text-foreground hover:bg-muted"
            >
              Ver en detalle
            </button>
          )}
          {onIgnore && (
            <button
              type="button"
              onClick={() => onIgnore(notice.id)}
              aria-label="Ignorar por 24 horas"
              title="Ignorar por 24 horas"
              className="inline-flex items-center gap-1 rounded-md border border-transparent px-2 py-1 text-[11px] font-medium text-muted-foreground hover:border-border hover:bg-muted"
            >
              <EyeOff className="h-3 w-3" aria-hidden="true" />
              Ignorar
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main panel
// ---------------------------------------------------------------------------

/**
 * Collapsible panel of improvement notices. Collapsed by default on mount,
 * unless `forceOpen` is true. Shows a summary of how many things need
 * attention in the collapsed state, with a severity breakdown.
 *
 * If `notices` is empty, this component renders nothing — empty state is the
 * caller's responsibility (Resumen shows a celebratory "Todo en orden" block;
 * per-tab usage just hides the panel).
 */
export function ImprovementNotesPanel({
  notices,
  severity,
  forceOpen = false,
  onIgnore,
  onNoticeClick,
  headerTitle,
  className,
}: ImprovementNotesPanelProps) {
  const [expanded, setExpanded] = useState(forceOpen);

  if (notices.length === 0) return null;

  const total = notices.length;
  const sev = dominantSeverity(severity);
  const title =
    headerTitle ?? `Tienes ${total} ${pluralize(total, "cosa por mejorar", "cosas por mejorar")}`;
  const subtitle = buildHeaderSubtitle(severity);

  return (
    <div
      className={cn("rounded-lg border p-4", severityBorderClass(sev), className)}
      data-testid="improvement-notes-panel"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex min-w-0 items-start gap-3">
          {severityIcon(sev)}
          <div className="min-w-0">
            <h3 className="text-sm font-semibold">{title}</h3>
            {subtitle && <p className="mt-0.5 text-xs text-muted-foreground">{subtitle}</p>}
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
        <div className="mt-3 space-y-2">
          {notices.map((notice) => (
            <NoticeCard
              key={notice.id}
              notice={notice}
              onIgnore={onIgnore}
              onClick={onNoticeClick}
            />
          ))}
        </div>
      )}
    </div>
  );
}
