"use client";

import { Loader2 } from "lucide-react";

import { useBrandSettings } from "@/features/brand/hooks/use-brand-settings";

import { StoryForm } from "./story-form";

export function StoryManager() {
  const { settings, updateStory, loading, saving } = useBrandSettings();

  if (loading) {
    return (
      <div className="flex justify-center py-8">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!settings) return null;

  return <StoryForm initialData={settings.story ?? {}} onSave={updateStory} isSaving={saving} />;
}
