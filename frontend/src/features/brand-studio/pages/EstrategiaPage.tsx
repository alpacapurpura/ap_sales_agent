"use client";

import { UniversalEditableSection } from "@/components/form-runtime";
import { useBrandSettings } from "@/features/brand-studio/hooks/use-brand-settings";
import { positioningSchema } from "@/features/brand-studio/schemas";

/**
 *
 */
export function EstrategiaPage() {
  const { settings, loading, updatePositioning } = useBrandSettings();

  return (
    <UniversalEditableSection
      schema={positioningSchema}
      values={settings?.positioning ?? { reasons_to_believe: [] }}
      onSave={async (next) => {
        await updatePositioning(next);
      }}
      isLoading={loading}
    />
  );
}
