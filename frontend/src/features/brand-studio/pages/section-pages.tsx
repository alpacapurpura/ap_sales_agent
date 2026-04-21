"use client";

import { useParams } from "next/navigation";

import { CommunicationStyleView } from "@/features/brand-studio/components/communication-style/CommunicationStyleView";
import { useBrandSettings } from "@/features/brand-studio/hooks/use-brand-settings";
import {
  communicationAssetsSchema,
  contactSchema,
  identitySchema,
  legalSchema,
  methodologySchema,
  narrativeSchema,
  positioningSchema,
  storySchema,
  visualsSchema,
} from "@/features/brand-studio/schemas";

import { SectionPage } from "./SectionPage";

import type {
  BrandIdentity,
  BrandNarrative,
  BrandPositioning,
  BrandSettings,
  BrandStory,
  BrandStrategy,
  BrandVisuals,
  CommunicationAssets,
  ContactData,
} from "@/features/brand-studio/types";

/**
 * Factory-generated page components for every brand-studio section whose
 * data lives under `BrandSettings` and whose save flow goes through one of
 * `useBrandSettings`' updater functions. Each page is 1-liner boilerplate;
 * differences live in the factory config.
 *
 * Special sections NOT generated here (separate hooks or nested shapes):
 *   - estilo       → top-level "Estilo Comunicacional" section backed by
 *                    personality_profiles table via CommunicationStyleView.
 *   - logos        → nested under visuals.logos; renders under visuals page.
 *   - avatars      → sub-entity, covered by PersonaDetailPage.
 */
const IdentityCorePage = createPage<BrandIdentity>({
  slug: "identity",
  schema: identitySchema,
  select: (s) => s.identity,
  save: (h) => h.updateIdentity,
});

export const IdentityPage = IdentityCorePage;

/**
 * Legal y cumplimiento page. Shares the BrandIdentity slice with IdentityPage
 * so the 23 legal fields persist alongside the core identity — the schema
 * picks only the legal-relevant paths and autosave merges them into the
 * existing identity blob through ``updateIdentity``.
 */
export const LegalPage = createPage<BrandIdentity>({
  slug: "legal",
  schema: legalSchema,
  select: (s) => s.identity,
  save: (h) => h.updateIdentity,
});

export const VisualsPage = createPage<BrandVisuals>({
  slug: "visuals",
  schema: visualsSchema,
  select: (s) => s.visuals,
  save: (h) => h.updateVisuals,
});

export const ContactPage = createPage<ContactData>({
  slug: "contact",
  schema: contactSchema,
  select: (s) => s.contact,
  save: (h) => h.updateContact,
});

export const MethodologyPage = createPage<BrandStrategy>({
  slug: "methodology",
  schema: methodologySchema,
  select: (s) => s.strategy,
  save: (h) => h.updateStrategy,
});

export const StoryPage = createPage<BrandStory>({
  slug: "story",
  schema: storySchema,
  select: (s) => s.story,
  save: (h) => h.updateStory,
});

export const PositioningPage = createPage<BrandPositioning>({
  slug: "positioning",
  schema: positioningSchema,
  select: (s) => s.positioning,
  save: (h) => h.updatePositioning,
});

export const NarrativePage = createPage<BrandNarrative>({
  slug: "narrative",
  schema: narrativeSchema,
  select: (s) => s.narrative,
  save: (h) => h.updateNarrative,
});

export const CommunicationAssetsPage = createPage<CommunicationAssets>({
  slug: "communication-assets",
  schema: communicationAssetsSchema,
  select: (s) => s.communication_assets,
  save: (h) => h.updateCommunicationAssets,
});

// ── Estilo Comunicacional ─────────────────────────────────────────────────────

/**
 * Estilo Comunicacional page. Backed by `personality_profiles` table, not
 * `BrandSettings` JSONB — so it does NOT use the `createPage` factory.
 * Reads the legacy `voice_tone` field from `BrandSettings.identity` to
 * offer the one-time migration card to tenants with existing text.
 */
export function CommunicationStylePage() {
  const params = useParams<{ tenantId: string }>();
  const { tenantId } = params;
  const hook = useBrandSettings();
  const voiceToneLegacy = hook.settings?.identity?.voice_tone ?? null;
  // Dismissed flag is persisted in localStorage inside MigrationCard itself.
  // We pass false here; MigrationCard reads localStorage on mount.
  return (
    <CommunicationStyleView
      tenantId={tenantId}
      voiceToneLegacy={voiceToneLegacy}
      voiceToneMigrationDismissed={false}
    />
  );
}

// SECTION_PAGE_MAP + BrandStudioSectionSlug live in ./section-page-map.ts
// so Server Components can index the map. See that module's header comment
// for the full rationale.

// ── factory ──────────────────────────────────────────────────────────────────

type BrandSettingsHook = ReturnType<typeof useBrandSettings>;

interface PageConfig<TSlice extends object> {
  slug: string;
  schema: Parameters<typeof SectionPage<TSlice>>[0]["schema"];
  /** Extract the slice this page edits from the BrandSettings root object. */
  select: (settings: BrandSettings) => TSlice | null | undefined;
  /** Return the updater function from the hook result (stable reference). */
  save: (hook: BrandSettingsHook) => (next: TSlice) => Promise<unknown>;
}

function createPage<TSlice extends object>(config: PageConfig<TSlice>) {
  function BrandSectionPage() {
    const hook = useBrandSettings();
    const values = hook.settings ? config.select(hook.settings) : undefined;
    const save = config.save(hook);
    return (
      <SectionPage
        sectionSlug={config.slug}
        schema={config.schema}
        values={values ?? undefined}
        onSave={async (next) => {
          await save(next);
        }}
        isLoading={hook.loading}
      />
    );
  }
  BrandSectionPage.displayName = `BrandSectionPage(${config.slug})`;
  return BrandSectionPage;
}
