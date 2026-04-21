/**
 * Architecture Fitness Test — Field Help Coverage
 *
 * Enforces that every FieldSchema across brand-studio and offer-studio
 * has a meaningful hint text. Uses a ratchet/allowlist pattern:
 *  - KNOWN_FIELDS_WITHOUT_HINT: technical/internal fields that don't
 *    benefit from user-facing help. Shrinks only — add justification.
 *  - KNOWN_HINT_LENGTH_VIOLATIONS: fields whose existing hints exceed
 *    the 240-char cap. Shrinks only — shorten on next touch.
 * Zero tolerance for voseo in Spanish hint text.
 */

import { describe, expect, it } from "vitest";

import { identitySchema } from "@/features/brand-studio/schemas/identity.schema";
import { positioningSchema } from "@/features/brand-studio/schemas/positioning.schema";
import { buyerPersonaSchema } from "@/features/brand-studio/schemas/buyer-persona.schema";
import { narrativeSchema } from "@/features/brand-studio/schemas/narrative.schema";
import { methodologySchema } from "@/features/brand-studio/schemas/methodology.schema";
import { storySchema } from "@/features/brand-studio/schemas/story.schema";
import { voiceSchema } from "@/features/brand-studio/schemas/voice.schema";
import { personalitySchema } from "@/features/brand-studio/schemas/personality.schema";
import { contactSchema } from "@/features/brand-studio/schemas/contact.schema";
import { logosSchema } from "@/features/brand-studio/schemas/logos.schema";
import { visualsSchema } from "@/features/brand-studio/schemas/visuals.schema";
import { avatarsSchema } from "@/features/brand-studio/schemas/avatars.schema";
import { communicationAssetsSchema } from "@/features/brand-studio/schemas/communication-assets.schema";
import { authorityItemSchema } from "@/features/brand-studio/schemas/authority-item.schema";
import { testimonialItemSchema } from "@/features/brand-studio/schemas/testimonial-item.schema";
import { teamMemberItemSchema } from "@/features/brand-studio/schemas/team-member-item.schema";

import { offerIdentitySchema } from "@/features/offer-studio/schemas/identity.schema";
import { offerPromiseSchema } from "@/features/offer-studio/schemas/promise.schema";
import { offerValueStackSchema } from "@/features/offer-studio/schemas/value-stack.schema";
import { offerStrategySchema } from "@/features/offer-studio/schemas/strategy.schema";
import { offerPsychologySchema } from "@/features/offer-studio/schemas/psychology.schema";
import { offerClosingSchema } from "@/features/offer-studio/schemas/closing.schema";
import { offerPricingSchema } from "@/features/offer-studio/schemas/pricing.schema";
import { offerProgramDetailsSchema } from "@/features/offer-studio/schemas/program-details.schema";
import { offerServiceDetailsSchema } from "@/features/offer-studio/schemas/service-details.schema";
import { offerEventDetailsSchema } from "@/features/offer-studio/schemas/event-details.schema";
import { offerTestimonialsSchema } from "@/features/offer-studio/schemas/testimonials.schema";
import { offerPortfolioSchema } from "@/features/offer-studio/schemas/portfolio.schema";
import { offerFaqSchema } from "@/features/offer-studio/schemas/faq.schema";
import { offerGallerySchema } from "@/features/offer-studio/schemas/gallery.schema";
import { offerKnowledgeSchema } from "@/features/offer-studio/schemas/knowledge.schema";
import { offerResourcesSchema } from "@/features/offer-studio/schemas/resources.schema";

import type { FieldSchema, SectionSchema } from "@/lib/form-runtime/schema";

// ─── Allowlists (ratchet — shrinks only) ────────────────────────────────────

/**
 * Fields that genuinely don't need a user-facing hint:
 * - URL/logo upload slots: the action UI handles guidance
 * - Pure numeric/text IDs resolved at runtime (concept_id)
 * - Fields whose label is self-explanatory and strictly formatted
 * Goal for this sprint: 0 fields in this list.
 */
const KNOWN_FIELDS_WITHOUT_HINT = new Set<string>([
  // brand.logos — URL upload slots handled by the logo-kit custom action
  "logos.primary",
  "logos.secondary",
  "logos.dark_mode",
  "logos.light_mode",
  "logos.favicon",
  // brand.visuals — colors/fonts managed via the visuals wizard action
  "visuals.theme_injector",
  "visuals.primary_color",
  "visuals.secondary_color",
  "visuals.accent_color",
  "visuals.background_color",
  "visuals.surface_color",
  "visuals.text_primary_color",
  "visuals.text_secondary_color",
  "visuals.font_heading",
  "visuals.font_body",
  "visuals.font_accent",
  "visuals.design_style",
  "visuals.photography_style",
  "visuals.icon_style",
  "visuals.logo_url",
  "visuals.logo_picker",
  "visuals.favicon_url",
  // communication-assets — internal workflow items with label-sufficient context
  "communication-assets.creative_concepts.name",
  "communication-assets.creative_concepts.description",
  "communication-assets.creative_concepts.tone",
  "communication-assets.assets.title",
  "communication-assets.assets.funnel_stage",
  "communication-assets.assets.asset_type",
  "communication-assets.assets.idea",
  "communication-assets.assets.copy_draft",
  "communication-assets.assets.objective",
  "communication-assets.assets.concept_id",
  "communication-assets.assets.status",
  // team-member — social URL fields: label is self-explanatory
  "team-member.personal_website",
  "team-member.personal_linkedin",
  "team-member.personal_instagram",
  "team-member.personal_tiktok",
  "team-member.personal_facebook",
  // testimonial-item — straightforward media metadata
  "testimonial-item.author_avatar_url",
  "testimonial-item.media_type",
  "testimonial-item.rating",
  "testimonial-item.captured_at",
  // authority-item
  "authority-item.obtained_at",
  // offer.gallery — before/after image slots: label self-explanatory
  "offer.gallery.before_after_pairs.before_url",
  "offer.gallery.before_after_pairs.after_url",
  "offer.gallery.before_after_pairs.caption",
  // offer.resources.edition_resources — short text fields with placeholder
  "offer.resources.edition_resources.name",
  "offer.resources.edition_resources.type",
  "offer.resources.edition_resources.url",
  "offer.resources.edition_resources.description",
  // offer.portfolio nested metrics — numeric breakdown, label self-explanatory
  "offer.portfolio.cases.results_metrics.metric",
  "offer.portfolio.cases.results_metrics.value",
  "offer.portfolio.cases.results_metrics.timeframe",
  // offer.program_details schedule sub-fields — factual logistics
  "offer.program_details.schedule.title",
  "offer.program_details.schedule.day_of_week",
  "offer.program_details.schedule.time",
  "offer.program_details.schedule.duration_minutes",
  // offer.program_details curriculum topics sub-field
  "offer.program_details.curriculum.description",
  "offer.program_details.curriculum.topics",
]);

/**
 * Fields whose hint currently exceeds 240 chars.
 * Shrinks only — shorten hint on next touch.
 */
const KNOWN_HINT_LENGTH_VIOLATIONS = new Set<string>([]);

// ─── Helpers ─────────────────────────────────────────────────────────────────

interface CollectedField {
  qualifiedId: string;
  field: FieldSchema;
}

function collectAllFields(schema: SectionSchema, prefix: string): CollectedField[] {
  const result: CollectedField[] = [];

  function walk(fields: FieldSchema[], currentPrefix: string) {
    for (const field of fields) {
      const qualifiedId = `${currentPrefix}.${field.id}`;
      result.push({ qualifiedId, field });
      if (field.itemSchema?.fields) {
        walk(field.itemSchema.fields, qualifiedId);
      }
    }
  }

  walk(schema.fields, prefix);
  return result;
}

const ALL_SCHEMAS: [string, SectionSchema][] = [
  // brand-studio
  ["identity", identitySchema],
  ["positioning", positioningSchema],
  ["buyer-persona", buyerPersonaSchema],
  ["narrative", narrativeSchema],
  ["methodology", methodologySchema],
  ["story", storySchema],
  ["voice", voiceSchema],
  ["personality", personalitySchema],
  ["contact", contactSchema],
  ["logos", logosSchema],
  ["visuals", visualsSchema],
  ["avatars", avatarsSchema],
  ["communication-assets", communicationAssetsSchema],
  ["authority-item", authorityItemSchema],
  ["testimonial-item", testimonialItemSchema],
  ["team-member", teamMemberItemSchema],
  // offer-studio
  ["offer.identity", offerIdentitySchema],
  ["offer.promise", offerPromiseSchema],
  ["offer.value_stack", offerValueStackSchema],
  ["offer.strategy", offerStrategySchema],
  ["offer.psychology", offerPsychologySchema],
  ["offer.closing", offerClosingSchema],
  ["offer.pricing", offerPricingSchema],
  ["offer.program_details", offerProgramDetailsSchema],
  ["offer.service_details", offerServiceDetailsSchema],
  ["offer.event_details", offerEventDetailsSchema],
  ["offer.testimonials", offerTestimonialsSchema],
  ["offer.portfolio", offerPortfolioSchema],
  ["offer.faq", offerFaqSchema],
  ["offer.gallery", offerGallerySchema],
  ["offer.knowledge", offerKnowledgeSchema],
  ["offer.resources", offerResourcesSchema],
];

const VOSEO_PATTERN =
  /\bvos\b|\btenés\b|\bhacés\b|\bquerés\b|\bpodés\b|\bsabés\b|\bmirá\b|\bdejá\b|\bfijate\b|\bsondes\b|\bponés\b|\busás\b/i;

// ─── Tests ────────────────────────────────────────────────────────────────────

describe("Field help coverage", () => {
  const allFields: CollectedField[] = [];
  for (const [prefix, schema] of ALL_SCHEMAS) {
    allFields.push(...collectAllFields(schema, prefix));
  }

  it("every field either has a hint or is allowlisted", () => {
    const missing: string[] = [];
    for (const { qualifiedId, field } of allFields) {
      if (!field.hint && !KNOWN_FIELDS_WITHOUT_HINT.has(qualifiedId)) {
        missing.push(qualifiedId);
      }
    }
    expect(missing, `Fields missing hint (add hint or allowlist): ${missing.join(", ")}`).toEqual(
      [],
    );
  });

  it("all hints are between 15 and 240 characters", () => {
    const violations: string[] = [];
    for (const { qualifiedId, field } of allFields) {
      if (!field.hint) continue;
      const len = field.hint.length;
      if (len < 15 || len > 240) {
        if (!KNOWN_HINT_LENGTH_VIOLATIONS.has(qualifiedId)) {
          violations.push(`${qualifiedId} (${len} chars)`);
        }
      }
    }
    expect(
      violations,
      `Hints outside 15–240 char range (fix or allowlist): ${violations.join(", ")}`,
    ).toEqual([]);
  });

  it("no voseo in any hint text (zero tolerance)", () => {
    const violations: string[] = [];
    for (const { qualifiedId, field } of allFields) {
      if (field.hint && VOSEO_PATTERN.test(field.hint)) {
        violations.push(`${qualifiedId}: "${field.hint}"`);
      }
    }
    expect(violations, `Voseo detected in hints: ${violations.join("\n")}`).toEqual([]);
  });
});
