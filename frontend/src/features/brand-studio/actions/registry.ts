/**
 * Brand-studio action registry bootstrap.
 *
 * Register every action key referenced by the brand-studio schemas. Sprint 1
 * points each key at a placeholder; Sprint 2 replaces each entry with the
 * real ported component via `registerAction(key, Real, { override: true })`.
 *
 * Side-effect import: features/brand-studio/pages/* should import this module
 * once at the top so the registry is populated before any schema renders a
 * custom field.
 */
import { hasAction, registerAction, type ActionComponent } from "@/lib/form-runtime/actions";

import {
  AvatarActionPlaceholder,
  BrandVisualsWizardPlaceholder,
  DimensionSlidersPlaceholder,
  ImageGalleryPickerPlaceholder,
  LegalActionPlaceholder,
  LogoKitPlaceholder,
  OnboardingWizardPlaceholder,
  PersonalityClonePlaceholder,
  PresetCatalogPlaceholder,
  SingleImagePickerPlaceholder,
  SmartFillDialogPlaceholder,
  VoiceClonePlaceholder,
} from "./placeholders";
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
  "legal",
] as const;

export type BrandStudioActionKey = (typeof BRAND_STUDIO_ACTION_KEYS)[number];

const PLACEHOLDERS: Readonly<Record<BrandStudioActionKey, ActionComponent>> = {
  "voice-clone": VoiceClonePlaceholder,
  "personality-clone": PersonalityClonePlaceholder,
  "personality-dimensions": DimensionSlidersPlaceholder,
  "personality-presets": PresetCatalogPlaceholder,
  "brand-visuals-wizard": BrandVisualsWizardPlaceholder,
  "single-image": SingleImagePickerPlaceholder,
  "theme-injector": ThemeInjectorAction,
  "logo-kit": LogoKitPlaceholder,
  "image-gallery": ImageGalleryPickerPlaceholder,
  avatar: AvatarActionPlaceholder,
  "smart-fill": SmartFillDialogPlaceholder,
  "onboarding-wizard": OnboardingWizardPlaceholder,
  legal: LegalActionPlaceholder,
};

/**
 * Registers every brand-studio action. Idempotent — each key is only
 * registered if the registry does not already have it, so it tolerates
 * registry resets (tests) and partial real-action upgrades (Sprint 2).
 */
export function bootstrapBrandStudioActions(): void {
  for (const key of BRAND_STUDIO_ACTION_KEYS) {
    if (hasAction(key)) continue;
    registerAction(key, PLACEHOLDERS[key]);
  }
}

// Auto-bootstrap on module load so consumers don't have to remember to call it.
bootstrapBrandStudioActions();
