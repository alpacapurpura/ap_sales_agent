"use client";

import { useBrandSettings } from "@/features/brand-studio/hooks/use-brand-settings";
import { useBrandStudioFieldRouting } from "@/features/brand-studio/hooks/use-field-routing";
import { communicationAssetsSchema } from "@/features/brand-studio/schemas/communication-assets.schema";
import { SectionPage } from "@/lib/studio-section-page";

import type { CommunicationAssets } from "@/features/brand-studio/types";

export function CommunicationAssetsPage() {
  const hook = useBrandSettings();
  const { activeFieldId, getFieldHref } = useBrandStudioFieldRouting("communication-assets");

  return (
    <SectionPage<CommunicationAssets>
      sectionSlug="communication-assets"
      schema={communicationAssetsSchema}
      values={hook.settings?.communication_assets ?? undefined}
      onSave={async (next) => {
        await hook.updateCommunicationAssets(next);
      }}
      isLoading={hook.loading}
      activeFieldId={activeFieldId}
      getFieldHref={getFieldHref}
    />
  );
}
