import { describe, it, expect } from "vitest";

import { formatMetricValue } from "../format-metric-value";

describe("formatMetricValue", () => {
  describe("count (default unit)", () => {
    it("formats small numbers with locale", () => {
      expect(formatMetricValue(42, "count")).toBe("42");
      expect(formatMetricValue(999, "count")).toBe("999");
    });

    it("formats thousands with k suffix", () => {
      expect(formatMetricValue(1500, "count")).toBe("1.5k");
      expect(formatMetricValue(9999, "count")).toBe("10.0k");
    });

    it("formats large thousands without decimal", () => {
      expect(formatMetricValue(15000, "count")).toBe("15k");
      expect(formatMetricValue(99999, "count")).toBe("100k");
    });

    it("formats millions with M suffix", () => {
      expect(formatMetricValue(1500000, "count")).toBe("1.5M");
      expect(formatMetricValue(10000000, "count")).toBe("10.0M");
    });

    it("handles zero", () => {
      expect(formatMetricValue(0, "count")).toBe("0");
    });

    it("handles negative values", () => {
      expect(formatMetricValue(-1500, "count")).toBe("-1.5k");
    });
  });

  describe("percentage", () => {
    it("formats with 2 decimals by default", () => {
      expect(formatMetricValue(45.678, "percentage")).toBe("45.68%");
    });

    it("respects custom percentDecimals", () => {
      expect(formatMetricValue(45.678, "percentage", { percentDecimals: 1 })).toBe("45.7%");
      expect(formatMetricValue(45.678, "percentage", { percentDecimals: 0 })).toBe("46%");
    });

    it("handles zero", () => {
      expect(formatMetricValue(0, "percentage")).toBe("0.00%");
    });
  });

  describe("currency", () => {
    it("formats with USD by default", () => {
      const result = formatMetricValue(1234.56, "currency");
      expect(result).toContain("1,234");
    });

    it("returns -- for zero", () => {
      expect(formatMetricValue(0, "currency")).toBe("--");
    });

    it("respects custom currency", () => {
      const result = formatMetricValue(100, "currency", { currency: "EUR" });
      expect(result).toContain("100");
    });
  });

  describe("ratio", () => {
    it("formats with 2 decimals and x suffix", () => {
      expect(formatMetricValue(3.456, "ratio")).toBe("3.46x");
    });

    it("handles zero", () => {
      expect(formatMetricValue(0, "ratio")).toBe("0.00x");
    });
  });
});
