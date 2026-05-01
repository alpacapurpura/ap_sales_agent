"use client";

import { useQuery } from "@tanstack/react-query";

import { fetchClient } from "@/lib/http-client";

import type { ContactDetail } from "../types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "";

/**
 * Fetches full contact detail from /api/v1/contacts/{contactId}.
 * Only runs when contactId is non-null.
 * fetchClient auto-injects X-Tenant-ID header.
 */
export function useContactDetailQuery(contactId: string | null) {
  return useQuery<ContactDetail, Error>({
    queryKey: ["crm", "contact-detail", contactId],
    queryFn: async () => {
      const res = await fetchClient(`${API_URL}/api/v1/contacts/${contactId}`);
      if (!res.ok) throw new Error(`Error al cargar contacto ${contactId}: ${res.status}`);
      return res.json() as Promise<ContactDetail>;
    },
    enabled: !!contactId,
    staleTime: 60_000,
  });
}
