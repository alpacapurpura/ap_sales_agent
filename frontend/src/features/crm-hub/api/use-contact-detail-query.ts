"use client";

import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";

import { useIsMounted } from "@/hooks/use-is-mounted";
import { fetchClient } from "@/lib/http-client";

import type { ContactDetail } from "../types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "";

/**
 * Fetches full contact detail from /api/v1/contacts/{contactId}.
 *
 * Auth pattern (homologated with offer-studio/use-assets.ts): see
 * use-contacts-query.ts for the rationale behind the `enabled` gate
 * and the no-token guard.
 *
 * fetchClient auto-injects X-Tenant-ID.
 */
export function useContactDetailQuery(contactId: string | null) {
  const isMounted = useIsMounted();
  const { getToken, isLoaded, isSignedIn } = useAuth();
  return useQuery<ContactDetail, Error>({
    queryKey: ["crm", "contact-detail", contactId],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("No autenticado");
      const res = await fetchClient(`${API_URL}/api/v1/contacts/${contactId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error(`Error al cargar contacto ${contactId}: ${res.status}`);
      return res.json() as Promise<ContactDetail>;
    },
    enabled: isMounted && isLoaded && isSignedIn && !!contactId,
    staleTime: 60_000,
  });
}
