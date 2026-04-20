import { describe, it, expect } from "vitest";

import { formatNextAllowed } from "../utils/rate-limit";

describe("formatNextAllowed", () => {
  it("formats a valid ISO date in Spanish", () => {
    const result = formatNextAllowed("2026-05-15T12:00:00Z", "es");
    // Should contain "mayo" and "2026"
    expect(result).toMatch(/mayo/i);
    expect(result).toMatch(/2026/);
  });

  it("includes the day number", () => {
    const result = formatNextAllowed("2026-05-15T12:00:00Z", "es");
    expect(result).toMatch(/15/);
  });

  it("returns the original string for invalid input", () => {
    const bad = "not-a-date";
    expect(formatNextAllowed(bad)).toBe(bad);
  });

  it("handles different locales without crashing", () => {
    const result = formatNextAllowed("2026-01-20T00:00:00Z", "en-US");
    expect(typeof result).toBe("string");
    expect(result.length).toBeGreaterThan(0);
  });

  it("defaults locale to 'es' when omitted", () => {
    const result = formatNextAllowed("2026-03-10T10:00:00Z");
    expect(result).toMatch(/marzo/i);
  });
});
