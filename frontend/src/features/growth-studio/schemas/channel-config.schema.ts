/**
 * Channel config schema — FE mirror of BE Pydantic ChannelOverviewParams.
 *
 * Consumes CHANNEL_REGISTRY — NO hardcoded channel slugs.
 * Uses .strict() to mirror Pydantic ConfigDict(extra="forbid").
 */
import { z } from "zod";

import { CHANNEL_REGISTRY } from "../lib/registries/channel-registry";

// ─── Enum values from registry (SSoT — 2A) ───────────────────────────────────

const CHANNEL_SLUGS = CHANNEL_REGISTRY.map((c) => c.slug) as [string, ...string[]];

// ─── Schema ───────────────────────────────────────────────────────────────────

/**
 * Channel configuration schema.
 *
 * Fields:
 * - slug: canonical channel slug (from CHANNEL_REGISTRY)
 * - dashboard: dashboard route identifier (kebab-case alphanumeric)
 * - kpis: ordered list of KPI names (min 1)
 * - color: hex color for channel branding (#RRGGBB)
 * - etl_rate_limit_per_hour: override for rate limit (1-20, default 3)
 */
export const channelConfigSchema = z
  .object({
    slug: z.enum(CHANNEL_SLUGS),
    dashboard: z.string().regex(/^[a-z0-9-]+$/, "Dashboard slug must be kebab-case alphanumeric"),
    kpis: z.array(z.string()).min(1, "Al menos un KPI requerido"),
    color: z.string().regex(/^#[0-9A-Fa-f]{6}$/, "Color debe ser un hex válido (#RRGGBB)"),
    etl_rate_limit_per_hour: z.number().int().min(1).max(20).default(3),
  })
  .strict(); // mirrors Pydantic extra="forbid"

export type ChannelConfig = z.infer<typeof channelConfigSchema>;
