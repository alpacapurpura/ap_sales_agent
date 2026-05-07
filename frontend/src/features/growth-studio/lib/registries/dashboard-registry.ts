/**
 * Dashboard Registry — per-channel lazy-loaded component map.
 *
 * Maps each ChannelSlug to a lazy import factory function for code-splitting.
 * Factories mirror the dynamic() imports in ChannelDashboardView.tsx.
 * Consumers: ChannelDispatcher (T-2), arch tests (T-6).
 *
 * Shape: Record<ChannelSlug, () => Promise<{ default: ComponentType }>>
 *
 * DO NOT hardcode channel→component mapping outside this registry.
 */

import type { ChannelSlug } from "./channel-registry";
import type { ComponentType } from "react";

// ─── Types ────────────────────────────────────────────────────────────────────

/** Lazy import factory — returns a Promise resolving to a default-export component. */
export type DashboardFactory = () => Promise<{ default: ComponentType }>;

// ─── Registry ────────────────────────────────────────────────────────────────

/**
 * Per-channel lazy import factories for dashboard components.
 * Each value is a function so callers control when the import fires.
 *
 * Paths mirror ChannelDashboardView.tsx dynamic() imports.
 */
export const DASHBOARD_COMPONENT_MAP: Record<ChannelSlug, DashboardFactory> = {
  "ig-organic": () =>
    import("../../components/metrics-dashboard/sidebar/ig-organic/IgOrganicDashboard").then(
      (m) => ({ default: m.IgOrganicDashboard as ComponentType }),
    ),

  "meta-ads": () =>
    import("../../components/metrics-dashboard/sidebar/meta-ads/MetaAdsDashboard").then((m) => ({
      default: m.MetaAdsDashboard as ComponentType,
    })),

  "yt-organic": () =>
    import("../../components/metrics-dashboard/sidebar/youtube-organic/YouTubeDashboard").then(
      (m) => ({ default: m.YouTubeDashboard as ComponentType }),
    ),

  "email-nurture": () =>
    import("../../components/metrics-dashboard/sidebar/mail/MailDashboard").then((m) => ({
      default: m.MailDashboard as ComponentType,
    })),

  "website-total": () =>
    import("../../components/metrics-dashboard/sidebar/website/WebsiteDashboard").then((m) => ({
      default: m.WebsiteDashboard as ComponentType,
    })),
};
