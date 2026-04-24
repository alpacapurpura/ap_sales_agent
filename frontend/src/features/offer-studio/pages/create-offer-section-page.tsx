"use client";

import { AlertTriangle } from "lucide-react";
import { useMemo } from "react";

import { useOfferStudioFieldRouting } from "@/features/offer-studio/hooks/use-field-routing";
import { useSectionMetadata } from "@/features/offer-studio/hooks/use-section-catalog";
import { SectionPage } from "@/lib/studio-section-page";

import { useOfferSettings, type UseOfferSettingsHook } from "../hooks/use-offer-settings";

import type { SectionKey, SectionScope } from "../api/archetype-catalog-api";
import type { OfferFormValues } from "../types/schema";
import type { SectionSchema } from "@/lib/form-runtime/schema";
import type { ReactElement } from "react";

export interface OfferSectionPageProps {
  offerId: string;
  editionCode: string;
}

type SliceUpdater = (slice: Partial<OfferFormValues>) => Promise<void>;
type SaveSelector = (hook: UseOfferSettingsHook) => SliceUpdater | undefined;

export interface CreateOfferSectionPageConfig {
  schema: SectionSchema;
  sectionKey: SectionKey;
  /**
   * Scope al que pertenece la sección. Si `edition_level`, el componente
   * muestra un guard cuando el `editionCode` es `"evergreen"` — los
   * campos viven en una edición concreta que el usuario debe elegir
   * desde el rail lateral.
   */
  requiredScope?: SectionScope;
  /**
   * Selector que devuelve la función updater del hook agregador. Si se
   * omite, la sección es "collection-only" — p.ej. `testimonials` o
   * `instructors` tienen rutas de detalle dedicadas y NO escriben por el
   * aggregator. En ese caso el save loggea warning y resuelve.
   */
  save?: SaveSelector;
}

const EMPTY_VALUES: Record<string, unknown> = Object.freeze({});

/**
 * Factory que produce el componente per-section del offer-studio.
 *
 * Cada per-section file bajo `sections/` lo invoca con su config. Esto
 * centraliza el wiring repetido (hook de data, metadata, field-routing,
 * save handler, guard de edition-scope) y deja que cada file se
 * concentre solo en el schema import (único — Turbopack code-split
 * per-section preservado).
 *
 * Named export — política `test-no-default-exports`. `next/dynamic` en
 * `SectionDispatcher.tsx` resuelve el named export via `.then()`.
 */
export function createOfferSectionPage(
  config: CreateOfferSectionPageConfig,
): (props: OfferSectionPageProps) => ReactElement {
  const { schema, sectionKey, requiredScope, save } = config;

  function OfferSectionPage({ offerId, editionCode }: OfferSectionPageProps): ReactElement {
    const hook = useOfferSettings(offerId);
    const metadata = useSectionMetadata(sectionKey);
    const { activeFieldId, getFieldHref } = useOfferStudioFieldRouting(sectionKey);

    const updater = save ? save(hook) : undefined;
    const handleSave = useSectionSaveHandler(sectionKey, offerId, editionCode, updater);

    if (requiredScope === "edition_level" && editionCode === "evergreen") {
      const label = metadata?.label_es?.toLowerCase() ?? "esta sección";
      return (
        <div className="mx-auto max-w-3xl rounded-md border border-dashed border-muted-foreground/30 bg-muted/20 p-8 text-center">
          <AlertTriangle className="mx-auto mb-3 h-8 w-8 text-muted-foreground" aria-hidden />
          <h3 className="text-lg font-medium">Esta sección necesita una edición concreta</h3>
          <p className="mt-2 text-sm text-muted-foreground">
            Los campos de {label} viven en la edición específica que estás configurando. Selecciona
            o crea una edición desde el rail lateral.
          </p>
        </div>
      );
    }

    const values = hook.settings ?? EMPTY_VALUES;

    return (
      <SectionPage<Record<string, unknown>>
        sectionSlug={sectionKey}
        schema={schema}
        values={values}
        activeFieldId={activeFieldId}
        getFieldHref={getFieldHref}
        onSave={handleSave}
        saveMode="autosave-with-banner"
        titleOverride={metadata?.label_es}
        descriptionOverride={metadata?.subtitle_es}
        isLoading={hook.loading}
      />
    );
  }

  OfferSectionPage.displayName = `OfferSectionPage(${sectionKey})`;
  return OfferSectionPage;
}

/**
 * Handler de save memoizado. Si hay updater, forwardea el patch al
 * aggregator (que mergea y persiste via `saveSection`). Si no hay
 * updater (collection-only), loggea warning y resuelve para no
 * bloquear el runtime.
 */
function useSectionSaveHandler(
  sectionKey: SectionKey,
  offerId: string,
  editionCode: string,
  updater: SliceUpdater | undefined,
) {
  return useMemo(
    () =>
      async (patch: Record<string, unknown>): Promise<void> => {
        if (!updater) {
          console.warn(
            `[offer-studio/${sectionKey}] save ignored — section uses a dedicated route ` +
              `(offerId=${offerId}, editionCode=${editionCode})`,
            patch,
          );
          return;
        }
        await updater(patch as Partial<OfferFormValues>);
      },
    [sectionKey, offerId, editionCode, updater],
  );
}
