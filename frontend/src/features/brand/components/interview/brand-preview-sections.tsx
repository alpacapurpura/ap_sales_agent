"use client";

import { useState, useMemo } from "react";

import { ScrollArea } from "@/components/ui/scroll-area";
import { BrandStudioTabs } from "@/features/brand/components/tabs/brand-studio-tabs";
import { EsenciaView } from "@/features/brand/components/views/esencia-view";
import { EstrategiaView } from "@/features/brand/components/views/estrategia-view";
import { IdentidadCreativaView } from "@/features/brand/components/views/identidad-creativa-view";
import { PublicoView } from "@/features/brand/components/views/publico-view";
import { useBrandSettings } from "@/features/brand/hooks/use-brand-settings";
import { useCopilotStore } from "@/features/copilot/store/copilot-store";

import type { BrandSectionId } from "@/features/brand/config/sections";
import type { BrandSettings } from "@/features/brand/types";
import type { PreviewSectionsProps } from "@/features/copilot/config/interview-preview-registry";

// Section views

// ── Block to Tab mapping (brand-specific) ───────────────────────────────────

const BLOCK_TO_TAB: Record<string, BrandSectionId> = {
  identidad: "esencia",
  posicionamiento: "estrategia",
  narrativa: "estrategia",
  publico: "publico",
  identidad_creativa: "identidad-creativa",
};

// ── Section view renderer ───────────────────────────────────────────────────

function PreviewSection({ activeTab }: { activeTab: BrandSectionId }) {
  switch (activeTab) {
    case "esencia":
      return <EsenciaView />;
    case "estrategia":
      return <EstrategiaView />;
    case "publico":
      return <PublicoView />;
    case "identidad-creativa":
      return <IdentidadCreativaView />;
    default:
      return <EsenciaView />;
  }
}

/**
 * Brand-specific sections preview for the interview left panel.
 * Renders tab bar + section view content. The active tab is synced
 * with the current interview block (via BLOCK_TO_TAB mapping).
 */
export function BrandPreviewSections({ currentBlock }: PreviewSectionsProps) {
  const { settings } = useBrandSettings();
  const previewData = useCopilotStore((s) => s.previewData);

  // Active tab — user-selected or derived from current interview block
  const [manualTab, setManualTab] = useState<BrandSectionId | null>(null);

  const activeTab: BrandSectionId =
    manualTab ?? (currentBlock ? (BLOCK_TO_TAB[currentBlock] ?? "esencia") : "esencia");

  // Merge live settings with interview draft data
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
    <>
      {/* Tab bar for switching preview sections */}
      <BrandStudioTabs activeTab={activeTab} onTabChange={setManualTab} settings={mergedSettings} />

      {/* Section preview content */}
      <div className="flex-1 overflow-hidden">
        <ScrollArea className="h-full">
          <PreviewSection activeTab={activeTab} />
        </ScrollArea>
      </div>
    </>
  );
}
