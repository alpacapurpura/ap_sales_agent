/**
 * Tests for stage-filter-params.schema.ts
 * TDD: written RED before schema implementation.
 */

import { describe, it, expect } from "vitest";

import { stageFilterParamsSchema } from "../stage-filter-params.schema";

describe("stageFilterParamsSchema", () => {
  it("accepts a valid stage with default period", () => {
    const result = stageFilterParamsSchema.safeParse({ stage: "atraccion-captura" });
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.period).toBe("30d");
      expect(result.data.channel).toBeUndefined();
    }
  });

  it("accepts a valid stage + channel + period combination", () => {
    const result = stageFilterParamsSchema.safeParse({
      stage: "ventas",
      channel: "meta-ads",
      period: "7d",
    });
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.stage).toBe("ventas");
      expect(result.data.channel).toBe("meta-ads");
      expect(result.data.period).toBe("7d");
    }
  });

  it("accepts all valid stage slugs", () => {
    const validSlugs = [
      "atraccion-captura",
      "nutricion-oportunidad",
      "ventas",
      "adopcion",
      "expansion-evangelizacion",
    ];
    for (const slug of validSlugs) {
      const result = stageFilterParamsSchema.safeParse({ stage: slug });
      expect(result.success, `Expected ${slug} to be valid`).toBe(true);
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
    for (const channel of validChannels) {
      const result = stageFilterParamsSchema.safeParse({
        stage: "atraccion-captura",
        channel,
      });
      expect(result.success, `Expected channel ${channel} to be valid`).toBe(true);
    }
  });

  it("accepts all valid period values", () => {
    for (const period of ["7d", "30d", "90d"]) {
      const result = stageFilterParamsSchema.safeParse({ stage: "adopcion", period });
      expect(result.success, `Expected period ${period} to be valid`).toBe(true);
    }
  });

  it("rejects an invalid stage slug", () => {
    const result = stageFilterParamsSchema.safeParse({ stage: "unknown-stage" });
    expect(result.success).toBe(false);
  });

  it("rejects an invalid channel slug", () => {
    const result = stageFilterParamsSchema.safeParse({
      stage: "ventas",
      channel: "twitter-ads",
    });
    expect(result.success).toBe(false);
  });

  it("rejects an invalid period", () => {
    const result = stageFilterParamsSchema.safeParse({
      stage: "ventas",
      period: "180d",
    });
    expect(result.success).toBe(false);
  });

  it("rejects extra keys (strict mode — mirrors Pydantic extra='forbid')", () => {
    const result = stageFilterParamsSchema.safeParse({
      stage: "adopcion",
      tenant_id: "some-uuid",
    });
    expect(result.success).toBe(false);
  });

  it("requires the stage field", () => {
    const result = stageFilterParamsSchema.safeParse({ period: "7d" });
    expect(result.success).toBe(false);
  });
});
