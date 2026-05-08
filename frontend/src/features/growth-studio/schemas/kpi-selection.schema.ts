/**
 * KPI selection schema — validates /api/v1/analytics/metrics/catalog responses
 * and user KPI selection.
 *
 * NO FE-side mirror constants — catalog is fetched at runtime via React Query.
 * Uses .strict() to mirror Pydantic ConfigDict(extra="forbid").
 */
import { z } from "zod";

// ─── Metric catalog entry schema ──────────────────────────────────────────────

/**
 * Single metric catalog entry. Mirrors BE MetricCatalogEntry DTO.
 */
export const metricCatalogEntrySchema = z.object({
  name: z.string(),
  display_name: z.string(),
  unit: z.enum(["count", "currency", "percentage", "ratio", "seconds", "json"]),
  aggregation: z.enum(["additive", "weighted_average", "derived", "non_aggregable", "snapshot"]),
  is_unique_metric: z.boolean(),
  higher_is_better: z.boolean(),
  providers: z.array(z.string()),
});

/**
 * Full catalog response from GET /api/v1/analytics/metrics/catalog.
 */
export const metricCatalogResponseSchema = z.object({
  metrics: z.array(metricCatalogEntrySchema),
  count: z.number().int().min(0),
});

// ─── KPI selection schema ─────────────────────────────────────────────────────

/**
 * User KPI selection (custom dashboard).
 * Min 1 / Max 10 KPIs per selection. .strict() rejects extra keys.
 */
export const kpiSelectionSchema = z
  .object({
    selected_kpis: z
      .array(z.string())
      .min(1, "Selecciona al menos un KPI")
      .max(10, "Máximo 10 KPIs por selección"),
  })
  .strict(); // mirrors Pydantic extra="forbid"

export type MetricCatalogEntry = z.infer<typeof metricCatalogEntrySchema>;
export type MetricCatalogResponse = z.infer<typeof metricCatalogResponseSchema>;
export type KpiSelection = z.infer<typeof kpiSelectionSchema>;
