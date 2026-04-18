"use client";

import { UniversalEditableSection } from "@/components/form-runtime";
import { useBrandSettings } from "@/features/brand-studio/hooks/use-brand-settings";
import { useBrandStudioFieldRouting } from "@/features/brand-studio/hooks/use-field-routing";
import { visualsSchema } from "@/features/brand-studio/schemas";

/**
 * Brand Studio → Identidad Creativa page (visuals). URL-driven per field.
 */
export function IdentidadCreativaPage() {
  const { settings, loading, updateVisuals } = useBrandSettings();
  const { activeFieldId, getFieldHref } = useBrandStudioFieldRouting("identidad-creativa");

  return (
    <UniversalEditableSection
      schema={visualsSchema}
      values={settings?.visuals ?? {}}
      onSave={async (next) => {
        await updateVisuals(next);
      }}
      isLoading={loading}
      activeFieldId={activeFieldId}
      getFieldHref={getFieldHref}
    />
  );
}
