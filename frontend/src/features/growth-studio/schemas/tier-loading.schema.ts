/**
 * Tier loading schema — validates progressive-loading tier response payloads.
 *
 * Growth-studio uses 4-tier loading (0=summary, 1=overview, 2=group-detail, 3=stage).
 * This schema validates the tier response envelope; payload is validated separately
 * by tier-specific DTOs.
 *
 * Uses .strict() to mirror Pydantic ConfigDict(extra="forbid").
 */
import { z } from "zod";

// ─── Schema ───────────────────────────────────────────────────────────────────

/**
 * Tier response envelope schema.
 *
 * Fields:
 * - tier: 0 (summary) | 1 (overview) | 2 (group-detail) | 3 (full stage)
 * - size_hint: rough data size classification
 * - truncated: true when data was capped (e.g. >10k rows — triggers Tier 3 drilldown)
 * - row_count: number of rows in the response
 * - payload: tier-specific response data (validated by per-tier DTOs)
 */
export const tierResponseSchema = z
  .object({
    tier: z.union([z.literal(0), z.literal(1), z.literal(2), z.literal(3)]),
    size_hint: z.enum(["small", "medium", "large"]),
    truncated: z.boolean().default(false),
    row_count: z.number().int().min(0),
    payload: z.unknown(), // tier-specific DTOs validated separately
  })
  .strict(); // mirrors Pydantic extra="forbid"

export type TierResponse = z.infer<typeof tierResponseSchema>;
