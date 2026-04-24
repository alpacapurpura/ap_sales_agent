"use client";

import { useBrandSettings } from "@/features/brand-studio/hooks/use-brand-settings";
import { useBrandStudioFieldRouting } from "@/features/brand-studio/hooks/use-field-routing";
import { visualsSchema } from "@/features/brand-studio/schemas/visuals.schema";
import { SectionPage } from "@/lib/studio-section-page";

import type { BrandVisuals } from "@/features/brand-studio/types";

export function VisualsPage() {
  const hook = useBrandSettings();
  const { activeFieldId, getFieldHref } = useBrandStudioFieldRouting("visuals");

  return (
    <SectionPage<BrandVisuals>
      sectionSlug="visuals"
      schema={visualsSchema}
      values={hook.settings?.visuals ?? undefined}
      onSave={async (next) => {
        await hook.updateVisuals(next);
      }}
      isLoading={hook.loading}
      activeFieldId={activeFieldId}
      getFieldHref={getFieldHref}
    />
  );
}
