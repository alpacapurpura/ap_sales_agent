"use client";

import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";

import { useIsMounted } from "@/hooks/use-is-mounted";
import { fetchClient } from "@/lib/http-client";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "";

export interface FilterFieldMeta {
  name: string;
  type: "enum_list" | "int_range" | "bool" | "datetime" | "string";
  enum_values: string[] | null;
  description: string | null;
}

export interface FilterSchemaResponse {
  version: string;
  fields: FilterFieldMeta[];
}

/**
 * Fetches the filter schema metadata from /api/v1/contacts/_filter-schema.
 * Used by FE to build filter UI dynamically (PI-3 expansion).
 *
 * Auth pattern (homologated with offer-studio/use-assets.ts): see
 * use-contacts-query.ts for the rationale behind the `enabled` gate
 * and the no-token guard.
 *
 * staleTime: Infinity because metadata is stable.
 * fetchClient auto-injects X-Tenant-ID.
 */
export function useFilterSchemaQuery() {
  const isMounted = useIsMounted();
  const { getToken, isLoaded, isSignedIn } = useAuth();
  return useQuery<FilterSchemaResponse, Error>({
    queryKey: ["crm", "contacts", "filter-schema"],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("No autenticado");
      const res = await fetchClient(`${API_URL}/api/v1/contacts/_filter-schema`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error(`Error al cargar esquema de filtros: ${res.status}`);
      return res.json() as Promise<FilterSchemaResponse>;
    },
    enabled: isMounted && isLoaded && isSignedIn,
    staleTime: Infinity, // metadata estable
  });
}
