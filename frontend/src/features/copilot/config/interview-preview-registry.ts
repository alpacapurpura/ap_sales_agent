import type { ComponentType } from "react";

// ── Types ───────────────────────────────────────────────────────────────────

export interface PreviewSummaryProps {
  data: Record<string, unknown>;
  completenessScore: number;
}

export interface PreviewSectionsProps {
  data: Record<string, unknown>;
  currentBlock: string;
  blocksCompleted: string[];
}

export interface PreviewTabsProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
  data: Record<string, unknown>;
}

export interface PreviewConfig {
  summaryComponent: ComponentType<PreviewSummaryProps>;
  sectionsComponent: ComponentType<PreviewSectionsProps>;
  tabsComponent?: ComponentType<PreviewTabsProps>;
  emptyStateMessage: string;
}

// ── Registry ────────────────────────────────────────────────────────────────

const PREVIEW_REGISTRY: Record<string, PreviewConfig> = {};

/**
 * Register a preview configuration for a given interview domain.
 * Each domain (brand, buyer_persona, offer) registers its own
 * preview components here so the generic InterviewSplitView can
 * render domain-specific previews without tight coupling.
 */
export function registerPreview(domain: string, config: PreviewConfig): void {
  PREVIEW_REGISTRY[domain] = config;
}

/**
 * Retrieve the preview configuration for a domain.
 * @throws {Error} if no preview is registered for the domain.
 */
export function getPreview(domain: string): PreviewConfig {
  const config = PREVIEW_REGISTRY[domain];
  if (!config) {
    throw new Error(`No preview registered for domain: ${domain}`);
  }
  return config;
}

/**
 * Clear the registry. Used only in tests to ensure isolation.
 */
export function clearPreviewRegistry(): void {
  for (const key of Object.keys(PREVIEW_REGISTRY)) {
    delete PREVIEW_REGISTRY[key];
  }
}
