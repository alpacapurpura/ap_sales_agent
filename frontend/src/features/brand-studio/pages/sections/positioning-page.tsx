"use client";

import { useBrandSettings } from "@/features/brand-studio/hooks/use-brand-settings";
import { useBrandStudioFieldRouting } from "@/features/brand-studio/hooks/use-field-routing";
import { positioningSchema } from "@/features/brand-studio/schemas/positioning.schema";
import { SectionPage } from "@/lib/studio-section-page";

import type { BrandPositioning } from "@/features/brand-studio/types";

export function PositioningPage() {
  const hook = useBrandSettings();
  const { activeFieldId, getFieldHref } = useBrandStudioFieldRouting("positioning");

  return (
    <SectionPage<BrandPositioning>
      sectionSlug="positioning"
      schema={positioningSchema}
      values={hook.settings?.positioning ?? undefined}
      onSave={async (next) => {
        await hook.updatePositioning(next);
      }}
      isLoading={hook.loading}
      activeFieldId={activeFieldId}
      getFieldHref={getFieldHref}
    />
  );
}
