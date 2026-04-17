"use client";

import { ChevronLeft, Plus } from "lucide-react";
import { useRouter } from "next/navigation";
import { useMemo } from "react";

import { cn } from "@/lib/utils";

import { EditionStatus, EditionVisibility } from "../../types";

import type { LaunchEdition } from "../../types";

export interface EditionsRailProps {
  offerId: string;
  offerName: string;
  tenantId: string;
  editions: LaunchEdition[];
  currentEditionId: string | null;
  waitlistCount?: number;
  onCollapse: () => void;
  onCreateNew: () => void;
}

interface Group {
  key: "active" | "upcoming" | "drafts" | "past";
  label: string;
  tone: "active" | "next" | "draft" | "past";
  items: LaunchEdition[];
}

function groupEditions(editions: LaunchEdition[]): Group[] {
  const active = editions.filter((e) => e.status === EditionStatus.ACTIVE);
  const upcoming = editions.filter((e) => e.status === EditionStatus.UPCOMING);
  const drafts = editions.filter((e) => e.status === EditionStatus.DRAFT);
  const past = editions
    .filter((e) => e.status === EditionStatus.COMPLETED || e.status === EditionStatus.CANCELLED)
    // Most-recent past edition first.
    .sort((a, b) => ((a.start_date ?? "") > (b.start_date ?? "") ? -1 : 1));

  const groups: Group[] = [
    { key: "active", label: "🔴 En curso", tone: "active", items: active },
    { key: "upcoming", label: "⭐ Próxima", tone: "next", items: upcoming },
    { key: "drafts", label: "✏ Borradores", tone: "draft", items: drafts },
    { key: "past", label: "✓ Pasadas", tone: "past", items: past },
  ];
  return groups.filter((g) => g.items.length > 0);
}

function formatShortDate(iso: string | null | undefined): string {
  if (!iso) return "Sin fecha";
  const d = new Date(iso);
  return d.toLocaleDateString("es-PE", {
    day: "2-digit",
    month: "short",
  });
}

function formatMonthYear(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleDateString("es-PE", { month: "short", year: "2-digit" });
}

/**
 * Secondary left-rail for the Offer Studio shell.
 *
 * Renders a vertical list of editions grouped by status. The "próxima"
 * (next upcoming + public) entry is highlighted; drafts show dashed
 * amber borders; past editions sit minimal at the bottom. Clicking an
 * entry replaces the `?edition=` query param so the tab body re-scopes.
 */
export function EditionsRail({
  offerId,
  offerName,
  tenantId,
  editions,
  currentEditionId,
  waitlistCount = 0,
  onCollapse,
  onCreateNew,
}: EditionsRailProps) {
  const router = useRouter();
  const groups = useMemo(() => groupEditions(editions), [editions]);

  const switchEdition = (editionId: string) => {
    const base = `/${tenantId}/offer-studio/offer/${offerId}`;
    router.replace(`${base}?edition=${editionId}`);
  };

  return (
    <aside
      aria-label="Ediciones de la oferta"
      className="flex w-60 shrink-0 flex-col border-r bg-background"
    >
      <header className="flex items-center justify-between border-b px-3 py-3">
        <span className="min-w-0 truncate text-sm font-semibold" title={offerName}>
          {offerName}
        </span>
        <button
          type="button"
          onClick={onCollapse}
          aria-label="Contraer rail"
          className="rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
        >
          <ChevronLeft className="h-4 w-4" aria-hidden />
        </button>
      </header>

      <div className="flex-1 space-y-4 overflow-y-auto p-2 text-sm">
        {groups.length === 0 ? (
          <EmptyState onCreateNew={onCreateNew} />
        ) : (
          groups.map((group) => (
            <div key={group.key}>
              <p
                className={cn(
                  "px-2 pb-1.5 text-[10px] font-semibold uppercase tracking-wider",
                  group.tone === "draft" ? "text-amber-600" : "text-muted-foreground",
                )}
              >
                {group.label}
              </p>
              <ul className="space-y-1">
                {group.items.map((edition) => (
                  <li key={edition.id}>
                    <EditionEntry
                      edition={edition}
                      tone={group.tone}
                      isSelected={edition.id === currentEditionId}
                      waitlistCount={
                        group.tone === "draft" && edition.id === currentEditionId
                          ? waitlistCount
                          : 0
                      }
                      onClick={() => switchEdition(edition.id)}
                    />
                  </li>
                ))}
              </ul>
            </div>
          ))
        )}
      </div>

      <footer className="border-t p-2">
        <button
          type="button"
          onClick={onCreateNew}
          className="flex w-full items-center justify-center gap-1.5 rounded-lg bg-primary px-3 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          <Plus className="h-4 w-4" aria-hidden /> Nueva edición
        </button>
        <p className="mt-1.5 text-center text-[10px] text-muted-foreground">Clonar recomendado</p>
      </footer>
    </aside>
  );
}

// ─────────────────────────────────────────────────────────────────────────────

interface EntryProps {
  edition: LaunchEdition;
  tone: Group["tone"];
  isSelected: boolean;
  waitlistCount: number;
  onClick: () => void;
}

const TONE_CLASSES_SELECTED: Record<Group["tone"], string> = {
  active: "bg-emerald-50 border-emerald-200 ring-1 ring-emerald-200/50",
  next: "bg-blue-50 border-blue-200 ring-1 ring-blue-200/50",
  draft: "border-amber-400 bg-amber-50",
  past: "bg-muted border-border",
};

const TONE_CLASSES_IDLE: Record<Group["tone"], string> = {
  active: "hover:bg-emerald-50/60",
  next: "hover:bg-blue-50/60",
  draft: "border-dashed border-amber-300 hover:bg-amber-50",
  past: "hover:bg-muted/50",
};

const TONE_TITLE_CLASSES: Record<Group["tone"], string> = {
  active: "text-emerald-900",
  next: "text-blue-900",
  draft: "text-amber-800",
  past: "text-muted-foreground",
};

const STATUS_LABELS: Record<EditionStatus, string> = {
  [EditionStatus.DRAFT]: "Borrador",
  [EditionStatus.UPCOMING]: "Próxima",
  [EditionStatus.ACTIVE]: "En curso",
  [EditionStatus.COMPLETED]: "Completa",
  [EditionStatus.CANCELLED]: "Cancelada",
};

function EditionEntry({ edition, tone, isSelected, waitlistCount, onClick }: EntryProps) {
  const isPublic = edition.visibility === EditionVisibility.PUBLIC;
  const toneClass = isSelected ? TONE_CLASSES_SELECTED[tone] : TONE_CLASSES_IDLE[tone];

  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={isSelected}
      aria-current={isSelected ? "true" : undefined}
      className={cn(
        "block w-full rounded-lg border border-transparent p-2.5 text-left transition-colors",
        toneClass,
      )}
    >
      <div className="flex items-center justify-between">
        <span className={cn("text-sm font-semibold", TONE_TITLE_CLASSES[tone])}>
          Edición #{edition.edition_number}
        </span>
        <span className="text-[10px] uppercase tracking-wider text-muted-foreground">
          {STATUS_LABELS[edition.status]}
        </span>
      </div>
      <p className="mt-1 text-xs text-muted-foreground">
        {edition.status === EditionStatus.COMPLETED || edition.status === EditionStatus.CANCELLED
          ? formatMonthYear(edition.start_date)
          : formatShortDate(edition.start_date)}
      </p>
      {edition.capacity ? (
        <p className="text-xs text-muted-foreground">
          {edition.enrollment_count}/{edition.capacity}
          {isPublic ? " · 🌐 Pública" : " · 🔒 Privada"}
        </p>
      ) : null}
      {waitlistCount > 0 ? (
        <p className="mt-1 text-xs text-purple-700">⚠ {waitlistCount} en waitlist</p>
      ) : null}
    </button>
  );
}

function EmptyState({ onCreateNew }: { onCreateNew: () => void }) {
  return (
    <div className="flex flex-col items-center gap-2 py-8 text-center">
      <p className="text-xs text-muted-foreground">Sin ediciones todavía</p>
      <button
        type="button"
        onClick={onCreateNew}
        className="rounded-md bg-primary px-2.5 py-1 text-xs font-medium text-primary-foreground hover:bg-primary/90"
      >
        Crear primera edición
      </button>
    </div>
  );
}
