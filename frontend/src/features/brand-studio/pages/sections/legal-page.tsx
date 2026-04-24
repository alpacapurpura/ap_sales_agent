"use client";

import { useBrandSettings } from "@/features/brand-studio/hooks/use-brand-settings";
import { useBrandStudioFieldRouting } from "@/features/brand-studio/hooks/use-field-routing";
import { legalSchema } from "@/features/brand-studio/schemas/legal.schema";
import { SectionPage } from "@/lib/studio-section-page";

import type { BrandIdentity } from "@/features/brand-studio/types";

/**
 * Legal y cumplimiento page. Comparte el slice `BrandIdentity` con
 * `identity-page.tsx`: el schema selecciona solo los paths legales y
 * el autosave los fusiona sobre el blob identity via `updateIdentity`.
 */
export function LegalPage() {
  const hook = useBrandSettings();
  const { activeFieldId, getFieldHref } = useBrandStudioFieldRouting("legal");

  return (
    <SectionPage<BrandIdentity>
      sectionSlug="legal"
      schema={legalSchema}
      values={hook.settings?.identity ?? undefined}
      onSave={async (next) => {
        await hook.updateIdentity(next);
      }}
      isLoading={hook.loading}
      activeFieldId={activeFieldId}
      getFieldHref={getFieldHref}
    />
  );
}
