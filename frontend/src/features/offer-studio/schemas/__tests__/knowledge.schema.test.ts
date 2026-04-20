import { describe, expect, it } from "vitest";

import { parseSectionSchema } from "@/lib/form-runtime/schema";

import { offerKnowledgeSchema } from "../knowledge.schema";

describe("offerKnowledgeSchema", () => {
  it("parses as a valid SectionSchema", () => {
    expect(() => parseSectionSchema(offerKnowledgeSchema)).not.toThrow();
  });

  it("declares offer_level scope and the canonical key", () => {
    expect(offerKnowledgeSchema.scope).toBe("offer_level");
    expect(offerKnowledgeSchema.key).toBe("offer.knowledge");
  });

  it("routes document uploads through a registered custom action", () => {
    const docs = offerKnowledgeSchema.fields.find((f) => f.id === "documents");
    expect(docs?.type).toBe("custom");
    expect(docs?.action).toBe("offer-knowledge-uploader");
  });
});
