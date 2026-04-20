import { describe, it, expect } from "vitest";

import { buildEditionSwitchHref, currentOfferTabSegment } from "../edition-route";

const BASE = "/acme/offer-studio/offer/offer-1";

describe("currentOfferTabSegment", () => {
  it("returns null for the offer root (Info)", () => {
    expect(currentOfferTabSegment(BASE, BASE)).toBeNull();
  });

  it("returns null for the edition default (no tab leaf)", () => {
    expect(currentOfferTabSegment(`${BASE}/editions/ed-1`, BASE)).toBeNull();
  });

  it("returns the offer-level tab segment", () => {
    expect(currentOfferTabSegment(`${BASE}/ventas`, BASE)).toBe("ventas");
    expect(currentOfferTabSegment(`${BASE}/assets`, BASE)).toBe("assets");
    expect(currentOfferTabSegment(`${BASE}/campaigns`, BASE)).toBe("campaigns");
    expect(currentOfferTabSegment(`${BASE}/landing`, BASE)).toBe("landing");
  });

  it("returns the per-edition tab segment", () => {
    expect(currentOfferTabSegment(`${BASE}/editions/ed-1/ventas`, BASE)).toBe("ventas");
    expect(currentOfferTabSegment(`${BASE}/editions/ed-1/assets`, BASE)).toBe("assets");
    expect(currentOfferTabSegment(`${BASE}/editions/ed-1/campaigns`, BASE)).toBe("campaigns");
    expect(currentOfferTabSegment(`${BASE}/editions/ed-1/landing`, BASE)).toBe("landing");
  });

  it("returns null for unknown suffixes", () => {
    expect(currentOfferTabSegment(`${BASE}/random`, BASE)).toBeNull();
    expect(currentOfferTabSegment(`${BASE}/editions/ed-1/whatever`, BASE)).toBeNull();
  });

  it("returns null when pathname does not match the base", () => {
    expect(currentOfferTabSegment("/other/tenant/offer-studio/offer/x", BASE)).toBeNull();
    expect(currentOfferTabSegment(null, BASE)).toBeNull();
    expect(currentOfferTabSegment(undefined, BASE)).toBeNull();
  });
});

describe("buildEditionSwitchHref", () => {
  it("builds the edition default when on Info", () => {
    expect(buildEditionSwitchHref(BASE, BASE, "ed-2")).toBe(`${BASE}/editions/ed-2`);
  });

  it("preserves the current tab when on a per-edition tab", () => {
    expect(buildEditionSwitchHref(`${BASE}/editions/ed-1/ventas`, BASE, "ed-2")).toBe(
      `${BASE}/editions/ed-2/ventas`,
    );
  });

  it("preserves the current tab when on an offer-level tab", () => {
    expect(buildEditionSwitchHref(`${BASE}/assets`, BASE, "ed-2")).toBe(
      `${BASE}/editions/ed-2/assets`,
    );
  });

  it("falls back to the edition default on unknown paths", () => {
    expect(buildEditionSwitchHref(`${BASE}/foo/bar`, BASE, "ed-2")).toBe(`${BASE}/editions/ed-2`);
  });
});
