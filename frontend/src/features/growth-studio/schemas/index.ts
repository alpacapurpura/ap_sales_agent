/**
 * Growth-studio schemas barrel export.
 *
 * Side-effect import of actions/registry ensures that any consumer
 * of growth-studio schemas also bootstraps the action registry.
 * Mirrors brand-studio/schemas/index.ts pattern.
 */

// Side-effect: bootstraps growth-studio action registry on first import.
import "../actions/registry";

export { channelConfigSchema } from "./channel-config.schema";
export type { ChannelConfig } from "./channel-config.schema";

export {
  kpiSelectionSchema,
  metricCatalogEntrySchema,
  metricCatalogResponseSchema,
} from "./kpi-selection.schema";
export type {
  KpiSelection,
  MetricCatalogEntry,
  MetricCatalogResponse,
} from "./kpi-selection.schema";

export { stageFilterParamsSchema } from "./stage-filter-params.schema";
export type { StageFilterParams } from "./stage-filter-params.schema";

export { tierResponseSchema } from "./tier-loading.schema";
export type { TierResponse } from "./tier-loading.schema";
