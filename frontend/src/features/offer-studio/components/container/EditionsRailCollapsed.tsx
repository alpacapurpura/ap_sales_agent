"use client";

import { ChevronRight, Plus } from "lucide-react";
import { useRouter } from "next/navigation";

import { cn } from "@/lib/utils";

import { EditionStatus } from "../../types";

import type { LaunchEdition } from "../../types";

export interface EditionsRailCollapsedProps {
  offerId: string;
  tenantId: string;
  editions: LaunchEdition[];
  currentEditionId: string | null;
  onExpand: () => void;
  onCreateNew: () => void;
}

type Tone = "active" | "next" | "draft" | "past";

function toneFor(edition: LaunchEdition): Tone {
  switch (edition.status) {
    case EditionStatus.ACTIVE:
      return "active";
    case EditionStatus.UPCOMING:
      return "next";
    case EditionStatus.DRAFT:
      return "draft";
    default:
      return "past";
  }
}

const BADGE_STYLES: Record<Tone, string> = {
  active: "bg-emerald-600 text-white font-bold ring-2 ring-emerald-200",
  next: "bg-blue-600 text-white font-bold ring-2 ring-blue-200",
  draft: "bg-amber-50 text-amber-700 border-2 border-dashed border-amber-400 font-semibold",
  past: "bg-muted text-muted-foreground font-semibold",
};

/**
 * Collapsed variant of the editions rail.
 *
 * Displays each edition as a 40×40 circle containing its number, colored
 * by lifecycle tone. Draft editions show a dashed amber border; active
 * and upcoming are filled with their respective colors. Hovering shows
 * the full title via native tooltip.
 */
export function EditionsRailCollapsed({
  offerId,
  tenantId,
  editions,
  currentEditionId,
  onExpand,
  onCreateNew,
}: EditionsRailCollapsedProps) {
  const router = useRouter();
  const switchEdition = (editionId: string) => {
    const base = `/${tenantId}/offer-studio/offer/${offerId}`;
    router.replace(`${base}?edition=${editionId}`);
  };

  // Order: active → upcoming → drafts → past.
  const ordered = [...editions].sort((a, b) => {
    const rank = (s: EditionStatus) =>
      ({
        [EditionStatus.ACTIVE]: 0,
        [EditionStatus.UPCOMING]: 1,
        [EditionStatus.DRAFT]: 2,
        [EditionStatus.COMPLETED]: 3,
        [EditionStatus.CANCELLED]: 4,
      })[s] ?? 5;
    return rank(a.status) - rank(b.status);
  });

  return (
    <aside
      aria-label="Ediciones (colapsado)"
      className="flex w-14 shrink-0 flex-col items-center gap-2 border-r bg-background py-3"
    >
      <button
        type="button"
        onClick={onExpand}
        aria-label="Expandir rail"
        className="mb-2 rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
      >
        <ChevronRight className="h-4 w-4" aria-hidden />
      </button>
      {ordered.map((edition) => {
        const tone = toneFor(edition);
        const isSelected = edition.id === currentEditionId;
        return (
          <button
            key={edition.id}
            type="button"
            onClick={() => switchEdition(edition.id)}
            title={`Edición #${edition.edition_number} · ${edition.status}`}
            aria-pressed={isSelected}
            className={cn(
              "flex h-10 w-10 items-center justify-center rounded-full text-sm transition-transform",
              BADGE_STYLES[tone],
              isSelected && "scale-110",
            )}
          >
            {edition.edition_number}
          </button>
        );
      })}
      <button
        type="button"
        onClick={onCreateNew}
        aria-label="Crear nueva edición"
        className="mt-auto flex h-10 w-10 items-center justify-center rounded-full border-2 border-dashed border-primary/40 text-primary hover:bg-primary/10"
      >
        <Plus className="h-4 w-4" aria-hidden />
      </button>
    </aside>
  );
}
