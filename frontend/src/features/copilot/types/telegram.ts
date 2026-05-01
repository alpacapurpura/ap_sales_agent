/**
 * Zod schemas for Copilot Telegram channel API responses.
 *
 * PI-5 PR-1. Mirrors backend `copilot/api/telegram_dto.py` (Pydantic v2).
 * Zod parses runtime + infers TS types — single source of truth FE.
 */

import { z } from "zod";

export const LinkTokenResponseSchema = z.object({
  token_id: z.string().uuid(),
  deep_link_url: z.string().url(),
  expires_at: z.string().datetime(),
});
export type LinkTokenResponse = z.infer<typeof LinkTokenResponseSchema>;

export const LinkStatusResponseSchema = z.object({
  linked: z.boolean(),
  channel_user_id_masked: z.string().nullable(),
  linked_at: z.string().datetime().nullable(),
});
export type LinkStatusResponse = z.infer<typeof LinkStatusResponseSchema>;

export const UnlinkResponseSchema = z.object({
  revoked: z.boolean(),
});
export type UnlinkResponse = z.infer<typeof UnlinkResponseSchema>;
