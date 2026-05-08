/**
 * Tests for kpi-selection.schema.ts
 * TDD: written RED before schema implementation.
 */

import { describe, it, expect } from "vitest";

import {
  kpiSelectionSchema,
  metricCatalogEntrySchema,
  metricCatalogResponseSchema,
} from "../kpi-selection.schema";

describe("kpiSelectionSchema", () => {
  it("accepts valid KPI selection with 1 item", () => {
    const result = kpiSelectionSchema.safeParse({ selected_kpis: ["impressions"] });
    expect(result.success).toBe(true);
  });

  it("accepts valid KPI selection with multiple items", () => {
    const result = kpiSelectionSchema.safeParse({
      selected_kpis: ["impressions", "clicks", "ctr", "spend"],
    });
    expect(result.success).toBe(true);
  });

  it("accepts exactly 10 KPIs (max)", () => {
    const result = kpiSelectionSchema.safeParse({
      selected_kpis: ["k1", "k2", "k3", "k4", "k5", "k6", "k7", "k8", "k9", "k10"],
    });
    expect(result.success).toBe(true);
  });

  it("rejects 0 KPIs (min 1)", () => {
    const result = kpiSelectionSchema.safeParse({ selected_kpis: [] });
    expect(result.success).toBe(false);
  });

  it("rejects more than 10 KPIs", () => {
    const result = kpiSelectionSchema.safeParse({
      selected_kpis: ["k1", "k2", "k3", "k4", "k5", "k6", "k7", "k8", "k9", "k10", "k11"],
    });
    expect(result.success).toBe(false);
  });

  it("rejects extra keys (strict mode)", () => {
    const result = kpiSelectionSchema.safeParse({
      selected_kpis: ["impressions"],
      extra_field: "value",
    });
    expect(result.success).toBe(false);
  });
});

describe("metricCatalogEntrySchema", () => {
  const validEntry = {
    name: "impressions",
    display_name: "Impresiones",
    unit: "count",
    aggregation: "additive",
    is_unique_metric: false,
    higher_is_better: true,
    providers: ["meta_ads"],
  };

  it("accepts a valid metric catalog entry", () => {
    const result = metricCatalogEntrySchema.safeParse(validEntry);
    expect(result.success).toBe(true);
  });

  it("accepts all valid unit types", () => {
    const units = ["count", "currency", "percentage", "ratio", "seconds", "json"];
    for (const unit of units) {
      const result = metricCatalogEntrySchema.safeParse({ ...validEntry, unit });
      expect(result.success, `Expected unit ${unit} to be valid`).toBe(true);
    }
  });

  it("accepts all valid aggregation types", () => {
    const aggregations = ["additive", "weighted_average", "derived", "non_aggregable", "snapshot"];
    for (const aggregation of aggregations) {
      const result = metricCatalogEntrySchema.safeParse({ ...validEntry, aggregation });
      expect(result.success, `Expected aggregation ${aggregation} to be valid`).toBe(true);
    }
  });

  it("rejects invalid unit", () => {
    const result = metricCatalogEntrySchema.safeParse({ ...validEntry, unit: "invalid_unit" });
    expect(result.success).toBe(false);
  });

  it("rejects invalid aggregation", () => {
    const result = metricCatalogEntrySchema.safeParse({ ...validEntry, aggregation: "sum" });
    expect(result.success).toBe(false);
  });
});

describe("metricCatalogResponseSchema", () => {
  it("accepts a valid catalog response", () => {
    const result = metricCatalogResponseSchema.safeParse({
      metrics: [],
      count: 0,
    });
    expect(result.success).toBe(true);
  });

  it("accepts a catalog response with entries", () => {
    const result = metricCatalogResponseSchema.safeParse({
      metrics: [
        {
          name: "impressions",
          display_name: "Impresiones",
          unit: "count",
          aggregation: "additive",
          is_unique_metric: false,
          higher_is_better: true,
          providers: ["meta_ads"],
        },
      ],
      count: 1,
    });
    expect(result.success).toBe(true);
  });
});
