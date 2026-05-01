/**
 * React Query polling hook: check Telegram link status by token_id.
 *
 * PI-5 PR-1. Refetch interval 3000ms while not linked. Stops auto when
 * `data.linked === true` (saves bandwidth + LLM cost).
 */

import { useQuery } from "@tanstack/react-query";

import { fetchClient } from "@/lib/http-client";

import { LinkStatusResponseSchema, type LinkStatusResponse } from "../types/telegram";

/**
 *
 */
export function useTelegramLinkStatus(tokenId: string | null) {
  return useQuery<LinkStatusResponse>({
    queryKey: ["copilot-telegram-link-status", tokenId],
    enabled: !!tokenId,
    refetchInterval: (query) => (query.state.data?.linked ? false : 3000),
    refetchIntervalInBackground: false,
    queryFn: async () => {
      const res = await fetchClient(`/api/v1/copilot/telegram/link-status?token_id=${tokenId}`);
      if (!res.ok) {
        throw new Error(`Status check failed: ${res.status}`);
      }
      return LinkStatusResponseSchema.parse(await res.json());
    },
  });
}
