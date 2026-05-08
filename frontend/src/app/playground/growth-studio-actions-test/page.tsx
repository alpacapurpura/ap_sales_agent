/**
 * Playground page — Growth Studio Action Components (test/dev only).
 *
 * Renders all 5 growth-studio action components with deterministic mock data.
 * Accessible only in non-production environments (playground layout redirect guard).
 *
 * Used by Playwright VR specs to capture visual baselines without requiring
 * a live copilot SSE stream. Each section has a stable data-testid for locator
 * selection.
 *
 * URL: /playground/growth-studio-actions-test
 */
"use client";

import { StageMetricsAction } from "@/features/growth-studio/actions/StageMetricsAction";
import { ChannelOverviewAction } from "@/features/growth-studio/actions/ChannelOverviewAction";
import { ETLRefreshAction } from "@/features/growth-studio/actions/ETLRefreshAction";
import { ETLRateLimitedAction } from "@/features/growth-studio/actions/ETLRateLimitedAction";
import { ETLConfirmAction } from "@/features/growth-studio/actions/ETLConfirmAction";

// ─── Mock payloads (deterministic, VR-stable) ────────────────────────────────

const STAGE_METRICS_MOCK = {
  stage_name: "Adopción",
  period: "Últimos 30 días",
  kpis: [
    { slug: "active_customers", value: 142 },
    { slug: "health_score_avg", value: 82 },
    { slug: "revenue_usd", value: 18500, currency: "USD" },
  ],
  tier_used: 1 as const,
  truncated: false,
  channel_breakdown: [
    { channel: "Meta Ads", value: 6200, currency: "USD" },
    { channel: "Email", value: 4800, currency: "USD" },
  ],
};

const STAGE_METRICS_TRUNCATED_MOCK = {
  stage_name: "Atracción y Captura",
  period: "Últimos 30 días",
  kpis: [{ slug: "impressions", value: 1_250_000 }],
  tier_used: 2 as const,
  truncated: true,
  row_count: 12_400,
};

const CHANNEL_OVERVIEW_MOCK = {
  channel_name: "Meta Ads",
  period: "last_30_days",
  dashboard_kpis: [
    { slug: "spend", value: 3200, label: "Inversión", currency: "USD" },
    { slug: "impressions", value: 180_000, label: "Impresiones" },
    { slug: "clicks", value: 4_200, label: "Clics" },
    { slug: "conversions", value: 98, label: "Conversiones" },
  ],
};

const ETL_REFRESH_MOCK = {
  status: "queued" as const,
  channel: "meta-ads",
  run_id: "run_2b_mock_001",
};

const ETL_RATE_LIMITED_MOCK = {
  channel: "meta-ads",
  retry_after_seconds: 1860,
};

const ETL_CONFIRM_MOCK = {
  channel: "meta-ads",
  confirm_message: "Ya iniciaste una actualización en la última hora. ¿Confirmas otro refresco?",
};

// ─── Noop onChange ────────────────────────────────────────────────────────────

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function noop(_: any) {}

// ─── Page ────────────────────────────────────────────────────────────────────

/**
 * Renders 6 action component instances with stable mock data.
 * Each section is wrapped in a div with data-testid for Playwright locators.
 */
export default function GrowthStudioActionsTestPage() {
  return (
    <main className="min-h-screen bg-background p-8 space-y-8">
      <h1 className="text-xl font-bold">Growth Studio — Action Components (Playground)</h1>

      {/* 1. StageMetricsAction — normal state */}
      <div data-testid="action-stage-metrics-normal" className="max-w-lg">
        <p className="text-xs text-muted-foreground mb-2">StageMetricsAction — normal</p>
        <StageMetricsAction value={STAGE_METRICS_MOCK} onChange={noop} />
      </div>

      {/* 2. StageMetricsAction — truncated / large-volume state */}
      <div data-testid="action-stage-metrics-truncated" className="max-w-lg">
        <p className="text-xs text-muted-foreground mb-2">StageMetricsAction — truncated</p>
        <StageMetricsAction value={STAGE_METRICS_TRUNCATED_MOCK} onChange={noop} />
      </div>

      {/* 3. ChannelOverviewAction */}
      <div data-testid="action-channel-overview" className="max-w-lg">
        <p className="text-xs text-muted-foreground mb-2">ChannelOverviewAction</p>
        <ChannelOverviewAction value={CHANNEL_OVERVIEW_MOCK} onChange={noop} />
      </div>

      {/* 4. ETLRefreshAction — queued */}
      <div data-testid="action-etl-refresh" className="max-w-lg">
        <p className="text-xs text-muted-foreground mb-2">ETLRefreshAction — queued</p>
        <ETLRefreshAction value={ETL_REFRESH_MOCK} onChange={noop} />
      </div>

      {/* 5. ETLRateLimitedAction */}
      <div data-testid="action-etl-rate-limited" className="max-w-lg">
        <p className="text-xs text-muted-foreground mb-2">ETLRateLimitedAction</p>
        <ETLRateLimitedAction value={ETL_RATE_LIMITED_MOCK} onChange={noop} />
      </div>

      {/* 6. ETLConfirmAction — confirm prompt */}
      <div data-testid="action-etl-confirm" className="max-w-lg">
        <p className="text-xs text-muted-foreground mb-2">ETLConfirmAction — confirm prompt</p>
        <ETLConfirmAction value={ETL_CONFIRM_MOCK} onChange={noop} />
      </div>
    </main>
  );
}
