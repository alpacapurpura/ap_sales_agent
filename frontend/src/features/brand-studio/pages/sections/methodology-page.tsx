"use client";

import { useBrandSettings } from "@/features/brand-studio/hooks/use-brand-settings";
import { useBrandStudioFieldRouting } from "@/features/brand-studio/hooks/use-field-routing";
import { methodologySchema } from "@/features/brand-studio/schemas/methodology.schema";
import { SectionPage } from "@/lib/studio-section-page";

import type { BrandStrategy } from "@/features/brand-studio/types";

export function MethodologyPage() {
  const hook = useBrandSettings();
  const { activeFieldId, getFieldHref } = useBrandStudioFieldRouting("methodology");

  return (
    <SectionPage<BrandStrategy>
      sectionSlug="methodology"
      schema={methodologySchema}
      values={hook.settings?.strategy ?? undefined}
      onSave={async (next) => {
        await hook.updateStrategy(next);
      }}
      isLoading={hook.loading}
      activeFieldId={activeFieldId}
      getFieldHref={getFieldHref}
    />
  );
}
