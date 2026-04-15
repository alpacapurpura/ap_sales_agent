import { describe, it, expect } from "vitest";

import { providerToConnectionRoute } from "../providerToConnectionRoute";

describe("providerToConnectionRoute", () => {
  it('maps "meta" to "meta"', () => {
    expect(providerToConnectionRoute("meta")).toBe("meta");
  });

  it('maps "google_analytics" to "google-analytics"', () => {
    expect(providerToConnectionRoute("google_analytics")).toBe("google-analytics");
  });

  it('maps "google_ads" to "google-analytics"', () => {
    expect(providerToConnectionRoute("google_ads")).toBe("google-analytics");
  });

  it('maps "youtube" to "youtube"', () => {
    expect(providerToConnectionRoute("youtube")).toBe("youtube");
  });

  it('maps "shopify" to "shopify"', () => {
    expect(providerToConnectionRoute("shopify")).toBe("shopify");
  });

  it('maps "email_marketing" to "mailerlite"', () => {
    expect(providerToConnectionRoute("email_marketing")).toBe("mailerlite");
  });

  it('maps "manychat" to "manychat"', () => {
    expect(providerToConnectionRoute("manychat")).toBe("manychat");
  });

  it('maps "telegram" to "telegram"', () => {
    expect(providerToConnectionRoute("telegram")).toBe("telegram");
  });

  it('maps "search_console" to "google-analytics"', () => {
    expect(providerToConnectionRoute("search_console")).toBe("google-analytics");
  });

  it('returns null for "internal"', () => {
    expect(providerToConnectionRoute("internal")).toBeNull();
  });

  it('returns null for "manual"', () => {
    expect(providerToConnectionRoute("manual")).toBeNull();
  });

  it("returns null for undefined", () => {
    expect(providerToConnectionRoute(undefined)).toBeNull();
  });

  it("returns null for unknown provider", () => {
    expect(providerToConnectionRoute("unknown_provider")).toBeNull();
  });
});
