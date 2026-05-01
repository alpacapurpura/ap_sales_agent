/**
 * React Query mutation: generate magic link token for Telegram binding.
 *
 * PI-5 PR-1. Backend POST /api/v1/copilot/telegram/link-tokens.
 */

import { useMutation } from "@tanstack/react-query";

import { fetchClient } from "@/lib/http-client";

import { LinkTokenResponseSchema, type LinkTokenResponse } from "../types/telegram";

/**
 *
 */
export function useCreateTelegramLinkToken() {
  return useMutation<LinkTokenResponse, Error>({
    mutationFn: async () => {
      const res = await fetchClient("/api/v1/copilot/telegram/link-tokens", {
        method: "POST",
        body: JSON.stringify({}),
      });
      if (!res.ok) {
        throw new Error(`Failed to create link token: ${res.status}`);
      }
      const json: unknown = await res.json();
      return LinkTokenResponseSchema.parse(json);
    },
  });
}
