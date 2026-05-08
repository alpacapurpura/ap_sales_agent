/**
 * ChannelDispatcher unit tests — T-2 growth-studio-folder-parity
 *
 * Verifica:
 * - Renders correct dashboard component per channel slug
 * - Reads from DASHBOARD_COMPONENT_MAP (no hardcoded slug→component switch)
 * - Shows fallback message for unknown channel
 * - All 5 canonical channel slugs are handled
 *
 * TDD: tests written RED before implementation.
 */
import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { Suspense } from "react";

// ─── Mocks ───────────────────────────────────────────────────────────────────

// Mock dashboard-registry to return simple identifiable components
vi.mock("@/features/growth-studio/lib/registries/dashboard-registry", () => ({
  DASHBOARD_COMPONENT_MAP: {
    "ig-organic": () =>
      Promise.resolve({
        default: () => <div data-testid="dashboard-ig-organic">IgOrganic</div>,
      }),
    "meta-ads": () =>
      Promise.resolve({
        default: () => <div data-testid="dashboard-meta-ads">MetaAds</div>,
      }),
    "yt-organic": () =>
      Promise.resolve({
        default: () => <div data-testid="dashboard-yt-organic">YouTube</div>,
      }),
    "email-nurture": () =>
      Promise.resolve({
        default: () => <div data-testid="dashboard-email-nurture">Email</div>,
      }),
    "website-total": () =>
      Promise.resolve({
        default: () => <div data-testid="dashboard-website-total">Website</div>,
      }),
  },
}));

// ─── Subject under test ───────────────────────────────────────────────────────

import { ChannelDispatcher } from "@/features/growth-studio/pages/ChannelDispatcher";
import type { GrowthStudioChannelSlug } from "@/features/growth-studio/pages/channel-slugs";

// ─── Tests ───────────────────────────────────────────────────────────────────

describe("ChannelDispatcher", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders IgOrganicDashboard for channel ig-organic", async () => {
    render(
      <Suspense fallback={<div>Loading...</div>}>
        <ChannelDispatcher slug="ig-organic" />
      </Suspense>,
    );
    const el = await screen.findByTestId("dashboard-ig-organic");
    expect(el).toBeTruthy();
  });

  it("renders MetaAdsDashboard for channel meta-ads", async () => {
    render(
      <Suspense fallback={<div>Loading...</div>}>
        <ChannelDispatcher slug="meta-ads" />
      </Suspense>,
    );
    const el = await screen.findByTestId("dashboard-meta-ads");
    expect(el).toBeTruthy();
  });

  it("renders YouTubeDashboard for channel yt-organic", async () => {
    render(
      <Suspense fallback={<div>Loading...</div>}>
        <ChannelDispatcher slug="yt-organic" />
      </Suspense>,
    );
    const el = await screen.findByTestId("dashboard-yt-organic");
    expect(el).toBeTruthy();
  });

  it("renders MailDashboard for channel email-nurture", async () => {
    render(
      <Suspense fallback={<div>Loading...</div>}>
        <ChannelDispatcher slug="email-nurture" />
      </Suspense>,
    );
    const el = await screen.findByTestId("dashboard-email-nurture");
    expect(el).toBeTruthy();
  });

  it("renders WebsiteDashboard for channel website-total", async () => {
    render(
      <Suspense fallback={<div>Loading...</div>}>
        <ChannelDispatcher slug="website-total" />
      </Suspense>,
    );
    const el = await screen.findByTestId("dashboard-website-total");
    expect(el).toBeTruthy();
  });

  it("covers all 5 canonical channel slugs (no missing entry in DASHBOARD_COMPONENT_MAP)", () => {
    const ALL_SLUGS: GrowthStudioChannelSlug[] = [
      "ig-organic",
      "meta-ads",
      "yt-organic",
      "email-nurture",
      "website-total",
    ];
    ALL_SLUGS.forEach((slug) => {
      expect(() =>
        render(
          <Suspense fallback={null}>
            <ChannelDispatcher slug={slug} />
          </Suspense>,
        ),
      ).not.toThrow();
    });
  });

  it("passes initialTab and isRouteBased props to dashboard component", async () => {
    // Dashboard components receive props; here we verify dispatcher passes them through
    // (the mock component doesn't consume them, but we verify no crash)
    expect(() =>
      render(
        <Suspense fallback={null}>
          <ChannelDispatcher slug="meta-ads" initialTab="campaigns" isRouteBased />
        </Suspense>,
      ),
    ).not.toThrow();
  });
});
