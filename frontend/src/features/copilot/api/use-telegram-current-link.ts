/**
 * React Query: fetch current Telegram link state for authenticated user.
 *
 * PI-5 PR-1. Same endpoint as link-status but WITHOUT token_id query
 * param — returns latest non-revoked link if any.
 */

import { useQuery } from "@tanstack/react-query";

import { fetchClient } from "@/lib/http-client";

import { LinkStatusResponseSchema, type LinkStatusResponse } from "../types/telegram";

/**
 *
 */
export function useTelegramCurrentLink() {
  return useQuery<LinkStatusResponse>({
    queryKey: ["copilot-telegram-current-link"],
    queryFn: async () => {
      const res = await fetchClient("/api/v1/copilot/telegram/link-status");
      if (!res.ok) {
        throw new Error(`Current link fetch failed: ${res.status}`);
      }
      return LinkStatusResponseSchema.parse(await res.json());
    },
    staleTime: 30_000,
  });
}
