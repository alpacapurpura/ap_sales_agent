/**
 * ARCH TEST: Section SSoT — offer-studio schemas must not re-declare section copy.
 *
 * The backend ``SECTION_CATALOG`` is the single source of truth for every
 * section's ``label_es`` + ``subtitle_es`` + ``help_text_es`` + ``icon_name``
 * (see ``.claude/rules/offer-catalogs.md``). Each offer-studio schema only
 * declares structure (``key``, ``scope``, ``fields``); presentation copy is
 * resolved on the consumer page via ``useSectionMetadata(sectionKey)`` and
 * passed to ``UniversalEditableSection`` through ``titleOverride`` +
 * ``descriptionOverride`` props.
 *
 * Legacy ``brand-studio/schemas/`` retains inline ``title`` + ``description``
 * until a future rework — this test scopes the check to offer-studio only.
 */
import { describe, it, expect } from "vitest";

import {
  offerClosingSchema,
  offerEventDetailsSchema,
  offerGallerySchema,
  offerIdentitySchema,
  offerInstructorsSchema,
  offerKnowledgeSchema,
  offerPricingSchema,
  offerProductDetailsSchema,
  offerProgramDetailsSchema,
  offerPromiseSchema,
  offerPsychologySchema,
  offerResourcesSchema,
  offerServiceDetailsSchema,
  offerStrategySchema,
  offerSubscriptionDetailsSchema,
  offerValueStackSchema,
} from "@/features/offer-studio/schemas";

import type { SectionSchema } from "@/lib/form-runtime/schema";

const OFFER_STUDIO_SCHEMAS: ReadonlyArray<readonly [string, SectionSchema]> = [
  ["offerClosingSchema", offerClosingSchema],
  ["offerEventDetailsSchema", offerEventDetailsSchema],
  ["offerGallerySchema", offerGallerySchema],
  ["offerIdentitySchema", offerIdentitySchema],
  ["offerInstructorsSchema", offerInstructorsSchema],
  ["offerKnowledgeSchema", offerKnowledgeSchema],
  ["offerPricingSchema", offerPricingSchema],
  ["offerProductDetailsSchema", offerProductDetailsSchema],
  ["offerProgramDetailsSchema", offerProgramDetailsSchema],
  ["offerPromiseSchema", offerPromiseSchema],
  ["offerPsychologySchema", offerPsychologySchema],
  ["offerResourcesSchema", offerResourcesSchema],
  ["offerServiceDetailsSchema", offerServiceDetailsSchema],
  ["offerStrategySchema", offerStrategySchema],
  ["offerSubscriptionDetailsSchema", offerSubscriptionDetailsSchema],
  ["offerValueStackSchema", offerValueStackSchema],
];

describe("Architecture: offer-studio schemas don't duplicate SectionCatalog copy", () => {
  it("all offer-studio schemas omit ``title`` (catalog-driven)", () => {
    const violations = OFFER_STUDIO_SCHEMAS.filter(
      ([, schema]) => schema.title !== undefined,
    ).map(([name, schema]) => `${name} declares title="${schema.title!}"`);
    expect(violations).toEqual([]);
  });

  it("all offer-studio schemas omit ``description`` (catalog-driven)", () => {
    const violations = OFFER_STUDIO_SCHEMAS.filter(
      ([, schema]) => schema.description !== undefined,
    ).map(([name, schema]) => `${name} declares description="${schema.description!}"`);
    expect(violations).toEqual([]);
  });

  it("all offer-studio schemas declare ``key`` and ``fields``", () => {
    for (const [name, schema] of OFFER_STUDIO_SCHEMAS) {
      expect(schema.key, `${name}: missing key`).toBeTruthy();
      expect(Array.isArray(schema.fields), `${name}: fields must be an array`).toBe(true);
      expect(schema.fields.length, `${name}: fields must be non-empty`).toBeGreaterThan(0);
    }
  });
});
