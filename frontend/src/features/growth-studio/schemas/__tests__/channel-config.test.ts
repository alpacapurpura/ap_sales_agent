/**
 * Tests for channel-config.schema.ts
 * TDD: written RED before schema implementation.
 */

import { describe, it, expect } from "vitest";

import { channelConfigSchema } from "../channel-config.schema";

describe("channelConfigSchema", () => {
  const validConfig = {
    slug: "meta-ads",
    dashboard: "meta-ads-dashboard",
    kpis: ["impressions", "clicks"],
    color: "#1877F2",
  };

  it("accepts a valid channel config with defaults", () => {
    const result = channelConfigSchema.safeParse(validConfig);
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.etl_rate_limit_per_hour).toBe(3);
    }
  });

  it("accepts a custom etl_rate_limit_per_hour", () => {
    const result = channelConfigSchema.safeParse({
      ...validConfig,
      etl_rate_limit_per_hour: 5,
    });
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.etl_rate_limit_per_hour).toBe(5);
    }
  });

  it("accepts all valid channel slugs", () => {
    const validChannels = [
      "meta-ads",
      "yt-organic",
      "email-nurture",
      "ig-organic",
      "website-total",
    ];
    for (const slug of validChannels) {
      const result = channelConfigSchema.safeParse({ ...validConfig, slug });
      expect(result.success, `Expected slug ${slug} to be valid`).toBe(true);
    }
  });

  it("rejects invalid hex color — missing #", () => {
    const result = channelConfigSchema.safeParse({
      ...validConfig,
      color: "1877F2",
    });
    expect(result.success).toBe(false);
  });

  it("rejects invalid hex color — too short", () => {
    const result = channelConfigSchema.safeParse({
      ...validConfig,
      color: "#FFF",
    });
    expect(result.success).toBe(false);
  });

  it("rejects invalid hex color — non-hex chars", () => {
    const result = channelConfigSchema.safeParse({
      ...validConfig,
      color: "#ZZZZZZ",
    });
    expect(result.success).toBe(false);
  });

  it("rejects unknown channel slug", () => {
    const result = channelConfigSchema.safeParse({
      ...validConfig,
      slug: "twitter-ads",
    });
    expect(result.success).toBe(false);
  });

  it("rejects empty kpis array", () => {
    const result = channelConfigSchema.safeParse({
      ...validConfig,
      kpis: [],
    });
    expect(result.success).toBe(false);
  });

  it("rejects extra keys (strict mode)", () => {
    const result = channelConfigSchema.safeParse({
      ...validConfig,
      unknown_field: "value",
    });
    expect(result.success).toBe(false);
  });

  it("rejects etl_rate_limit_per_hour out of range", () => {
    expect(
      channelConfigSchema.safeParse({ ...validConfig, etl_rate_limit_per_hour: 0 }).success,
    ).toBe(false);
    expect(
      channelConfigSchema.safeParse({ ...validConfig, etl_rate_limit_per_hour: 21 }).success,
    ).toBe(false);
  });

  it("rejects invalid dashboard slug pattern", () => {
    const result = channelConfigSchema.safeParse({
      ...validConfig,
      dashboard: "Dashboard With Spaces",
    });
    expect(result.success).toBe(false);
  });
});
