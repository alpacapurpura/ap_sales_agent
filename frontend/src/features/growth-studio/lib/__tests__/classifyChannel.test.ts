import { describe, it, expect } from "vitest";

import { classifyChannel } from "../classifyChannel";

describe("classifyChannel", () => {
  it('returns "disconnected" when channel is not connected', () => {
    expect(
      classifyChannel({
        connected: false,
        slug: "meta-ads",
        metrics: [],
      }),
    ).toBe("disconnected");
  });

  it('returns "disconnected" even if channel has metrics but is not connected', () => {
    expect(
      classifyChannel({
        connected: false,
        slug: "ig-organic",
        metrics: [{ value: 100 }],
      }),
    ).toBe("disconnected");
  });

  it('returns "proximamente" for ai-sdr with no metrics', () => {
    expect(
      classifyChannel({
        connected: true,
        slug: "ai-sdr",
        metrics: [],
      }),
    ).toBe("proximamente");
  });

  it('returns "proximamente" for ai-sdr with all-zero metrics', () => {
    expect(
      classifyChannel({
        connected: true,
        slug: "ai-sdr",
        metrics: [{ value: 0 }],
      }),
    ).toBe("proximamente");
  });

  it('returns "active" for ai-sdr with non-zero metrics', () => {
    expect(
      classifyChannel({
        connected: true,
        slug: "ai-sdr",
        metrics: [{ value: 5 }],
      }),
    ).toBe("active");
  });

  it('returns "proximamente" for checkout-lp regardless of metrics', () => {
    expect(
      classifyChannel({
        connected: true,
        slug: "checkout-lp",
        metrics: [{ value: 100 }],
      }),
    ).toBe("proximamente");
  });

  it('returns "proximamente" for link-enviado with no metrics', () => {
    expect(
      classifyChannel({
        connected: true,
        slug: "link-enviado",
        metrics: [],
      }),
    ).toBe("proximamente");
  });

  it('returns "active" for link-enviado with non-zero metrics', () => {
    expect(
      classifyChannel({
        connected: true,
        slug: "link-enviado",
        metrics: [{ value: 10 }],
      }),
    ).toBe("active");
  });

  it('returns "no-data" for connected channel with empty metrics', () => {
    expect(
      classifyChannel({
        connected: true,
        slug: "ga4-search",
        metrics: [],
      }),
    ).toBe("no-data");
  });

  it('returns "no-data" for connected channel with all-zero metrics', () => {
    expect(
      classifyChannel({
        connected: true,
        slug: "ig-organic",
        metrics: [{ value: 0 }, { value: 0 }],
      }),
    ).toBe("no-data");
  });

  it('returns "active" for connected channel with non-zero metrics', () => {
    expect(
      classifyChannel({
        connected: true,
        slug: "ig-organic",
        metrics: [{ value: 500 }, { value: 0 }],
      }),
    ).toBe("active");
  });

  it('returns "active" for connected channel with single non-zero metric', () => {
    expect(
      classifyChannel({
        connected: true,
        slug: "meta-ads",
        metrics: [{ value: 1 }],
      }),
    ).toBe("active");
  });
});
