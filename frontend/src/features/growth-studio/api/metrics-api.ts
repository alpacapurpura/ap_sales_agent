// Barrel re-export — all existing imports continue to work

import { promoteToEvangelist, createNpsSurvey } from "./crm-actions-api";
import { triggerInitialLoad, getInitialLoadStatus, triggerSyncAll } from "./etl-api";
import {
  getUnmatchedProducts,
  getSourceProducts,
  getProductMappings,
  createProductMapping,
  deleteProductMapping,
  getOfferProductsDetail,
} from "./product-mapping-api";
import { metricsApi as _stageApi } from "./stage-detail-api";

/** Unified API object — backwards-compatible with the previous monolith */
export const metricsApi = {
  ..._stageApi,
  getUnmatchedProducts,
  getSourceProducts,
  getProductMappings,
  createProductMapping,
  deleteProductMapping,
  getOfferProductsDetail,
  triggerInitialLoad,
  getInitialLoadStatus,
  triggerSyncAll,
  promoteToEvangelist,
  createNpsSurvey,
};

// Re-export types so `import type { X } from '.../metrics-api'` keeps working
export type { PeriodType } from "./stage-detail-api";
export type {
  UnmatchedProduct,
  SourceProduct,
  ProductMapping,
  CreateProductMappingResult,
  ProductMetric,
  OfferProductDetail,
} from "./product-mapping-api";
export type { SyncProviderResult, SyncAllResponse } from "./etl-api";
export type { MetricCatalog, MetricCatalogEntry } from "../types/metrics";

// Re-export standalone functions for direct imports
export {
  getUnmatchedProducts,
  getSourceProducts,
  getProductMappings,
  createProductMapping,
  deleteProductMapping,
  getOfferProductsDetail,
} from "./product-mapping-api";
export { triggerInitialLoad, getInitialLoadStatus, triggerSyncAll } from "./etl-api";
export { promoteToEvangelist, createNpsSurvey } from "./crm-actions-api";
