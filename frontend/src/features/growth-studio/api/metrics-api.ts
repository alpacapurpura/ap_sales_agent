// Barrel re-export — all existing imports continue to work

import { metricsApi as _stageApi } from './stage-detail-api';
import { getUnmatchedProducts, getSourceProducts, getProductMappings, createProductMapping, deleteProductMapping } from './product-mapping-api';
import { triggerInitialLoad, getInitialLoadStatus } from './etl-api';
import { promoteToEvangelist, createNpsSurvey } from './crm-actions-api';

/** Unified API object — backwards-compatible with the previous monolith */
export const metricsApi = {
  ..._stageApi,
  getUnmatchedProducts,
  getSourceProducts,
  getProductMappings,
  createProductMapping,
  deleteProductMapping,
  triggerInitialLoad,
  getInitialLoadStatus,
  promoteToEvangelist,
  createNpsSurvey,
};

// Re-export types so `import type { X } from '.../metrics-api'` keeps working
export type { UnmatchedProduct, SourceProduct, ProductMapping, CreateProductMappingResult } from './product-mapping-api';

// Re-export standalone functions for direct imports
export { getUnmatchedProducts, getSourceProducts, getProductMappings, createProductMapping, deleteProductMapping } from './product-mapping-api';
export { triggerInitialLoad, getInitialLoadStatus } from './etl-api';
export { promoteToEvangelist, createNpsSurvey } from './crm-actions-api';
