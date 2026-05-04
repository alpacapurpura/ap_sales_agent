"use client";

import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";

import { useIsMounted } from "@/hooks/use-is-mounted";
import { fetchClient } from "@/lib/http-client";

import type { ContactListItem, ContactFilterParams, PaginatedResponse } from "../types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "";

export interface UseContactsQueryParams {
  filters: ContactFilterParams;
  limit: number;
  offset: number;
}

/**
 * Fetches the paginated list of contacts from /api/v1/contacts/.
 *
 * Auth + hydration pattern:
 *   - `useIsMounted` keeps `enabled=false` on the server and on the first
 *     client paint, so React Query's optimistic `fetchStatus='fetching'`
 *     flag (which only appears once `enabled=true`) cannot diverge between
 *     SSR and CSR. Without this gate, the DataTable renders the empty
 *     state on the server and the loading skeleton on the first client
 *     render, producing a hydration mismatch.
 *   - `isLoaded && isSignedIn` waits for Clerk to bootstrap, so the query
 *     never fires with `Bearer null` (which BE answers 401, which
 *     fetchClient turns into a hard redirect to /sign-in).
 *   - `queryFn` throws if Clerk returns no token rather than sending the
 *     literal string "null" as the bearer.
 *
 * fetchClient auto-injects X-Tenant-ID.
 */
export function useContactsQuery(params: UseContactsQueryParams) {
  const isMounted = useIsMounted();
  const { getToken, isLoaded, isSignedIn } = useAuth();
  return useQuery<PaginatedResponse<ContactListItem>, Error>({
    queryKey: ["crm", "contacts", params],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("No autenticado");
      const search = buildSearchParams(params);
      const res = await fetchClient(`${API_URL}/api/v1/contacts/?${search.toString()}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error(`Error al cargar contactos: ${res.status}`);
      return res.json() as Promise<PaginatedResponse<ContactListItem>>;
    },
    enabled: isMounted && isLoaded && isSignedIn,
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
