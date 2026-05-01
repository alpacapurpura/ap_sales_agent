/**
 * React Query mutation: soft-delete current Telegram link.
 *
 * PI-5 PR-1. Backend DELETE /api/v1/copilot/telegram/link.
 * Invalidates `copilot-telegram-current-link` on success.
 */

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { fetchClient } from "@/lib/http-client";

import { UnlinkResponseSchema, type UnlinkResponse } from "../types/telegram";

/**
 *
 */
export function useUnlinkTelegram() {
  const qc = useQueryClient();
  return useMutation<UnlinkResponse, Error>({
    mutationFn: async () => {
      const res = await fetchClient("/api/v1/copilot/telegram/link", {
        method: "DELETE",
      });
      if (!res.ok) {
        throw new Error(`Failed to unlink: ${res.status}`);
      }
      return UnlinkResponseSchema.parse(await res.json());
    },
    onSuccess: async () => {
      await qc.invalidateQueries({
        queryKey: ["copilot-telegram-current-link"],
      });
    },
  });
}
