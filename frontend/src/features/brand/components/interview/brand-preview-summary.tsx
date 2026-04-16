"use client";

import { useMemo } from "react";

import { useBrandSettings } from "@/features/brand/hooks/use-brand-settings";
import { useCopilotStore } from "@/features/copilot/store/copilot-store";

import type { BrandSettings } from "@/features/brand/types";
import type { PreviewSummaryProps } from "@/features/copilot/config/interview-preview-registry";

/**
 * Brand-specific summary for the interview preview left panel.
 * Computes and exposes the merged brand settings (live + interview draft overlay).
 *
 * For brand, this is a lightweight component — the main visual content
 * lives in BrandPreviewSections which renders tabs + section views.
 */
export function BrandPreviewSummary({ completenessScore }: PreviewSummaryProps) {
  const { settings } = useBrandSettings();
  const previewData = useCopilotStore((s) => s.previewData);

  const mergedSettings = useMemo<BrandSettings | null>(() => {
    if (!settings) return null;
    if (!previewData) return settings;
    return {
      ...settings,
      ...Object.fromEntries(
        Object.entries(previewData).map(([k, v]) => [
          k,
          typeof v === "object" && v !== null && !Array.isArray(v)
            ? {
                ...((settings[k as keyof BrandSettings] as object) ?? {}),
                ...v,
              }
            : v,
        ]),
      ),
    } as BrandSettings;
  }, [settings, previewData]);

  if (!mergedSettings) return null;

  return (
    <div className="flex items-center gap-2 px-4 py-2 border-b border-white/5 bg-background/50">
      <span className="text-xs text-muted-foreground">Completitud de marca</span>
      <span className="text-xs font-semibold text-purple-400">{completenessScore}%</span>
    </div>
  );
}
