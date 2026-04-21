/**
 * Brand-studio action registry bootstrap.
 *
 * Register every action key referenced by the brand-studio schemas. Sprint 1
 * points each key at a placeholder; Sprint 2 replaces each entry with the
 * real ported component via `registerAction(key, Real, { override: true })`.
 *
 * Side-effect import: features/brand-studio/schemas/index.ts imports this
 * module once so every page that consumes a schema gets the registry
 * populated transitively — no per-page side-effect imports required.
 */
import { hasAction, registerAction, type ActionComponent } from "@/lib/form-runtime/actions";

import { DimensionSlidersAction } from "./DimensionSlidersAction";
import { ImageGalleryPickerAction } from "./ImageGalleryPickerAction";
import { LogoKitAction } from "./LogoKitAction";
import {
  AvatarActionPlaceholder,
  BrandVisualsWizardPlaceholder,
  OnboardingWizardPlaceholder,
  PersonalityClonePlaceholder,
  SmartFillDialogPlaceholder,
  VoiceClonePlaceholder,
} from "./placeholders";
import { PresetCatalogAction } from "./PresetCatalogAction";
import { SingleImagePickerAction } from "./SingleImagePickerAction";
import { ThemeInjectorAction } from "./ThemeInjectorAction";

export const BRAND_STUDIO_ACTION_KEYS = [
  "voice-clone",
  "personality-clone",
  "personality-dimensions",
  "personality-presets",
  "brand-visuals-wizard",
  "single-image",
  "theme-injector",
  "logo-kit",
  "image-gallery",
  "avatar",
  "smart-fill",
  "onboarding-wizard",
] as const;

export type BrandStudioActionKey = (typeof BRAND_STUDIO_ACTION_KEYS)[number];

/**
 * Current component each key resolves to. Some are real ported actions,
 * the rest are placeholders pending port (Sprint 2.x) or migration to
 * copilot tools (Sprint 4).
 *
 * The `as unknown as ActionComponent` cast is required where the action
 * has a narrower TValue than the registry's generic default — TypeScript
 * treats `ActionComponent<string>` as non-assignable to
 * `ActionComponent<unknown>` due to function-parameter variance.
 */
const REGISTRY_ENTRIES: Readonly<Record<BrandStudioActionKey, ActionComponent>> = {
  "voice-clone": VoiceClonePlaceholder,
  "personality-clone": PersonalityClonePlaceholder,
  "personality-dimensions": DimensionSlidersAction as unknown as ActionComponent,
  "personality-presets": PresetCatalogAction as unknown as ActionComponent,
  "brand-visuals-wizard": BrandVisualsWizardPlaceholder,
  "single-image": SingleImagePickerAction as unknown as ActionComponent,
  "theme-injector": ThemeInjectorAction,
  "logo-kit": LogoKitAction as unknown as ActionComponent,
  "image-gallery": ImageGalleryPickerAction as unknown as ActionComponent,
  avatar: AvatarActionPlaceholder,
  "smart-fill": SmartFillDialogPlaceholder,
  "onboarding-wizard": OnboardingWizardPlaceholder,
};

/**
 * Registers every brand-studio action. Idempotent — each key is only
 * registered if the registry does not already have it, so it tolerates
 * registry resets (tests) and partial real-action upgrades (Sprint 2).
 */
export function bootstrapBrandStudioActions(): void {
  for (const key of BRAND_STUDIO_ACTION_KEYS) {
    if (hasAction(key)) continue;
    registerAction(key, REGISTRY_ENTRIES[key]);
  }
}

// Auto-bootstrap on module load so consumers don't have to remember to call it.
bootstrapBrandStudioActions();
