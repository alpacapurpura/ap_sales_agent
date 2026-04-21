"use client";

import { AlertTriangle, Loader2 } from "lucide-react";
import { useParams } from "next/navigation";
import { useCallback, useMemo } from "react";

import { UniversalEditableSection } from "@/components/form-runtime";
import { useSectionMetadata } from "@/features/offer-studio/hooks/use-section-catalog";
import { resolveOfferEditorRoute } from "@/features/offer-studio/pages/resolve-offer-editor-route";
import {
  offerClosingSchema,
  offerEventDetailsSchema,
  offerFaqSchema,
  offerGallerySchema,
  offerIdentitySchema,
  offerInstructorsSchema,
  offerKnowledgeSchema,
  offerLocationSchema,
  offerPlatformDetailsSchema,
  offerPortfolioSchema,
  offerPricingSchema,
  offerProductDetailsSchema,
  offerProgramDetailsSchema,
  offerPromiseSchema,
  offerPsychologySchema,
  offerResourcesSchema,
  offerServiceDetailsSchema,
  offerStrategySchema,
  offerSubscriptionDetailsSchema,
  offerTestimonialsSchema,
  offerValueStackSchema,
} from "@/features/offer-studio/schemas";

import { useOfferSettings, type UseOfferSettingsHook } from "../hooks/use-offer-settings";

import type { SectionKey, SectionScope } from "../api/archetype-catalog-api";
import type { OfferFormValues } from "../types/schema";
import type { SectionSchema } from "@/lib/form-runtime/schema";
import type { ReactElement } from "react";

interface OfferSectionPageProps {
  offerId: string;
  editionCode: string;
}

/**
 * Factory: produce a page component bound to a specific schema + save
 * routing.
 *
 * Every offer-studio singleton section renders through the same mount —
 * schema + values from ``useOfferSettings`` + save routed to the matching
 * updater. Loading state renders a spinner; error / scope-mismatch state
 * renders an explanatory card so the user never sees a blank screen while
 * the resolver / catalog is still resolving.
 *
 * Save wiring accepts an optional ``save`` selector that picks the right
 * updater from the hook. If omitted (``undefined``), the section is treated
 * as "collection-only" — e.g. ``testimonials`` / ``instructors`` have their
 * own InstancePicker + detail routes under ``/editor/{slug}`` and do NOT
 * write through the aggregator. In that case the factory still mounts the
 * runtime so the catalog / schema invariants remain inspectable; save is a
 * no-op that logs a warning.
 *
 * Mirrors ``features/brand-studio/pages/section-pages.tsx`` — same shape,
 * same factory, same brand-parity contract. Differences (save-per-section
 * vs. single PUT, edition context) are absorbed by ``useOfferSettings``.
 */

const EMPTY_VALUES: Record<string, unknown> = Object.freeze({});

type SliceUpdater = (slice: Partial<OfferFormValues>) => Promise<void>;
type SaveSelector = (hook: UseOfferSettingsHook) => SliceUpdater | undefined;

function createSectionPage(
  schema: SectionSchema,
  sectionKey: SectionKey,
  requiredScope?: SectionScope,
  save?: SaveSelector,
): (props: OfferSectionPageProps) => ReactElement {
  function OfferSectionPage({ offerId, editionCode }: OfferSectionPageProps): ReactElement {
    const params = useParams<{
      tenantId?: string;
      section?: string;
      fieldId?: string | string[];
    }>();
    const hook = useOfferSettings(offerId);
    const metadata = useSectionMetadata(sectionKey);

    const { activeFieldId, sectionBasePath } = resolveOfferEditorRoute({
      tenantId: params?.tenantId ?? "",
      offerId,
      section: params?.section ?? "",
      fieldId: params?.fieldId,
    });
    const getFieldHref = useStableFieldHref(sectionBasePath);

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
      <UniversalEditableSection<Record<string, unknown>>
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

/** Memoise the href builder so React Perf sees a stable function across renders. */
function useStableFieldHref(sectionBasePath: string) {
  return useCallback(
    (fieldId: string | null): string =>
      fieldId ? `${sectionBasePath}/${fieldId}` : sectionBasePath,
    [sectionBasePath],
  );
}

/**
 * Build the section save handler. When an updater is provided the handler
 * forwards the patch to ``useOfferSettings`` (which merges into current
 * form values and calls ``saveSection`` under the hood). When no updater is
 * provided — collection-only sections that have their own detail routes —
 * the handler logs a warning and resolves so the runtime doesn't block.
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

/** Generic fallback while catalog / editions resolve. */
export function SectionPageLoading(): ReactElement {
  return (
    <div className="flex h-64 items-center justify-center">
      <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" aria-hidden />
    </div>
  );
}

// ── Offer-level sections ────────────────────────────────────────────────────

export const IdentityPage = createSectionPage(
  offerIdentitySchema,
  "identity",
  "offer_level",
  (h) => h.updateIdentity,
);
export const StrategyPage = createSectionPage(
  offerStrategySchema,
  "strategy",
  "offer_level",
  (h) => h.updateStrategy,
);
export const PsychologyPage = createSectionPage(
  offerPsychologySchema,
  "psychology",
  "offer_level",
  (h) => h.updatePsychology,
);
export const PromisePage = createSectionPage(
  offerPromiseSchema,
  "promise",
  "offer_level",
  (h) => h.updatePromise,
);
export const ValueStackPage = createSectionPage(
  offerValueStackSchema,
  "value_stack",
  "offer_level",
  (h) => h.updateValueStack,
);
// Collection sections — save handled by their dedicated detail routes, not the aggregator.
export const InstructorsPage = createSectionPage(
  offerInstructorsSchema,
  "instructors",
  "offer_level",
);
export const KnowledgePage = createSectionPage(offerKnowledgeSchema, "knowledge", "offer_level");
export const ClosingPage = createSectionPage(
  offerClosingSchema,
  "closing",
  "offer_level",
  (h) => h.updateClosing,
);
export const ProductDetailsPage = createSectionPage(
  offerProductDetailsSchema,
  "product_details",
  "offer_level",
  (h) => h.updateProductDetails,
);
export const SubscriptionDetailsPage = createSectionPage(
  offerSubscriptionDetailsSchema,
  "subscription_details",
  "offer_level",
  (h) => h.updateSubscriptionDetails,
);
export const GalleryPage = createSectionPage(offerGallerySchema, "gallery", "offer_level");

// ── Edition-level sections ──────────────────────────────────────────────────

export const EventDetailsPage = createSectionPage(
  offerEventDetailsSchema,
  "event_details",
  "edition_level",
  (h) => h.updateEventDetails,
);

// ── Mixed-scope sections ────────────────────────────────────────────────────

export const PricingPage = createSectionPage(
  offerPricingSchema,
  "pricing",
  "mixed",
  (h) => h.updatePricing,
);
export const ProgramDetailsPage = createSectionPage(
  offerProgramDetailsSchema,
  "program_details",
  "mixed",
  (h) => h.updateProgramDetails,
);
export const ServiceDetailsPage = createSectionPage(
  offerServiceDetailsSchema,
  "service_details",
  "mixed",
  (h) => h.updateServiceDetails,
);
export const ResourcesPage = createSectionPage(offerResourcesSchema, "resources", "mixed");
export const LocationPage = createSectionPage(
  offerLocationSchema,
  "location",
  "mixed",
  (h) => h.updateLocation,
);

// ── Nuevas secciones (Latam mass-market rollout) ───────────────────────────

export const FaqPage = createSectionPage(offerFaqSchema, "faq", "offer_level");
export const TestimonialsPage = createSectionPage(
  offerTestimonialsSchema,
  "testimonials",
  "offer_level",
);
export const PortfolioPage = createSectionPage(offerPortfolioSchema, "portfolio", "offer_level");
export const PlatformDetailsPage = createSectionPage(
  offerPlatformDetailsSchema,
  "platform_details",
  "offer_level",
  (h) => h.updatePlatformDetails,
);

/** Name the index in the same shape the server-safe map expects. */
export const OFFER_STUDIO_SECTION_KEYS: readonly SectionKey[] = [
  "identity",
  "strategy",
  "psychology",
  "promise",
  "value_stack",
  "instructors",
  "knowledge",
  "closing",
  "product_details",
  "subscription_details",
  "gallery",
  "event_details",
  "pricing",
  "program_details",
  "service_details",
  "resources",
  "faq",
  "testimonials",
  "portfolio",
  "location",
  "platform_details",
];
