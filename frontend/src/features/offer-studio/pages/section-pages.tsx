"use client";

import { AlertTriangle, Loader2 } from "lucide-react";
import { usePathname } from "next/navigation";
import { useCallback } from "react";

import { UniversalEditableSection } from "@/components/form-runtime";
import {
  offerClosingSchema,
  offerEventDetailsSchema,
  offerGallerySchema,
  offerIdentitySchema,
  offerInstructorsSchema,
  offerKnowledgeSchema,
  offerPricingSchema,
  offerProductDetailsSchema,
  offerProgramDetailsSchema,
  offerPromiseSchema,
  offerPsychologySchema,
  offerResourcesSchema,
  offerServiceDetailsSchema,
  offerStrategySchema,
  offerSubscriptionDetailsSchema,
  offerValueStackSchema,
} from "@/features/offer-studio/schemas";

import type { SectionKey, SectionScope } from "../api/archetype-catalog-api";
import type { SectionSchema } from "@/lib/form-runtime/schema";
import type { ReactElement } from "react";

interface OfferSectionPageProps {
  offerId: string;
  editionCode: string;
}

/**
 * Factory: produce a page component bound to a specific schema.
 *
 * Every offer-studio section renders through the same mount — schema +
 * values + save routing. The consumer (Phase E) replaces this placeholder
 * save flow with live ``useOffer`` / ``useEdition`` mutations once the
 * per-section actions are ported.
 *
 * Loading state renders a spinner; error / scope-mismatch state renders
 * an explanatory card so the user never sees a blank screen while the
 * resolver / catalog is still resolving.
 */
const EMPTY_VALUES: Record<string, unknown> = Object.freeze({});

function createSectionPage(
  schema: SectionSchema,
  requiredScope?: SectionScope,
): (props: OfferSectionPageProps) => ReactElement {
  return function SectionPageComponent({ offerId, editionCode }: OfferSectionPageProps) {
    const pathname = usePathname() ?? "";
    // Phase D.2 scaffold: real data + save wiring lands in Phase E once
    // each legacy ``*Form.tsx`` is ported as an action. Until then the
    // runtime mounts with empty values so the UX is inspectable
    // end-to-end and smoke tests can assert routing works.
    const activeFieldId = extractActiveFieldId(pathname);
    const sectionBasePath = stripActiveFieldId(pathname);
    const getFieldHref = useStableFieldHref(sectionBasePath);
    const handleSave = useStableSaveHandler(schema.key, offerId, editionCode);

    if (requiredScope === "edition_level" && editionCode === "evergreen") {
      return (
        <div className="mx-auto max-w-3xl rounded-md border border-dashed border-muted-foreground/30 bg-muted/20 p-8 text-center">
          <AlertTriangle className="mx-auto mb-3 h-8 w-8 text-muted-foreground" aria-hidden />
          <h3 className="text-lg font-medium">Esta sección necesita una edición concreta</h3>
          <p className="mt-2 text-sm text-muted-foreground">
            Los campos de {schema.title.toLowerCase()} viven en la edición específica que estás
            configurando. Seleccioná o creá una edición desde el rail lateral.
          </p>
        </div>
      );
    }

    return (
      <div className="mx-auto max-w-5xl p-6">
        <UniversalEditableSection<Record<string, unknown>>
          schema={schema}
          values={EMPTY_VALUES}
          activeFieldId={activeFieldId}
          getFieldHref={getFieldHref}
          onSave={handleSave}
          saveMode="autosave-with-banner"
        />
      </div>
    );
  };
}

/** Memoise the href builder so React Perf sees a stable function across renders. */
function useStableFieldHref(sectionBasePath: string) {
  return useCallback(
    (fieldId: string | null): string =>
      fieldId ? `${sectionBasePath}/${fieldId}` : sectionBasePath,
    [sectionBasePath],
  );
}

/** Memoise the placeholder save handler so React Perf sees a stable function. */
function useStableSaveHandler(sectionKey: string, offerId: string, editionCode: string) {
  return useCallback(
    (patch: Record<string, unknown>): Promise<void> => {
      console.warn(
        `[offer-studio/${sectionKey}] onSave placeholder — offer=${offerId} code=${editionCode}`,
        patch,
      );
      return Promise.resolve();
    },
    [sectionKey, offerId, editionCode],
  );
}

/**
 * Extract the fieldId segment from a catch-all pathname of the shape
 * ``/.../edition/{code}/{section}/{fieldId?}``. Returns ``null`` when
 * the pathname ends at the section slug (detail pane collapsed).
 */
const FIELD_ID_PATTERN = /\/edition\/[^/]+\/[^/]+(?:\/([^/?#]+))?$/;

function extractActiveFieldId(pathname: string): string | null {
  // eslint-disable-next-line @typescript-eslint/prefer-regexp-exec -- match() is correct here; the first capture group is what we want, exec() would require a result variable with less readable semantics.
  const match = pathname.match(FIELD_ID_PATTERN);
  return match?.[1] ?? null;
}

/**
 * Return the pathname with any trailing fieldId segment stripped. Used
 * to build ``getFieldHref`` so the URL always lands on the section root
 * plus an optional selected field.
 */
function stripActiveFieldId(pathname: string): string {
  return pathname.replace(/(\/edition\/[^/]+\/[^/]+)(\/[^/?#]+)?$/, "$1");
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

export const IdentityPage = createSectionPage(offerIdentitySchema, "offer_level");
export const StrategyPage = createSectionPage(offerStrategySchema, "offer_level");
export const PsychologyPage = createSectionPage(offerPsychologySchema, "offer_level");
export const PromisePage = createSectionPage(offerPromiseSchema, "offer_level");
export const ValueStackPage = createSectionPage(offerValueStackSchema, "offer_level");
export const InstructorsPage = createSectionPage(offerInstructorsSchema, "offer_level");
export const KnowledgePage = createSectionPage(offerKnowledgeSchema, "offer_level");
export const ClosingPage = createSectionPage(offerClosingSchema, "offer_level");
export const ProductDetailsPage = createSectionPage(offerProductDetailsSchema, "offer_level");
export const SubscriptionDetailsPage = createSectionPage(
  offerSubscriptionDetailsSchema,
  "offer_level",
);
export const GalleryPage = createSectionPage(offerGallerySchema, "offer_level");

// ── Edition-level sections ──────────────────────────────────────────────────

export const EventDetailsPage = createSectionPage(offerEventDetailsSchema, "edition_level");

// ── Mixed-scope sections ────────────────────────────────────────────────────

export const PricingPage = createSectionPage(offerPricingSchema, "mixed");
export const ProgramDetailsPage = createSectionPage(offerProgramDetailsSchema, "mixed");
export const ServiceDetailsPage = createSectionPage(offerServiceDetailsSchema, "mixed");
export const ResourcesPage = createSectionPage(offerResourcesSchema, "mixed");

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
];
