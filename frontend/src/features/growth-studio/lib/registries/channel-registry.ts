/**
 * Channel Registry — SSoT for growth-studio channels.
 *
 * 5 canonical channels mapping to their funnel stages. Immutable (Object.freeze).
 * Replaces: config/channel-stage-map.ts getStageForChannel() (re-exported here).
 * Consumers: ChannelDispatcher (T-2), ChannelDashboardView, arch tests (T-6).
 *
 * DO NOT hardcode channel slugs elsewhere — consume this registry.
 */

import type { StageSlug } from "./stage-registry";

// ─── Types ────────────────────────────────────────────────────────────────────

export type ChannelSlug =
  | "meta-ads"
  | "yt-organic"
  | "email-nurture"
  | "ig-organic"
  | "website-total";

export interface ChannelRegistryEntry {
  /** Canonical slug (kebab-case). Used in URLs + API calls. */
  slug: ChannelSlug;
  /** Funnel stage this channel belongs to. */
  stageSlug: StageSlug;
  /** Spanish neutro display name. */
  name: string;
  /** ETL provider identifier (matches backend extraction_contract). */
  etlProvider: string;
  /** Brand color for charts and badges (CSS hex or Tailwind color token). */
  color: string;
}

// ─── Registry ────────────────────────────────────────────────────────────────

export const CHANNEL_REGISTRY: readonly ChannelRegistryEntry[] = Object.freeze([
  {
    slug: "meta-ads",
    stageSlug: "atraccion-captura",
    name: "Meta Ads",
    etlProvider: "meta_ads",
    color: "#1877F2",
  },
  {
    slug: "ig-organic",
    stageSlug: "atraccion-captura",
    name: "Instagram Orgánico",
    etlProvider: "ig_organic",
    color: "#E1306C",
  },
  {
    slug: "yt-organic",
    stageSlug: "atraccion-captura",
    name: "YouTube Orgánico",
    etlProvider: "yt_organic",
    color: "#FF0000",
  },
  {
    slug: "email-nurture",
    stageSlug: "nutricion-oportunidad",
    name: "Email Marketing",
    etlProvider: "email_nurture",
    color: "#10B981",
  },
  {
    slug: "website-total",
    stageSlug: "atraccion-captura",
    name: "Sitio Web",
    etlProvider: "website_total",
    color: "#6366F1",
  },
] as const satisfies ChannelRegistryEntry[]);

// ─── Accessors ───────────────────────────────────────────────────────────────

/**
 * Get the stage slug for a given channel.
 * Falls back to "atraccion-captura" for unknown channels.
 */
export function getStageForChannel(channelSlug: string): StageSlug {
  const entry = CHANNEL_REGISTRY.find((c) => c.slug === channelSlug);
  return entry?.stageSlug ?? "atraccion-captura";
}

/** Get a channel entry by slug, or undefined if not found. */
export function getChannel(slug: ChannelSlug): ChannelRegistryEntry | undefined {
  return CHANNEL_REGISTRY.find((c) => c.slug === slug);
}

/** Get all channel slugs. */
export function getChannelSlugs(): ChannelSlug[] {
  return CHANNEL_REGISTRY.map((c) => c.slug);
}

/** Get all channels belonging to a specific stage. */
export function getChannelsForStage(stageSlug: StageSlug): ChannelRegistryEntry[] {
  return CHANNEL_REGISTRY.filter((c) => c.stageSlug === stageSlug);
}
