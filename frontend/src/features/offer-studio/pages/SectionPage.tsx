"use client";

import { UniversalEditableSection } from "@/components/form-runtime";
import { useOfferStudioFieldRouting } from "@/features/offer-studio/hooks/use-field-routing";

import type { SectionSchema } from "@/lib/form-runtime/schema";
import type { ReactNode } from "react";

export interface SectionPageProps<TSlice extends object> {
  /** URL slug identifying the section (e.g. "promise", "pricing"). */
  sectionSlug: string;
  /** Form-runtime schema describing the section's fields. */
  schema: SectionSchema;
  /** Current slice resolved from the Offer / LaunchEdition pair. */
  values: TSlice | null | undefined;
  /** Save function wired to the mutation dispatcher. Receives the composed slice. */
  onSave: (next: TSlice) => Promise<void>;
  /** Forwarded to the runtime's loading state. */
  isLoading?: boolean;
  /**
   * Optional right-rail slot. When provided, UniversalEditableSection
   * renders a 3-column split (NavRail / form / copilot). Omit to keep the
   * standard 2-column layout (same rendering brand-studio uses today).
   *
   * The copilot slot is the canonical extension point for per-section
   * assistance — see ``docs/ux-sessions/2026-04-20-offer-studio-homologation/
   * UI-SPEC-copilot-sidebar.md``.
   */
  copilotSlot?: ReactNode;
  className?: string;
}

/**
 * Presentational section page. Reads ``activeFieldId`` + builds
 * ``getFieldHref`` from the URL via ``useOfferStudioFieldRouting``, then
 * delegates to ``UniversalEditableSection``. Consumers compose this with
 * the section's schema + slice selector + onSave function.
 *
 * Mirrors ``features/brand-studio/pages/SectionPage.tsx`` so both studios
 * share the same contract — the only offer-specific concerns (offerId /
 * editionCode) live in the field-routing hook, invisible to the page
 * shell.
 *
 * Route contract (owned by the consumer page file in ``app/.../``):
 *
 *   /{tenantId}/offer-studio/offer/{offerId}/edition/{editionCode}/{sectionSlug}
 *     → list view
 *   /{tenantId}/offer-studio/offer/{offerId}/edition/{editionCode}/{sectionSlug}/{fieldId}
 *     → detail view
 */
export function SectionPage<TSlice extends object>({
  sectionSlug,
  schema,
  values,
  onSave,
  isLoading,
  copilotSlot,
  className,
}: SectionPageProps<TSlice>) {
  const { activeFieldId, getFieldHref } = useOfferStudioFieldRouting(sectionSlug);

  return (
    <UniversalEditableSection
      schema={schema}
      values={values}
      onSave={onSave}
      isLoading={isLoading}
      activeFieldId={activeFieldId}
      getFieldHref={getFieldHref}
      copilotSlot={copilotSlot}
      className={className}
    />
  );
}
