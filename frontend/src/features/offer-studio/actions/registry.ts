/**
 * Offer-studio action registry bootstrap.
 *
 * Register every action key referenced by the offer-studio schemas. Sprint
 * 15 points each key at a placeholder; subsequent sprints replace each
 * entry with the real ported component via
 * ``registerAction(key, Real, { override: true })``.
 *
 * Side-effect import: ``features/offer-studio/schemas/index.ts`` imports
 * this module once so every page that consumes a schema gets the registry
 * populated transitively — no per-page side-effect imports required.
 *
 * Homologated with ``features/brand-studio/actions/registry.ts`` — same
 * pattern: tuple of keys + typed registry entries + idempotent bootstrap.
 */
import { hasAction, registerAction, type ActionComponent } from "@/lib/form-runtime/actions";

import {
  EditionPricingOverridePlaceholder,
  FAQBuilderPlaceholder,
  GalleryMultiImagePlaceholder,
  GallerySingleImagePlaceholder,
  InstructorsPickerPlaceholder,
  KnowledgeUploaderPlaceholder,
  PaymentProviderPickerPlaceholder,
  PricingOptionsBuilderPlaceholder,
  PricingTiersBuilderPlaceholder,
  SchedulingEventTypePickerPlaceholder,
  SocialProofPickerPlaceholder,
  ValueStackBuilderPlaceholder,
} from "./placeholders";

export const OFFER_STUDIO_ACTION_KEYS = [
  "offer-pricing-options-builder",
  "offer-pricing-tiers-builder",
  "offer-knowledge-uploader",
  "offer-instructors-picker",
  "offer-gallery-single-image",
  "offer-gallery-multi-image",
  "payment-provider-picker",
  "scheduling-event-type-picker",
  "offer-social-proof-picker",
  "offer-value-stack-builder",
  "offer-faq-builder",
  "offer-edition-pricing-override",
] as const;

export type OfferStudioActionKey = (typeof OFFER_STUDIO_ACTION_KEYS)[number];

/**
 * Current component each key resolves to. Placeholders render a muted
 * "pendiente" card — later sprints swap each entry with the real action
 * without touching consumers.
 */
const REGISTRY_ENTRIES: Readonly<Record<OfferStudioActionKey, ActionComponent>> = {
  "offer-pricing-options-builder": PricingOptionsBuilderPlaceholder,
  "offer-pricing-tiers-builder": PricingTiersBuilderPlaceholder,
  "offer-knowledge-uploader": KnowledgeUploaderPlaceholder,
  "offer-instructors-picker": InstructorsPickerPlaceholder,
  "offer-gallery-single-image": GallerySingleImagePlaceholder,
  "offer-gallery-multi-image": GalleryMultiImagePlaceholder,
  "payment-provider-picker": PaymentProviderPickerPlaceholder,
  "scheduling-event-type-picker": SchedulingEventTypePickerPlaceholder,
  "offer-social-proof-picker": SocialProofPickerPlaceholder,
  "offer-value-stack-builder": ValueStackBuilderPlaceholder,
  "offer-faq-builder": FAQBuilderPlaceholder,
  "offer-edition-pricing-override": EditionPricingOverridePlaceholder,
};

/**
 * Registers every offer-studio action. Idempotent — each key is only
 * registered if the registry does not already have it, so it tolerates
 * registry resets (tests) and partial real-action upgrades.
 */
export function bootstrapOfferStudioActions(): void {
  for (const key of OFFER_STUDIO_ACTION_KEYS) {
    if (hasAction(key)) continue;
    registerAction(key, REGISTRY_ENTRIES[key]);
  }
}

// Auto-bootstrap on module load so consumers don't have to remember to call it.
bootstrapOfferStudioActions();
