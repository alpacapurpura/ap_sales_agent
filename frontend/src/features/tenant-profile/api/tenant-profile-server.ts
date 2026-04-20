/**
 * Server-only utility for fetching the tenant profile from Server Components.
 *
 * Used by the dashboard layout to gate access until the profile is complete.
 * CONTRACT §6.4
 */
import { auth } from "@clerk/nextjs/server";

import { config } from "@/lib/config";

import type { TenantProfileResponse } from "../types/tenant-profile";

const API_URL =
  typeof window === "undefined" && process.env.INTERNAL_API_URL
    ? process.env.INTERNAL_API_URL
    : config.api.baseUrl;

/**
 * Fetches the tenant profile server-side using the Clerk session token.
 * Returns null when not authenticated or on any non-2xx response so the
 * gating layout can fail open (let the route render) instead of crashing.
 */
export async function fetchTenantProfileServer(
  tenantId: string,
): Promise<TenantProfileResponse | null> {
  try {
    const { getToken } = await auth();
    const token = await getToken();
    if (!token) return null;

    const res = await fetch(`${API_URL}/api/v1/tenant/profile`, {
      headers: {
        Authorization: `Bearer ${token}`,
        "X-Tenant-ID": tenantId,
      },
      cache: "no-store",
    });

    if (!res.ok) return null;
    return res.json() as Promise<TenantProfileResponse>;
  } catch {
    return null;
  }
}
