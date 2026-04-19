"use client";

import { BusinessTypesSection } from "@/features/brand-studio/components/business-types/BusinessTypesSection";
import { useBrandSettings } from "@/features/brand-studio/hooks/use-brand-settings";
import {
  authoritySchema,
  communicationAssetsSchema,
  contactSchema,
  identitySchema,
  methodologySchema,
  narrativeSchema,
  positioningSchema,
  storySchema,
  teamSchema,
  testimonialsSchema,
  visualsSchema,
} from "@/features/brand-studio/schemas";

import { SectionPage } from "./SectionPage";

import type {
  AuthorityItem,
  BrandIdentity,
  BrandNarrative,
  BrandPositioning,
  BrandSettings,
  BrandStory,
  BrandStrategy,
  BrandVisuals,
  CommunicationAssets,
  ContactData,
  KeyFigure,
  TestimonialItem,
} from "@/features/brand-studio/types";

/**
 * Factory-generated page components for every brand-studio section whose
 * data lives under `BrandSettings` and whose save flow goes through one of
 * `useBrandSettings`' updater functions. Each page is 1-liner boilerplate;
 * differences live in the factory config.
 *
 * Special sections NOT generated here (separate hooks or nested shapes):
 *   - personality  → own API via usePersonalityHooks (see Sprint 2 deferred).
 *   - voice        → subset of identity (voice_tone); renders under identity page.
 *   - logos        → nested under visuals.logos; renders under visuals page.
 *   - avatars      → sub-entity, covered by PersonaDetailPage (Sprint 2.8).
 */
const IdentityCorePage = createPage<BrandIdentity>({
  slug: "identity",
  schema: identitySchema,
  select: (s) => s.identity,
  save: (h) => h.updateIdentity,
});

/**
 * Brand Studio → Identity page. Composes the factory-generated form with
 * a read-only ``BusinessTypesSection`` at the foot so the user can always
 * see which business types drive the Offer Studio preset filter — without
 * cluttering the form schema itself (business_types remain managed
 * through the onboarding dialog, which is the single edit surface).
 */
export function IdentityPage() {
  return (
    <div className="space-y-6">
      <IdentityCorePage />
      <BusinessTypesSection />
    </div>
  );
}
IdentityPage.displayName = "BrandIdentityPage";

export const VisualsPage = createPage<BrandVisuals>({
  slug: "visuals",
  schema: visualsSchema,
  select: (s) => s.visuals,
  save: (h) => h.updateVisuals,
});

export const TeamPage = createPage<KeyFigure[]>({
  slug: "team",
  schema: teamSchema,
  select: (s) => s.team,
  save: (h) => h.updateTeam,
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

export const TestimonialsPage = createPage<TestimonialItem[]>({
  slug: "testimonials",
  schema: testimonialsSchema,
  select: (s) => s.testimonials,
  save: (h) => h.updateTestimonials,
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

export const AuthorityPage = createPage<AuthorityItem[]>({
  slug: "authority",
  schema: authoritySchema,
  select: (s) => s.authority_vault,
  save: (h) => h.updateVault,
});

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
