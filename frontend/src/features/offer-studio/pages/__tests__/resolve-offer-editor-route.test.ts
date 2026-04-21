import { describe, expect, it } from "vitest";

import { resolveOfferEditorRoute } from "../resolve-offer-editor-route";

describe("resolveOfferEditorRoute", () => {
  const baseParams = {
    tenantId: "8f2894db-81dd-4f06-86ff-80318e7d6831",
    offerId: "02ccdb9f-e872-4648-bd84-43de1d7a429e",
    section: "program_details",
  };
  const EXPECTED_BASE =
    "/8f2894db-81dd-4f06-86ff-80318e7d6831/offer-studio/offer/02ccdb9f-e872-4648-bd84-43de1d7a429e/editor/program_details";

  it("returns null activeFieldId and bare section path at section root", () => {
    const result = resolveOfferEditorRoute(baseParams);
    expect(result.activeFieldId).toBeNull();
    expect(result.sectionBasePath).toBe(EXPECTED_BASE);
  });

  it("extracts active fieldId from catch-all single value", () => {
    const result = resolveOfferEditorRoute({
      ...baseParams,
      fieldId: ["weekly_time_commitment_hours"],
    });
    expect(result.activeFieldId).toBe("weekly_time_commitment_hours");
    expect(result.sectionBasePath).toBe(EXPECTED_BASE);
  });

  it("ignores trailing stale fieldId segments and keeps base path clean (regression)", () => {
    // Bug: clicking successive fields kept appending to URL
    // (/editor/section/f1/f2/f3 instead of replacing to /editor/section/f3).
    // sectionBasePath MUST be the section root regardless of how many
    // segments landed in the catch-all.
    const result = resolveOfferEditorRoute({
      ...baseParams,
      fieldId: ["weekly_time_commitment_hours", "curriculum", "interaction_type"],
    });
    expect(result.activeFieldId).toBe("weekly_time_commitment_hours");
    expect(result.sectionBasePath).toBe(EXPECTED_BASE);
  });

  it("handles string fieldId (single optional catch-all shape)", () => {
    const result = resolveOfferEditorRoute({
      ...baseParams,
      fieldId: "curriculum",
    });
    expect(result.activeFieldId).toBe("curriculum");
  });

  it("returns null activeFieldId when catch-all array is empty", () => {
    const result = resolveOfferEditorRoute({ ...baseParams, fieldId: [] });
    expect(result.activeFieldId).toBeNull();
  });
});
