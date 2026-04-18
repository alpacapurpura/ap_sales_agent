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

/** Static lazy-loaded entry — components resolved on demand via dynamic import. */
export interface PreviewRegistryEntry {
  summaryComponent: () => Promise<{ default: ComponentType<PreviewSummaryProps> }>;
  sectionsComponent: () => Promise<{ default: ComponentType<PreviewSectionsProps> }>;
  emptyStateMessage: string;
}

// ── Static registry (lazy imports, no side-effects) ─────────────────────────
//
// Brand and buyer_persona entries were removed alongside the Sprint 5 deletion
// of features/brand/: the sidebar-hosted preview pane is going away entirely
// (see DECISIONS.md D5) so only the still-live offer flow remains listed.
// Sprint 4c removes this registry together with CopilotPreviewPane and the
// remaining offer preview renderers.

const PREVIEW_REGISTRY: Record<string, PreviewRegistryEntry> = {
  offer: {
    summaryComponent: () =>
      import("@/features/offer-studio/components/interview/previews/OfferPreviewSummary").then(
        (m) => ({ default: m.OfferPreviewSummary }),
      ),
    sectionsComponent: () =>
      import("@/features/offer-studio/components/interview/previews/OfferPreviewSections").then(
        (m) => ({ default: m.OfferPreviewSections }),
      ),
    emptyStateMessage: "Describe tu oferta para ver la vista previa en vivo.",
  },
};

// ── Public API ───────────────────────────────────────────────────────────────

/**
 * Returns the lazy registry entry for a domain, or null if unsupported.
 * Prefer this over getPreview() in new code.
 */
export function getPreviewEntry(domain: string): PreviewRegistryEntry | null {
  return PREVIEW_REGISTRY[domain] ?? null;
}

/**
 * Returns the list of supported interview domains.
 */
export function getSupportedDomains(): string[] {
  return Object.keys(PREVIEW_REGISTRY);
}
