import { describe, it, expect } from "vitest";

import { JOB_INVALIDATION_MAP } from "../job-invalidation-map";

describe("JOB_INVALIDATION_MAP", () => {
  const EXPECTED_MODULES = ["brand", "offer", "asset", "persona"] as const;

  it("has an entry for every expected module", () => {
    for (const mod of EXPECTED_MODULES) {
      expect(JOB_INVALIDATION_MAP).toHaveProperty(mod);
    }
  });

  it("each entry is a non-empty array", () => {
    for (const mod of EXPECTED_MODULES) {
      expect(Array.isArray(JOB_INVALIDATION_MAP[mod])).toBe(true);
      expect(JOB_INVALIDATION_MAP[mod].length).toBeGreaterThan(0);
    }
  });

  it("each nested entry is an array of strings", () => {
    for (const mod of EXPECTED_MODULES) {
      for (const key of JOB_INVALIDATION_MAP[mod]) {
        expect(Array.isArray(key)).toBe(true);
        for (const str of key) {
          expect(typeof str).toBe("string");
          expect(str.length).toBeGreaterThan(0);
        }
      }
    }
  });

  it("brand has brand-settings and brand-sections entries", () => {
    const brandKeys = JOB_INVALIDATION_MAP.brand.map((k) => k[0]);
    expect(brandKeys).toContain("brand-settings");
    expect(brandKeys).toContain("brand-sections");
  });

  it("offer has offer entry", () => {
    const offerKeys = JOB_INVALIDATION_MAP.offer.map((k) => k[0]);
    expect(offerKeys).toContain("offer");
  });

  it("asset has assets entry", () => {
    const assetKeys = JOB_INVALIDATION_MAP.asset.map((k) => k[0]);
    expect(assetKeys).toContain("assets");
  });

  it("persona has personas entry", () => {
    const personaKeys = JOB_INVALIDATION_MAP.persona.map((k) => k[0]);
    expect(personaKeys).toContain("personas");
  });
});
