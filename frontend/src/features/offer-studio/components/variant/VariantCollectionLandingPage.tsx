"use client";

import { Plus } from "lucide-react";

import { Button } from "@/components/ui/button";

import { getVariantLabel, getVariantStructureMeta } from "../../lib/variant-structure-catalog";

import { VariantCard } from "./VariantCard";

import type { LaunchEdition } from "../../types";

interface VariantCollectionLandingPageProps {
  /** All variants under the offer. Includes placeholders + published + archived. */
  variants: readonly LaunchEdition[];
  /** Label of the offer — shown above the collection title. */
  offerName: string;
  /** Empty-state CTA. Called when the user clicks "Nueva <noun>". */
  onCreate: () => void;
  onEdit: (variant: LaunchEdition) => void;
  onDuplicate: (variant: LaunchEdition) => void;
  onDelete: (variant: LaunchEdition) => void;
  /**
   * Optional — when provided, the page shows the suitability note as a
   * muted caption under the title (pulled from the preset / archetype
   * catalog by the caller).
   */
  suitabilityNote?: string;
}

/**
 * Polymorphic variant collection page. Replaces the legacy hand-rolled
 * "editions tab" with a rail that adapts to the offer's
 * ``variant_structure``.
 *
 *   - PROGRAMA cohort → title "Cohortes", temporal cards.
 *   - MEMBRESIA tier → title "Planes", tier cards with price anchor.
 *   - PRODUCTO sku    → title "Variantes", SKU cards with attributes.
 *   - EXPERIENCIA temporal_single_date → title "Salidas".
 *   - SERVICIO recurring_intake → title "Convocatorias".
 *   - REGIONAL / MODALITY / LANGUAGE surface the same rail with their
 *     dedicated card template.
 *
 * Works without backend changes — every variant already carries its
 * ``variant_structure`` (Sprint 7). Each offer's variants share the same
 * structure; mixing structures on the same offer is rejected by the
 * create flow.
 *
 * Mirrors ``features/brand-studio`` buyer-personas collection landing in
 * terms of layout: lista-de-cards + empty-state + "+ Nueva" CTA.
 */
export function VariantCollectionLandingPage({
  variants,
  offerName,
  onCreate,
  onEdit,
  onDuplicate,
  onDelete,
  suitabilityNote,
}: VariantCollectionLandingPageProps) {
  const structure = variants[0]?.variant_structure ?? null;
  const title = getVariantLabel(structure);
  const meta = getVariantStructureMeta(structure);
  const singularNoun = meta?.nounEs ?? "edición";

  const isEmpty = variants.length === 0;

  return (
    <div className="flex h-full flex-col gap-6 overflow-y-auto p-6">
      <header className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-wide text-muted-foreground">{offerName}</p>
          <h2 className="mt-1 text-2xl font-semibold tracking-tight">{title}</h2>
          {meta?.descriptionEs && (
            <p className="mt-1 max-w-2xl text-sm text-muted-foreground">{meta.descriptionEs}</p>
          )}
          {suitabilityNote && (
            <p className="mt-2 text-xs italic text-muted-foreground">{suitabilityNote}</p>
          )}
        </div>
        <Button size="sm" onClick={onCreate}>
          <Plus className="mr-1.5 h-4 w-4" />
          {`Nueva ${singularNoun}`}
        </Button>
      </header>

      {isEmpty ? (
        <EmptyState nounSingular={singularNoun} onCreate={onCreate} />
      ) : (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {variants.map((v) => (
            <VariantCard
              key={v.id}
              variant={v}
              onEdit={() => onEdit(v)}
              onDuplicate={() => onDuplicate(v)}
              onDelete={() => onDelete(v)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function EmptyState({ nounSingular, onCreate }: { nounSingular: string; onCreate: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-lg border border-dashed bg-muted/20 p-12 text-center">
      <h3 className="text-lg font-semibold">Aún no tienes ninguna {nounSingular}</h3>
      <p className="mt-1 max-w-md text-sm text-muted-foreground">
        Crea la primera y el editor te guiará para completar las secciones específicas.
      </p>
      <Button className="mt-4" onClick={onCreate}>
        <Plus className="mr-1.5 h-4 w-4" />
        {`Crear primera ${nounSingular}`}
      </Button>
    </div>
  );
}
