/**
 * Tests for tier-loading.schema.ts
 * TDD: written RED before schema implementation.
 */

import { describe, it, expect } from "vitest";

import { tierResponseSchema } from "../tier-loading.schema";

describe("tierResponseSchema", () => {
  const validTier1 = {
    tier: 1,
    size_hint: "small",
    row_count: 42,
    payload: { kpis: [] },
  };

  it("accepts a valid tier 0 response", () => {
    const result = tierResponseSchema.safeParse({ ...validTier1, tier: 0 });
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.truncated).toBe(false);
    }
  });

  it("accepts a valid tier 1 response with default truncated=false", () => {
    const result = tierResponseSchema.safeParse(validTier1);
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.truncated).toBe(false);
    }
  });

  it("accepts a valid tier 2 response", () => {
    const result = tierResponseSchema.safeParse({ ...validTier1, tier: 2, size_hint: "medium" });
    expect(result.success).toBe(true);
  });

  it("accepts a valid tier 3 response with truncated=true", () => {
    const result = tierResponseSchema.safeParse({
      ...validTier1,
      tier: 3,
      size_hint: "large",
      truncated: true,
      row_count: 15000,
    });
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.truncated).toBe(true);
    }
  });

  it("accepts all valid tier values (0, 1, 2, 3)", () => {
    for (const tier of [0, 1, 2, 3]) {
      const result = tierResponseSchema.safeParse({ ...validTier1, tier });
      expect(result.success, `Expected tier ${tier} to be valid`).toBe(true);
    }
  });

  it("rejects tier value outside 0-3 range", () => {
    const result = tierResponseSchema.safeParse({ ...validTier1, tier: 4 });
    expect(result.success).toBe(false);
  });

  it("rejects invalid size_hint", () => {
    const result = tierResponseSchema.safeParse({ ...validTier1, size_hint: "tiny" });
    expect(result.success).toBe(false);
  });

  it("rejects negative row_count", () => {
    const result = tierResponseSchema.safeParse({ ...validTier1, row_count: -1 });
    expect(result.success).toBe(false);
  });

  it("rejects extra keys (strict mode)", () => {
    const result = tierResponseSchema.safeParse({
      ...validTier1,
      extra_field: "value",
    });
    expect(result.success).toBe(false);
  });

  it("accepts arbitrary payload (unknown type)", () => {
    const result = tierResponseSchema.safeParse({
      ...validTier1,
      payload: { any: "shape", nested: { works: true } },
    });
    expect(result.success).toBe(true);
  });
});
