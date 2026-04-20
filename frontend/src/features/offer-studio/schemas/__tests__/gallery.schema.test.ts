import { describe, expect, it } from "vitest";

import { parseSectionSchema } from "@/lib/form-runtime/schema";

import { offerGallerySchema } from "../gallery.schema";

describe("offerGallerySchema", () => {
  it("parses as a valid SectionSchema", () => {
    expect(() => parseSectionSchema(offerGallerySchema)).not.toThrow();
  });

  it("declares offer_level scope and the canonical key", () => {
    expect(offerGallerySchema.scope).toBe("offer_level");
    expect(offerGallerySchema.key).toBe("offer.gallery");
  });

  it("routes every custom-uploader visual through a registered action", () => {
    // After the Latam simplification pass, the schema mixes `custom` actions
    // (hero / gallery / before-after) with a plain `url` field for the
    // YouTube/Vimeo demo video — no uploader needed.
    for (const field of offerGallerySchema.fields) {
      if (field.type === "custom") {
        expect(field.action).toBeTruthy();
      }
    }
  });

  it("includes the before/after pairs array for transformational offers", () => {
    const field = offerGallerySchema.fields.find((f) => f.id === "before_after_pairs");
    expect(field?.type).toBe("array");
    expect(field?.itemSchema).toBeTruthy();
  });
});
