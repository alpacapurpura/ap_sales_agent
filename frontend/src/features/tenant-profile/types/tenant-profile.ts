/**
 * TypeScript types for the tenant-profile bounded context.
 *
 * Backend SSoT: backend/src/modules/tenant_profile/api/dtos.py
 * CONTRACT §6.1
 */

/**
 * ExpertBusinessType slugs — MUST mirror
 * ``backend/src/shared/domain/expert_business_type.py`` verbatim.
 */
export type ExpertBusinessTypeSlug =
  | "profesional_salud"
  | "consultor_profesional"
  | "coach_mentor"
  | "academia_infoproductor"
  | "anfitrion_productor"
  | "agencia_freelance"
  | "marca_ecommerce"
  | "negocio_local"
  | "software_saas";

export const EXPERT_BUSINESS_TYPE_SLUGS: readonly ExpertBusinessTypeSlug[] = [
  "profesional_salud",
  "consultor_profesional",
  "coach_mentor",
  "academia_infoproductor",
  "anfitrion_productor",
  "agencia_freelance",
  "marca_ecommerce",
  "negocio_local",
  "software_saas",
] as const;

/**
 * Alias mirroring the backend enum name. Prefer this in cross-feature code
 * that reads as a domain concept; ``…Slug`` remains for API contract context.
 */
export type ExpertBusinessType = ExpertBusinessTypeSlug;

/**
 * Response DTO from GET /api/v1/tenant/profile and PATCH /api/v1/tenant/profile.
 */
export interface TenantProfileResponse {
  readonly tenant_id: string;
  readonly business_types: ExpertBusinessTypeSlug[];
  readonly declared_at: string | null;
  readonly updated_at: string;
  readonly is_complete: boolean;
  readonly can_change_now: boolean;
  readonly next_allowed_change_at: string | null;
}

/**
 * Payload for PATCH /api/v1/tenant/profile.
 */
export interface UpdateTenantProfileRequest {
  business_types: ExpertBusinessTypeSlug[];
}

/**
 * Single item from the business-types catalog.
 * Maps to BusinessTypeMetadataDTO on the backend.
 */
export interface BusinessTypeMetadataDTO {
  readonly slug: ExpertBusinessTypeSlug;
  readonly label_es: string;
  readonly description_es: string;
  readonly icon_name: string;
  readonly examples_es: string[];
}

/**
 * Response from GET /api/v1/catalogs/business-types.
 */
export interface BusinessTypesCatalogResponse {
  readonly version: string;
  readonly business_types: BusinessTypeMetadataDTO[];
}

/**
 * Typed error shape returned by the backend on 409 (rate limit).
 * CONTRACT §3.3
 */
export interface RateLimitedError {
  readonly code: "rate_limited";
  readonly next_allowed_change_at: string;
}
