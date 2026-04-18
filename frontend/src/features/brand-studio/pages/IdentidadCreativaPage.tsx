"use client";

import { UniversalEditableSection } from "@/components/form-runtime";
import { useBrandSettings } from "@/features/brand-studio/hooks/use-brand-settings";
import { visualsSchema } from "@/features/brand-studio/schemas";

/**
 *
 */
export function IdentidadCreativaPage() {
  const { settings, loading, updateVisuals } = useBrandSettings();

  return (
    <UniversalEditableSection
      schema={visualsSchema}
      values={settings?.visuals ?? {}}
      onSave={async (next) => {
        await updateVisuals(next);
      }}
      isLoading={loading}
    />
  );
}
