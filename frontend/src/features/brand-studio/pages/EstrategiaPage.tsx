"use client";

import { UniversalEditableSection } from "@/components/form-runtime";
import { useBrandSettings } from "@/features/brand-studio/hooks/use-brand-settings";
import { useBrandStudioFieldRouting } from "@/features/brand-studio/hooks/use-field-routing";
import { positioningSchema } from "@/features/brand-studio/schemas";

/**
 * Brand Studio → Estrategia page (positioning). URL-driven per field.
 */
export function EstrategiaPage() {
  const { settings, loading, updatePositioning } = useBrandSettings();
  const { activeFieldId, getFieldHref } = useBrandStudioFieldRouting("estrategia");

  return (
    <UniversalEditableSection
      schema={positioningSchema}
      values={settings?.positioning ?? { reasons_to_believe: [] }}
      onSave={async (next) => {
        await updatePositioning(next);
      }}
      isLoading={loading}
      activeFieldId={activeFieldId}
      getFieldHref={getFieldHref}
    />
  );
}
