"use client";

import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";

import { authorityApi, type AuthorityItem } from "@/lib/api/authority-item";

/**
 * Single-authority-item query keyed by (tenant_id, item_id).
 */
export function useAuthorityItem(itemId: string | null | undefined) {
  const { getToken } = useAuth();
  const params = useParams<{ tenantId: string }>();
  const tenantId = params?.tenantId ?? "";

  return useQuery<AuthorityItem | null>({
    queryKey: ["authority_item", tenantId, itemId],
    enabled: Boolean(itemId),
    queryFn: async () => {
      const token = await getToken();
      if (!token || !itemId) return null;
      return authorityApi.get(token, itemId);
    },
    retry: (failureCount, err: Error) => {
      if (err.message.includes("401") || err.message.includes("404")) return false;
      return failureCount < 2;
    },
  });
}
