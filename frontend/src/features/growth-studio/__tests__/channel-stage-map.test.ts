import { describe, it, expect } from "vitest";

import {
  getStageForChannel,
  getChannel,
  getChannelSlugs,
  getChannelsForStage,
  CHANNEL_REGISTRY,
} from "../lib/registries/channel-registry";

// ─── getStageForChannel ─────────────────────────────────────────────────────

describe("getStageForChannel", () => {
  it("returns correct stage for meta-ads", () => {
    expect(getStageForChannel("meta-ads")).toBe("atraccion-captura");
  });

  it("returns correct stage for ig-organic", () => {
    expect(getStageForChannel("ig-organic")).toBe("atraccion-captura");
  });

  it("returns correct stage for yt-organic", () => {
    expect(getStageForChannel("yt-organic")).toBe("atraccion-captura");
  });

  it("returns correct stage for website-total", () => {
    expect(getStageForChannel("website-total")).toBe("atraccion-captura");
  });

  it("returns correct stage for email-nurture", () => {
    expect(getStageForChannel("email-nurture")).toBe("nutricion-oportunidad");
  });

  it("falls back to atraccion-captura for unknown channels", () => {
    expect(getStageForChannel("unknown-channel")).toBe("atraccion-captura");
    expect(getStageForChannel("tiktok")).toBe("atraccion-captura");
    expect(getStageForChannel("")).toBe("atraccion-captura");
  });
});

// ─── getChannel ─────────────────────────────────────────────────────────────

describe("getChannel", () => {
  it("returns entry for known slugs", () => {
    expect(getChannel("meta-ads")).toBeDefined();
    expect(getChannel("ig-organic")).toBeDefined();
    expect(getChannel("yt-organic")).toBeDefined();
    expect(getChannel("email-nurture")).toBeDefined();
    expect(getChannel("website-total")).toBeDefined();
  });

  it("returns correct entry shape for meta-ads", () => {
    const entry = getChannel("meta-ads");
    expect(entry?.slug).toBe("meta-ads");
    expect(entry?.stageSlug).toBe("atraccion-captura");
    expect(entry?.name).toBeTruthy();
    expect(entry?.etlProvider).toBeTruthy();
    expect(entry?.color).toMatch(/^#/);
  });
});

// ─── getChannelSlugs ────────────────────────────────────────────────────────

describe("getChannelSlugs", () => {
  it("returns all 5 canonical channel slugs", () => {
    const slugs = getChannelSlugs();
    expect(slugs).toHaveLength(5);
    expect(slugs).toContain("meta-ads");
    expect(slugs).toContain("ig-organic");
    expect(slugs).toContain("yt-organic");
    expect(slugs).toContain("email-nurture");
    expect(slugs).toContain("website-total");
  });
});

// ─── getChannelsForStage ────────────────────────────────────────────────────

describe("getChannelsForStage", () => {
  it("returns 4 channels for atraccion-captura", () => {
    const channels = getChannelsForStage("atraccion-captura");
    expect(channels).toHaveLength(4);
    expect(channels.map((c) => c.slug)).toContain("meta-ads");
    expect(channels.map((c) => c.slug)).toContain("ig-organic");
    expect(channels.map((c) => c.slug)).toContain("yt-organic");
    expect(channels.map((c) => c.slug)).toContain("website-total");
  });

  it("returns 1 channel for nutricion-oportunidad", () => {
    const channels = getChannelsForStage("nutricion-oportunidad");
    expect(channels).toHaveLength(1);
    expect(channels[0].slug).toBe("email-nurture");
  });

  it("returns empty array for stages with no channels", () => {
    expect(getChannelsForStage("ventas")).toHaveLength(0);
    expect(getChannelsForStage("adopcion")).toHaveLength(0);
    expect(getChannelsForStage("expansion-evangelizacion")).toHaveLength(0);
  });
});

// ─── Registry integrity ─────────────────────────────────────────────────────

describe("CHANNEL_REGISTRY integrity", () => {
  it("every entry has required fields", () => {
    for (const entry of CHANNEL_REGISTRY) {
      expect(entry.slug, `${entry.slug} must have slug`).toBeTruthy();
      expect(entry.stageSlug, `${entry.slug} must have stageSlug`).toBeTruthy();
      expect(entry.name, `${entry.slug} must have name`).toBeTruthy();
      expect(entry.etlProvider, `${entry.slug} must have etlProvider`).toBeTruthy();
      expect(entry.color, `${entry.slug} must have color`).toMatch(/^#/);
    }
  });

  it("no duplicate slugs", () => {
    const slugs = CHANNEL_REGISTRY.map((c) => c.slug);
    const unique = new Set(slugs);
    expect(unique.size).toBe(slugs.length);
  });
});
