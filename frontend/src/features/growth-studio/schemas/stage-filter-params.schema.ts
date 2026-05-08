/**
 * Stage filter params schema — FE mirror of BE Pydantic StageFilterParams.
 *
 * Consumes 2A registries (STAGE_REGISTRY + CHANNEL_REGISTRY) — NO hardcoded slugs.
 * Uses .strict() to mirror Pydantic ConfigDict(extra="forbid").
 *
 * Adversarial defense: z.enum() rejects path injection, XSS, prompt injection,
 * and tenant_id payload smuggling at parse time.
 */
import { z } from "zod";

import { CHANNEL_REGISTRY } from "../lib/registries/channel-registry";
import { STAGE_REGISTRY } from "../lib/registries/stage-registry";

// ─── Enum values from registries (SSoT — 2A) ─────────────────────────────────

const STAGE_SLUGS = STAGE_REGISTRY.map((s) => s.slug) as [string, ...string[]];
const CHANNEL_SLUGS = CHANNEL_REGISTRY.map((c) => c.slug) as [string, ...string[]];

// ─── Schema ───────────────────────────────────────────────────────────────────

/**
 * Mirrors BE `StageFilterParams` (Pydantic v2, extra="forbid").
 *
 * Fields:
 * - stage: canonical funnel stage slug (from STAGE_REGISTRY)
 * - channel: optional channel slug filter (from CHANNEL_REGISTRY)
 * - period: time window "7d" | "30d" | "90d", defaults to "30d"
 */
export const stageFilterParamsSchema = z
  .object({
    stage: z.enum(STAGE_SLUGS),
    channel: z.enum(CHANNEL_SLUGS).optional(),
    period: z.enum(["7d", "30d", "90d"]).default("30d"),
  })
  .strict(); // mirrors Pydantic extra="forbid"

export type StageFilterParams = z.infer<typeof stageFilterParamsSchema>;
