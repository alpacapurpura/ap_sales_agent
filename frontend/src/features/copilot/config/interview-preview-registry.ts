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

/** Backward-compatible config interface (sync components). Kept for legacy callers. */
export interface PreviewConfig {
  summaryComponent: ComponentType<PreviewSummaryProps>;
  sectionsComponent: ComponentType<PreviewSectionsProps>;
  tabsComponent?: ComponentType<PreviewTabsProps>;
  emptyStateMessage: string;
}

/** Static lazy-loaded entry — components resolved on demand via dynamic import. */
export interface PreviewRegistryEntry {
  summaryComponent: () => Promise<{ default: ComponentType<PreviewSummaryProps> }>;
  sectionsComponent: () => Promise<{ default: ComponentType<PreviewSectionsProps> }>;
  emptyStateMessage: string;
}

// ── Static registry (lazy imports, no side-effects) ─────────────────────────

const PREVIEW_REGISTRY: Record<string, PreviewRegistryEntry> = {
  brand: {
    summaryComponent: () =>
      import(
        "@/features/brand/components/interview/brand-preview-summary"
      ).then((m) => ({ default: m.BrandPreviewSummary })),
    sectionsComponent: () =>
      import(
        "@/features/brand/components/interview/brand-preview-sections"
      ).then((m) => ({ default: m.BrandPreviewSections })),
    emptyStateMessage: "Responde las preguntas para construir tu perfil de marca.",
  },
  offer: {
    summaryComponent: () =>
      import(
        "@/features/offer-studio/components/interview/previews/offer-preview-summary"
      ).then((m) => ({ default: m.OfferPreviewSummary })),
    sectionsComponent: () =>
      import(
        "@/features/offer-studio/components/interview/previews/offer-preview-sections"
      ).then((m) => ({ default: m.OfferPreviewSections })),
    emptyStateMessage: "Describe tu oferta para ver la vista previa en vivo.",
  },
  buyer_persona: {
    summaryComponent: () =>
      import(
        "@/features/brand/components/interview/previews/persona-preview-summary"
      ).then((m) => ({ default: m.PersonaPreviewSummary })),
    sectionsComponent: () =>
      import(
        "@/features/brand/components/interview/previews/persona-preview-sections"
      ).then((m) => ({ default: m.PersonaPreviewSections })),
    emptyStateMessage: "Comienza la entrevista para construir tu buyer persona.",
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

/**
 * Backward-compatible retrieval. Throws if the domain is not registered.
 * Callers will migrate to getPreviewEntry() in a future phase.
 *
 * @throws {Error} if no entry exists for the domain.
 */
export function getPreview(domain: string): PreviewConfig {
  const entry = getPreviewEntry(domain);
  if (!entry) {
    throw new Error(`No preview registered for domain: ${domain}`);
  }
  // Bridge to the old sync interface.
  // summaryComponent / sectionsComponent are intentionally null here —
  // lazy entries must be loaded asynchronously via getPreviewEntry().
  return {
    summaryComponent: null as any, // lazy — use getPreviewEntry() for async loading
    sectionsComponent: null as any, // lazy — use getPreviewEntry() for async loading
    emptyStateMessage: entry.emptyStateMessage,
  };
}

/**
 * No-op. Registry is now static; side-effect register-* imports still call
 * this function, but it does nothing.
 */
export function registerPreview(
  _domain: string,
  _config: PreviewConfig,
): void {
  // No-op: registry is static. Side-effect imports call this but it is ignored.
}

/**
 * No-op. Registry is static and cannot be cleared.
 * Kept for test isolation in legacy test files.
 */
export function clearPreviewRegistry(): void {
  // No-op: registry is static.
}
