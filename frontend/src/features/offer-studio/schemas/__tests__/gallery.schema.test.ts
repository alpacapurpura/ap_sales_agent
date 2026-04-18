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

  it("routes every visual through a registered custom action", () => {
    for (const field of offerGallerySchema.fields) {
      expect(field.type).toBe("custom");
      expect(field.action).toBeTruthy();
    }
  });
});
