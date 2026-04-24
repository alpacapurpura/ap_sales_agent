"use client";

import { Check, Loader2, Wrench } from "lucide-react";
import { memo } from "react";

import { cn } from "@/lib/utils";

import { useAsyncToolJob } from "../../hooks/use-async-tool-job";
import { humanizeToolName } from "../../utils/tool-labels";

interface ToolCallChipProps {
  tool: string;
  status?: "running" | "done";
  /** Job id from the async extraction tool result. When present, renders extended live layout. */
  jobId?: string;
  className?: string;
}

// ── Extended layout (with jobId) ─────────────────────────────────────────────

interface ExtendedChipProps {
  tool: string;
  jobId: string;
  legacyStatus: "running" | "done";
  className?: string;
}

const ExtendedToolCallChip = memo(function ExtendedToolCallChip({
  tool,
  jobId,
  legacyStatus,
  className,
}: ExtendedChipProps) {
  const job = useAsyncToolJob(jobId);
  const label = humanizeToolName(tool);

  // When a jobId is present, the LLM tool handler's status is misleading:
  // the tool returned a dispatch envelope ("done" from the LLM's perspective)
  // while the actual ARQ worker is still running for 1-2 minutes. Trust the
  // polled job.status over legacyStatus; only use legacyStatus as a last-resort
  // for the first few frames before the store update lands.
  void legacyStatus;
  const status = job?.status ?? "queued";
  const isRunning = status === "running" || status === "queued";
  const isCompleted = status === "completed" || status === "failed";
  const progress = job?.progress ?? 0;
  const stage = job?.stage ?? "";
  const fieldCount = job?.filledFields?.length ?? 0;
  const sectionCount = job?.sectionsCompleted?.length ?? 0;

  if (isCompleted) {
    // Collapsed pill — success tint
    return (
      <div
        role="status"
        aria-live="polite"
        aria-label={`Herramienta: ${label}, completada — ${fieldCount} campos, ${sectionCount} secciones`}
        className={cn(
          "rounded-xl border border-success/30 bg-success/5 px-3 py-2 text-[11px] shadow-sm",
          "animate-in fade-in slide-in-from-bottom-1 duration-200",
          className,
        )}
      >
        <div className="flex items-center gap-1.5 font-medium text-success">
          <Check className="h-3 w-3 shrink-0" aria-hidden="true" />
          <Wrench className="h-3 w-3 shrink-0 opacity-60" aria-hidden="true" />
          <span className="truncate font-mono text-[10.5px] tracking-tight">{label}</span>
        </div>
        {(fieldCount > 0 || sectionCount > 0) && (
          <div className="mt-1 text-[10px] text-success/70">
            {fieldCount > 0 && `${fieldCount} campos`}
            {fieldCount > 0 && sectionCount > 0 && " · "}
            {sectionCount > 0 && `${sectionCount} secciones`}
          </div>
        )}
      </div>
    );
  }

  // Expanded 4-row layout while running / queued
  return (
    <div
      role="status"
      aria-live="polite"
      aria-label={`Herramienta: ${label}, en progreso ${progress}%`}
      className={cn(
        "rounded-xl border border-border bg-background/60 px-3 py-2 text-[11px] shadow-sm backdrop-blur-sm",
        "animate-in fade-in slide-in-from-bottom-1 duration-200",
        className,
      )}
    >
      {/* Row 1: icon + label + percentage */}
      <div className="flex items-center gap-1.5 font-medium text-muted-foreground">
        {isRunning ? (
          <Loader2 className="h-3 w-3 shrink-0 animate-spin text-brand" aria-hidden="true" />
        ) : (
          <Wrench className="h-3 w-3 shrink-0 opacity-60" aria-hidden="true" />
        )}
        <Wrench className="h-3 w-3 shrink-0 opacity-60" aria-hidden="true" />
        <span className="flex-1 truncate font-mono text-[10.5px] tracking-tight">{label}</span>
        <span className="shrink-0 tabular-nums text-brand">{progress}%</span>
      </div>

      {/* Row 2: progress bar */}
      <div className="relative mt-1.5 h-1 w-full overflow-hidden rounded-full bg-muted">
        <div
          data-testid="job-progress-bar"
          className="absolute left-0 top-0 h-full rounded-full bg-brand transition-all duration-500"
          style={{ width: `${progress}%` }}
          aria-hidden="true"
        />
      </div>

      {/* Row 3: stage text */}
      {stage && <div className="mt-1 truncate text-[10px] text-muted-foreground">{stage}</div>}

      {/* Row 4: optional counters */}
      {(fieldCount > 0 || sectionCount > 0) && (
        <div className="mt-0.5 text-[10px] text-muted-foreground/70">
          {fieldCount > 0 && `${fieldCount} campos`}
          {fieldCount > 0 && sectionCount > 0 && " · "}
          {sectionCount > 0 && `${sectionCount} secciones`}
        </div>
      )}
    </div>
  );
});
ExtendedToolCallChip.displayName = "ExtendedToolCallChip";

// ── Legacy layout (no jobId) ─────────────────────────────────────────────────

export const ToolCallChip = memo(function ToolCallChip({
  tool,
  status = "running",
  jobId,
  className,
}: ToolCallChipProps) {
  if (jobId) {
    return (
      <ExtendedToolCallChip tool={tool} jobId={jobId} legacyStatus={status} className={className} />
    );
  }

  const label = humanizeToolName(tool);
  const isRunning = status === "running";

  return (
    <div
      role="status"
      aria-live="polite"
      aria-label={`Herramienta: ${label}${isRunning ? ", en progreso" : ", completada"}`}
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border border-border bg-background/60 px-2.5 py-1 text-[11px] font-medium text-muted-foreground shadow-sm backdrop-blur-sm",
        "animate-in fade-in slide-in-from-bottom-1 duration-200",
        className,
      )}
    >
      {isRunning ? (
        <Loader2 className="h-3 w-3 shrink-0 animate-spin text-brand" aria-hidden="true" />
      ) : (
        <Check className="h-3 w-3 shrink-0 text-success" aria-hidden="true" />
      )}
      <Wrench className="h-3 w-3 shrink-0 opacity-60" aria-hidden="true" />
      <span className="truncate font-mono text-[10.5px] tracking-tight">{label}</span>
    </div>
  );
});
ToolCallChip.displayName = "ToolCallChip";
