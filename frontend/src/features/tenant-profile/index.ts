/**
 * Public API for the tenant-profile feature slice.
 * CONTRACT §6.1
 */

// Components
export { BusinessTypeCard } from "./components/BusinessTypeCard";
export { BusinessTypesChipBar } from "./components/BusinessTypesChipBar";
export { BusinessTypesSelector } from "./components/BusinessTypesSelector";
export { ChangeBusinessTypesConfirmDialog } from "./components/ChangeBusinessTypesConfirmDialog";

// Hooks
export { useTenantProfile, TENANT_PROFILE_QUERY_KEY } from "./hooks/use-tenant-profile";
export { useUpdateTenantProfile } from "./hooks/use-update-tenant-profile";
export {
  useBusinessTypesCatalog,
  BUSINESS_TYPES_CATALOG_QUERY_KEY,
} from "./hooks/use-business-types-catalog";

// Utils
export { formatNextAllowed } from "./utils/rate-limit";

// Types
export type {
  ExpertBusinessTypeSlug,
  TenantProfileResponse,
  UpdateTenantProfileRequest,
  BusinessTypeMetadataDTO,
  BusinessTypesCatalogResponse,
  RateLimitedError,
} from "./types/tenant-profile";
export { EXPERT_BUSINESS_TYPE_SLUGS } from "./types/tenant-profile";
