"use client";

import { useBrandSettings } from "@/features/brand-studio/hooks/use-brand-settings";
import { useBrandStudioFieldRouting } from "@/features/brand-studio/hooks/use-field-routing";
import { storySchema } from "@/features/brand-studio/schemas/story.schema";
import { SectionPage } from "@/lib/studio-section-page";

import type { BrandStory } from "@/features/brand-studio/types";

export function StoryPage() {
  const hook = useBrandSettings();
  const { activeFieldId, getFieldHref } = useBrandStudioFieldRouting("story");

  return (
    <SectionPage<BrandStory>
      sectionSlug="story"
      schema={storySchema}
      values={hook.settings?.story ?? undefined}
      onSave={async (next) => {
        await hook.updateStory(next);
      }}
      isLoading={hook.loading}
      activeFieldId={activeFieldId}
      getFieldHref={getFieldHref}
    />
  );
}
