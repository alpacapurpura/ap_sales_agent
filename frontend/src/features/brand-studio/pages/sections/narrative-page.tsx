"use client";

import { useBrandSettings } from "@/features/brand-studio/hooks/use-brand-settings";
import { useBrandStudioFieldRouting } from "@/features/brand-studio/hooks/use-field-routing";
import { narrativeSchema } from "@/features/brand-studio/schemas/narrative.schema";
import { SectionPage } from "@/lib/studio-section-page";

import type { BrandNarrative } from "@/features/brand-studio/types";

export function NarrativePage() {
  const hook = useBrandSettings();
  const { activeFieldId, getFieldHref } = useBrandStudioFieldRouting("narrative");

  return (
    <SectionPage<BrandNarrative>
      sectionSlug="narrative"
      schema={narrativeSchema}
      values={hook.settings?.narrative ?? undefined}
      onSave={async (next) => {
        await hook.updateNarrative(next);
      }}
      isLoading={hook.loading}
      activeFieldId={activeFieldId}
      getFieldHref={getFieldHref}
    />
  );
}
