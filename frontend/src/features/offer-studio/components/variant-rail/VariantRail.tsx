"use client";

/**
 * VariantRail — Polymorphic sibling of the legacy EditionsRail.
 *
 * Architectural decisions vs EditionsRail:
 *   1. Renamed `editions` → `variants` and `currentEditionId` → `currentVariantId`
 *      for brand-parity wording (the rail is now variant-polymorphic across all
 *      8 VariantStructure types, not just temporal editions).
 *   2. Header noun is driven by getVariantNounPlural(structure) from the catalog
 *      SSoT — never hardcoded. Rail title = "Planes (3)" / "Cohortes (2)" / etc.
 *   3. Grouping dispatches to groupVariantsByStructure() which handles the 8
 *      structure types with distinct group taxonomies.
 *   4. Entry rendering dispatches to VariantEntryDispatch which reads
 *      variant.variant_structure and renders the appropriate narrow card.
 *   5. buildEditionSwitchHref is re-used from the legacy container location —
 *      both rails share the same URL shape. F4 will consolidate the helper.
 *
 * EditionsRail.tsx is intentionally left UNTOUCHED (F4 removes it). Both live
 * in parallel during the migration window (F2 → F3 consumer migration → F4
 * deletion).
 */

import { ChevronLeft, Plus } from "lucide-react";
import { usePathname, useRouter } from "next/navigation";
import { useMemo } from "react";

import { cn } from "@/lib/utils";

import { getVariantNoun, getVariantNounPlural } from "../../lib/variant-structure-catalog";
import { buildEditionSwitchHref } from "../container/edition-route";

import { VariantEntryDispatch } from "./entries/VariantEntryDispatch";
import { groupVariantsByStructure } from "./grouping";

import type { VariantStructure } from "../../api/archetype-catalog-api";
import type { LaunchEdition } from "../../types";

export interface VariantRailProps {
  offerId: string;
  tenantId: string;
  variants: LaunchEdition[];
  currentVariantId: string | null;
  waitlistCount?: number;
  onCollapse: () => void;
  onCreateNew: () => void;
}

/**
 * Derive the variant structure from the first variant in the list.
 * All variants in a single offer share the same structure — this is
 * enforced at the data model level. Falls back to temporal_cohort as a
 * safe default for empty lists.
 */
function resolveStructure(variants: LaunchEdition[]): VariantStructure {
  return variants[0]?.variant_structure ?? "temporal_cohort";
}

/**
 * Polymorphic variant rail for the Offer Studio shell. Adapts the legacy
 * EditionsRail to dispatch per variant_structure. Width, border, and
 * collapse behaviour are identical to EditionsRail (224px / w-56).
 */
export function VariantRail({
  offerId,
  tenantId,
  variants,
  currentVariantId,
  waitlistCount = 0,
  onCollapse,
  onCreateNew,
}: VariantRailProps) {
  const router = useRouter();
  const pathname = usePathname();

  const structure = useMemo(() => resolveStructure(variants), [variants]);
  const groups = useMemo(
    () => groupVariantsByStructure(variants, structure),
    [variants, structure],
  );

  const nounPlural = getVariantNounPlural(structure);
  const nounSingular = getVariantNoun(structure);
  // Capitalize first letter for the header: "planes" → "Planes"
  const headerLabel = `${nounPlural.charAt(0).toUpperCase()}${nounPlural.slice(1)} (${variants.length})`;
  const ctaLabel = `+ Nueva ${nounSingular}`;
  const emptyLabel = `Aún no tienes ${nounPlural}`;

  const switchVariant = (variantId: string) => {
    const base = `/${tenantId}/offer-studio/offer/${offerId}`;
    router.push(buildEditionSwitchHref(pathname, base, variantId));
  };

  return (
    <aside
      aria-label="Variantes de la oferta"
      className="flex w-56 shrink-0 flex-col border-r bg-background"
    >
      <header className="flex items-center justify-between border-b px-3 py-2.5">
        <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          {headerLabel}
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
          <EmptyState emptyLabel={emptyLabel} onCreateNew={onCreateNew} />
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
                {group.items.map((variant) => (
                  <li key={variant.id}>
                    <VariantEntryDispatch
                      variant={variant}
                      tone={group.tone}
                      isSelected={variant.id === currentVariantId}
                      waitlistCount={
                        group.tone === "draft" && variant.id === currentVariantId
                          ? waitlistCount
                          : 0
                      }
                      onClick={() => switchVariant(variant.id)}
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
          <Plus className="h-4 w-4" aria-hidden />
          {ctaLabel}
        </button>
        <p className="mt-1.5 text-center text-[10px] text-muted-foreground">Clonar recomendado</p>
      </footer>
    </aside>
  );
}

// ─── Empty state ──────────────────────────────────────────────────────────────

function EmptyState({ emptyLabel, onCreateNew }: { emptyLabel: string; onCreateNew: () => void }) {
  return (
    <div className="flex flex-col items-center gap-2 py-8 text-center">
      <p className="text-xs text-muted-foreground">{emptyLabel}</p>
      <button
        type="button"
        onClick={onCreateNew}
        className="rounded-md bg-primary px-2.5 py-1 text-xs font-medium text-primary-foreground hover:bg-primary/90"
      >
        Crear primera variante
      </button>
    </div>
  );
}
