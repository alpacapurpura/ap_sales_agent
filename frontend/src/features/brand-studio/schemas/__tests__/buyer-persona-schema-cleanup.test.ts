import { describe, it, expect } from "vitest";

import { buyerPersonaSchema } from "../buyer-persona.schema";

/**
 * Regression tests for PR-1-drop-buyer-persona-fields (PI-4 S1).
 * Asserts that the `objections` and `preferred_channels` array fields
 * have been removed from the buyer-persona form schema.
 */
describe("buyerPersonaSchema cleanup PR-1", () => {
  it("does not contain objections field", () => {
    const ids = buyerPersonaSchema.fields.map((f) => f.id);
    expect(ids).not.toContain("objections");
  });

  it("does not contain preferred_channels field", () => {
    const ids = buyerPersonaSchema.fields.map((f) => f.id);
    expect(ids).not.toContain("preferred_channels");
  });

  it("retains pain_points and desires fields", () => {
    const ids = buyerPersonaSchema.fields.map((f) => f.id);
    expect(ids).toContain("pain_points");
    expect(ids).toContain("desires");
  });
});
