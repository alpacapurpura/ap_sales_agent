"use client";

import { CheckCircle2 } from "lucide-react";
import { memo } from "react";

import { useBrandSectionLabelResolver } from "@/features/brand-studio/hooks/use-brand-section-catalog";
import { useSectionLabelResolver as useOfferSectionLabelResolver } from "@/features/offer-studio/hooks/use-section-catalog";
import { cn } from "@/lib/utils";

import { useCopilotNavigator } from "../../hooks/use-copilot-navigator";

import type { ExtractionSummaryData } from "../../types/message-blocks";

interface ExtractionSummaryCardProps {
  data: ExtractionSummaryData;
  className?: string;
}

/** Resolve a human-readable Spanish label for a section slug.
 *
 * The backend emits ``label = slug``; the single source of truth is the
 * section catalog served by the BE — offer via ``useSectionLabelResolver``
 * (``/api/v1/offer/archetypes/catalog``) and brand via
 * ``useBrandSectionLabelResolver`` (``/api/v1/brand/sections/catalog``).
 * If ``module`` is absent or the slug is unknown, we fall back to the
 * label the payload already carries, then to the slug itself.
 */
interface ResolveSectionLabelParams {
  slug: string;
  payloadLabel: string;
  module: ExtractionSummaryData["module"];
  resolveOfferLabel: (slug: string) => string;
  resolveBrandLabel: (slug: string) => string;
}

function resolveSectionLabel({
  slug,
  payloadLabel,
  module,
  resolveOfferLabel,
  resolveBrandLabel,
}: ResolveSectionLabelParams): string {
  if (module === "brand") return resolveBrandLabel(slug);
  if (module === "offer") return resolveOfferLabel(slug);
  return payloadLabel || slug;
}

/** Coverage threshold for color classification. */
function coverageColor(filled: number, total: number): string {
  if (total === 0) return "bg-muted";
  const ratio = filled / total;
  if (ratio >= 0.7) return "bg-success";
  if (ratio >= 0.4) return "bg-warning";
  return "bg-destructive";
}

/** Format source_ref for display: strip protocol and trailing slash. */
function formatRef(ref: string): string {
  return ref.replace(/^https?:\/\//, "").replace(/\/$/, "");
}

/**
 * Renders the extraction completion summary card.
 *
 * Emitted by the backend worker on job completion via card_kind="extraction_summary".
 * Mirrors ClarifyCard visual tokens — same shell, border, ring, padding.
 */
export const ExtractionSummaryCard = memo(function ExtractionSummaryCard({
  data,
  className,
}: ExtractionSummaryCardProps) {
  const {
    source_ref,
    module,
    duration_seconds,
    total_fields,
    total_sections,
    coverage_by_section,
    strong_assumptions_count,
    open_questions_count,
    primary_cta_route,
  } = data;

  const { executeAction } = useCopilotNavigator();
  const resolveOfferLabel = useOfferSectionLabelResolver();
  const resolveBrandLabel = useBrandSectionLabelResolver();

  // Resolve display labels from the canonical catalog when possible.
  const resolvedSections = coverage_by_section.map((s) => ({
    ...s,
    label: resolveSectionLabel({
      slug: s.slug,
      payloadLabel: s.label,
      module,
      resolveOfferLabel,
      resolveBrandLabel,
    }),
  }));

  const primarySectionLabel = resolvedSections[0]?.label ?? "la sección principal";

  const handleReview = (): void => {
    executeAction({ type: "navigate", route: primary_cta_route });
  };

  const handleViewQuestions = (): void => {
    // Dispatch a chat message — kept simple as the full CTA flow is backend-driven
    window.dispatchEvent(
      new CustomEvent("copilot:field-update", {
        detail: { fieldId: "__open_questions__", newValue: null },
      }),
    );
  };

  return (
    <div
      role="group"
      aria-label="Resumen de extracción"
      className={cn(
        "animate-in slide-in-from-bottom-2 fade-in duration-300",
        "rounded-xl border border-border bg-card p-3.5 text-card-foreground shadow-sm",
        "ring-1 ring-brand/10",
        className,
      )}
    >
      {/* ── Header ─────────────────────────────────────────────────── */}
      <div className="mb-3 flex items-center gap-2 text-xs font-semibold text-foreground">
        <span
          className="flex h-5 w-5 items-center justify-center rounded-full bg-success/15 text-success"
          aria-hidden="true"
        >
          <CheckCircle2 className="h-3.5 w-3.5" />
        </span>
        <span className="flex-1 truncate">
          Listo — analicé{" "}
          <span className="font-mono text-[10px] font-normal text-muted-foreground">
            {formatRef(source_ref)}
          </span>
        </span>
        <span className="shrink-0 text-[10px] font-normal text-muted-foreground">
          {duration_seconds}s
        </span>
      </div>

      {/* ── Stat boxes ─────────────────────────────────────────────── */}
      <div className="mb-3 flex gap-2">
        <div className="flex-1 rounded-lg border border-border/60 bg-muted/40 p-2.5 text-center">
          <div className="text-lg font-bold leading-none text-foreground">{total_fields}</div>
          <div className="mt-0.5 text-[10px] text-muted-foreground">campos</div>
        </div>
        <div className="flex-1 rounded-lg border border-border/60 bg-muted/40 p-2.5 text-center">
          <div className="text-lg font-bold leading-none text-foreground">{total_sections}</div>
          <div className="mt-0.5 text-[10px] text-muted-foreground">secciones</div>
        </div>
      </div>

      {/* ── Coverage by section ─────────────────────────────────────── */}
      {resolvedSections.length > 0 && (
        <div className="mb-3">
          <div className="mb-1.5 text-[9px] font-semibold uppercase tracking-wider text-muted-foreground">
            Cobertura por sección
          </div>
          <div className="flex flex-col gap-1">
            {resolvedSections.map((section) => (
              <div key={section.slug} className="flex items-center gap-2 text-[10.5px]">
                <span className="w-20 shrink-0 truncate text-foreground">{section.label}</span>
                <div className="relative h-1.5 flex-1 overflow-hidden rounded-full bg-muted">
                  <div
                    data-testid="coverage-bar-fill"
                    className={cn(
                      "absolute left-0 top-0 h-full rounded-full transition-all duration-500",
                      coverageColor(section.filled, section.total),
                    )}
                    style={{
                      width: `${section.total > 0 ? Math.round((section.filled / section.total) * 100) : 0}%`,
                    }}
                    aria-label={`${section.label}: ${section.filled} de ${section.total}`}
                  />
                </div>
                <span className="w-10 shrink-0 text-right text-muted-foreground">
                  {section.filled}/{section.total}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Assumptions & questions summary ────────────────────────── */}
      <div className="mb-3 text-[10.5px] text-muted-foreground">
        <span>Supuestos: </span>
        <span className="font-medium text-foreground">{strong_assumptions_count}</span>
        <span className="mx-1.5">·</span>
        <span>Preguntas: </span>
        <span className="font-medium text-foreground">{open_questions_count}</span>
      </div>

      {/* ── CTAs ───────────────────────────────────────────────────── */}
      <div className="flex flex-wrap gap-1.5">
        <button
          type="button"
          onClick={handleReview}
          className={cn(
            "rounded-md border border-brand/40 bg-brand/10 px-2.5 py-1 text-[11px] font-medium text-brand",
            "transition-colors duration-150 active:scale-[0.98]",
            "hover:bg-brand/20",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand/60 focus-visible:ring-offset-1 focus-visible:ring-offset-background",
          )}
        >
          Revisar {primarySectionLabel} →
        </button>

        {open_questions_count > 0 && (
          <button
            type="button"
            onClick={handleViewQuestions}
            className={cn(
              "rounded-md border border-border bg-background px-2.5 py-1 text-[11px] font-medium text-foreground",
              "transition-colors duration-150 active:scale-[0.98]",
              "hover:border-brand/60 hover:bg-brand/10 hover:text-brand",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand/60 focus-visible:ring-offset-1 focus-visible:ring-offset-background",
            )}
          >
            Ver preguntas ({open_questions_count})
          </button>
        )}

        {strong_assumptions_count > 0 && (
          <button
            type="button"
            onClick={() => {
              /* Future: open assumptions panel */
            }}
            className={cn(
              "rounded-md border border-border bg-background px-2.5 py-1 text-[11px] font-medium text-foreground",
              "transition-colors duration-150 active:scale-[0.98]",
              "hover:border-brand/60 hover:bg-brand/10 hover:text-brand",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand/60 focus-visible:ring-offset-1 focus-visible:ring-offset-background",
            )}
          >
            Ver supuestos
          </button>
        )}
      </div>
    </div>
  );
});
ExtractionSummaryCard.displayName = "ExtractionSummaryCard";
