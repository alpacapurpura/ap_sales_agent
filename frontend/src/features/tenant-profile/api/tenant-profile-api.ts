/**
 * fetchClient wrappers for the tenant-profile API.
 *
 * Endpoints:
 *   GET  /api/v1/tenant/profile                — current profile
 *   PATCH /api/v1/tenant/profile               — update business_types
 *   GET  /api/v1/catalogs/business-types       — enum catalog (near-immutable)
 *
 * CONTRACT §3.1 / §6.1
 */
import { config } from "@/lib/config";
import { fetchClient } from "@/lib/http-client";

import type {
  BusinessTypesCatalogResponse,
  TenantProfileResponse,
  UpdateTenantProfileRequest,
} from "../types/tenant-profile";

const API_URL = config.api.baseUrl;

/**
 * Fetch the current tenant profile.
 * Requires Authorization header (Clerk Bearer token).
 */
export async function getTenantProfile(token: string): Promise<TenantProfileResponse> {
  const res = await fetchClient(`${API_URL}/api/v1/tenant/profile`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch tenant profile: ${res.status} ${res.statusText}`);
  }
  return res.json() as Promise<TenantProfileResponse>;
}

/**
 * Update the tenant's business_types.
 * Returns the updated profile on success.
 * On 409 the raw Response is returned so the caller can extract the error body.
 */
export async function updateTenantProfile(
  token: string,
  payload: UpdateTenantProfileRequest,
): Promise<Response> {
  return fetchClient(`${API_URL}/api/v1/tenant/profile`, {
    method: "PATCH",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
}

/**
 * Fetch the business-types catalog (near-immutable enum metadata).
 * No Authorization header required by contract, but fetchClient still sends
 * X-Tenant-ID for backend consistency — the catalog endpoint ignores it.
 */
export async function getBusinessTypesCatalog(
  token: string,
): Promise<BusinessTypesCatalogResponse> {
  const res = await fetchClient(`${API_URL}/api/v1/catalogs/business-types`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch business-types catalog: ${res.status} ${res.statusText}`);
  }
  return res.json() as Promise<BusinessTypesCatalogResponse>;
}
