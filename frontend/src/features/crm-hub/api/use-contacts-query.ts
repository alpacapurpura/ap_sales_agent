"use client";

import { useQuery } from "@tanstack/react-query";

import { fetchClient } from "@/lib/http-client";

import type { ContactListItem, ContactFilterParams, PaginatedResponse } from "../types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "";

export interface UseContactsQueryParams {
  filters: ContactFilterParams;
  limit: number;
  offset: number;
}

/**
 * Fetches the paginated list of contacts from /api/v1/contacts.
 * fetchClient auto-injects X-Tenant-ID header.
 */
export function useContactsQuery(params: UseContactsQueryParams) {
  return useQuery<PaginatedResponse<ContactListItem>, Error>({
    queryKey: ["crm", "contacts", params],
    queryFn: async () => {
      const search = buildSearchParams(params);
      const res = await fetchClient(`${API_URL}/api/v1/contacts/?${search.toString()}`);
      if (!res.ok) throw new Error(`Error al cargar contactos: ${res.status}`);
      return res.json() as Promise<PaginatedResponse<ContactListItem>>;
    },
    staleTime: 30_000,
    placeholderData: (prev) => prev, // pagination smooth UX
  });
}

function buildSearchParams(p: UseContactsQueryParams): URLSearchParams {
  const sp = new URLSearchParams();
  sp.set("limit", String(p.limit));
  sp.set("offset", String(p.offset));
  for (const [k, v] of Object.entries(p.filters)) {
    if (v === undefined || v === null) continue;
    if (Array.isArray(v)) {
      if (v.length > 0) sp.set(k, v.join(","));
    } else {
      sp.set(k, String(v));
    }
  }
  return sp;
}
