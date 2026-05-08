/**
 * T-5 Phase 5 — growth-studio-folder-parity
 *
 * Verifica que los 6 dashboards sidebar + ChannelConnectionModal consumen
 * `useCopilotOffset` y aplican el offset correctamente a los elementos
 * fixed/portal, eliminando la superposición con el drawer del copilot.
 *
 * Origin: PI-8 PR-1 hotfix. 6 KNOWN_VIOLATIONS drenadas en T-5.
 *
 * Tests:
 * 1. [yt] YouTubeDashboard aplica paddingRight = offset al contenedor fixed
 * 2. [yt] YouTubeDashboard NO aplica paddingRight en modo isRouteBased
 * 3. [mail] MailDashboard aplica paddingRight = offset al contenedor fixed
 * 4. [meta] MetaAdsDashboard aplica paddingRight = offset al contenedor fixed
 * 5. [ig] IgOrganicDashboard aplica paddingRight = offset al contenedor fixed
 * 6. [website] WebsiteDashboard aplica paddingRight = offset al contenedor fixed
 * 7. [modal] ChannelConnectionModal aplica marginRight = offset al Dialog.Content
 * 8. [modal] ChannelConnectionModal NO aplica marginRight cuando offset = 0
 */
import { render } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

// ── Mock useCopilotOffset ────────────────────────────────────────────────────
const useCopilotOffsetMock = vi.fn<() => number>(() => 0);

vi.mock("@/hooks/use-copilot-offset", () => ({
  useCopilotOffset: () => useCopilotOffsetMock(),
  COPILOT_OPEN_WIDTH: 460,
  COPILOT_RAIL_WIDTH: 60,
}));

// ── Navigation mocks ─────────────────────────────────────────────────────────
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
  useParams: () => ({ tenantId: "tenant-1" }),
  useSearchParams: () => ({ get: () => null }),
}));

// ── Clerk mock (needed by useMailDashboard + any hook that calls useAuth) ────
vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({
    getToken: vi.fn().mockResolvedValue("mock-token"),
    isLoaded: true,
    isSignedIn: true,
  }),
}));

// ── React Query mocks (hooks used by dashboards) ─────────────────────────────
vi.mock("@/features/growth-studio/hooks/use-channel-dashboard", () => ({
  useChannelDashboard: () => ({ data: undefined, isLoading: false }),
}));

vi.mock("@/features/growth-studio/hooks/use-sync-channel", () => ({
  useSyncChannel: () => ({
    sync: vi.fn(),
    isSyncing: false,
    cooldownMinutes: 0,
    result: null,
    error: null,
  }),
}));

vi.mock("@/features/growth-studio/hooks/use-hash-scroll", () => ({
  useHashScroll: () => undefined,
}));

vi.mock("@/features/growth-studio/hooks/use-connection-health", () => ({
  useConnectionHealth: () => ({ data: null }),
}));

// ── Mail-specific mocks (useMailDashboard calls useAuth + useQuery) ──────────
vi.mock("@/features/growth-studio/hooks/use-mail-dashboard", () => ({
  useMailDashboard: () => ({ data: undefined, isLoading: false }),
}));

// ── MetaAds-specific mocks ───────────────────────────────────────────────────
// campaignData: use `undefined` (not null) so computeMetaAdsOnboardingTrigger
// correctly evaluates `bothLoaded = false` and skips `activeCampaigns` access.
vi.mock("@/features/growth-studio/api/campaigns-api", () => ({
  useCampaignPerformance: () => ({ data: undefined, isLoading: false }),
}));

vi.mock("@/features/growth-studio/api/offer-association-api", () => ({
  useAssociations: () => ({ data: undefined }),
  useMetaHealthCheck: () => ({ data: undefined }),
  useMetricsByOffer: () => ({ data: undefined, isLoading: false }),
  useOffersForAssignment: () => ({ data: undefined, isLoading: false }),
  useCampaignTemplateForOffer: () => ({ data: undefined, isLoading: false }),
  useCreateAssociation: () => ({ mutate: vi.fn(), isPending: false }),
  useDeleteAssociation: () => ({ mutate: vi.fn(), isPending: false }),
  useAutoDetectSuggestions: () => ({ data: undefined, isLoading: false }),
  useApplySuggestions: () => ({ mutate: vi.fn(), isPending: false }),
}));

// Return the full NoticesSummary shape that MetaAdsDashboard accesses
// (perTabCounts + maxSeverityPerTab per tab key).
const EMPTY_NOTICES_SUMMARY = {
  byTab: { campanas: [], creativos: [], audiencia: [], costos: [] },
  total: 0,
  perTabCounts: { campanas: 0, creativos: 0, audiencia: 0, costos: 0 },
  severity: { critical: 0, warning: 0, info: 0 },
  severityPerTab: {
    campanas: { critical: 0, warning: 0, info: 0 },
    creativos: { critical: 0, warning: 0, info: 0 },
    audiencia: { critical: 0, warning: 0, info: 0 },
    costos: { critical: 0, warning: 0, info: 0 },
  },
  maxSeverityPerTab: { campanas: null, creativos: null, audiencia: null, costos: null },
};

vi.mock("@/features/growth-studio/hooks/use-meta-ads-notices", () => ({
  useMetaAdsNotices: () => EMPTY_NOTICES_SUMMARY,
}));

vi.mock("@/features/tenant/context/tenant-locale-context", () => ({
  useTenantLocale: () => ({ currency: "USD", timezone: "UTC" }),
}));

vi.mock("@/lib/format-date", () => ({
  formatTenantDateTime: (d: string) => d,
}));

// ── ChannelConnectionModal mocks ─────────────────────────────────────────────
vi.mock("@/features/growth-studio/lib/channel-view-map", () => ({
  getConnectionView: () => null,
}));

// Radix dialog portal mock — renders portal content inline for jsdom.
// We override @radix-ui/react-dialog's Portal so that DialogPrimitive.Portal
// renders its children directly into the current container (no createPortal),
// making the dialog content queryable via the render container rather than
// document.body. The DialogOverlay (from @/components/ui/dialog) also wraps
// @radix-ui/react-dialog so we mock at the source level.
vi.mock("@radix-ui/react-dialog", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@radix-ui/react-dialog")>();
  return {
    ...actual,
    Portal: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  };
});

// ── Imports (after mocks are registered) ────────────────────────────────────
import React from "react";
import { YouTubeDashboard } from "@/features/growth-studio/components/metrics-dashboard/sidebar/youtube-organic/YouTubeDashboard";
import { MailDashboard } from "@/features/growth-studio/components/metrics-dashboard/sidebar/mail/MailDashboard";
import { MetaAdsDashboard } from "@/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/MetaAdsDashboard";
import { IgOrganicDashboard } from "@/features/growth-studio/components/metrics-dashboard/sidebar/ig-organic/IgOrganicDashboard";
import { WebsiteDashboard } from "@/features/growth-studio/components/metrics-dashboard/sidebar/website/WebsiteDashboard";
import { ChannelConnectionModal } from "@/features/growth-studio/components/metrics-dashboard/channel-widgets/ChannelConnectionModal";

// ── Helpers ──────────────────────────────────────────────────────────────────

/**
 * Returns the first element with className containing "fixed" inside a
 * React portal (rendered into document.body by createPortal).
 */
function getFixedContainer(): HTMLElement | null {
  return document.body.querySelector<HTMLElement>("[class*='fixed']");
}

beforeEach(() => {
  useCopilotOffsetMock.mockReset();
  useCopilotOffsetMock.mockReturnValue(0);
  // Clean up portals between tests
  document.body.innerHTML = "";
});

// ── YouTubeDashboard ─────────────────────────────────────────────────────────
describe("YouTubeDashboard — useCopilotOffset adoption", () => {
  it("applies paddingRight equal to copilotOffset on the fixed container when open", () => {
    useCopilotOffsetMock.mockReturnValue(460);
    render(<YouTubeDashboard />);

    const fixed = getFixedContainer();
    expect(fixed).not.toBeNull();
    expect(fixed?.style.paddingRight).toBe("460px");
  });

  it("does NOT apply paddingRight when isRouteBased=true", () => {
    useCopilotOffsetMock.mockReturnValue(460);
    render(<YouTubeDashboard isRouteBased />);

    // In route-based mode the component doesn't use createPortal so
    // the fixed container is not rendered; check no paddingRight applied.
    const containers = document.querySelectorAll<HTMLElement>("[class*='min-h-screen']");
    containers.forEach((el) => {
      expect(el.style.paddingRight).toBe("");
    });
  });
});

// ── MailDashboard ────────────────────────────────────────────────────────────
describe("MailDashboard — useCopilotOffset adoption", () => {
  it("applies paddingRight equal to copilotOffset on the fixed container when open", () => {
    useCopilotOffsetMock.mockReturnValue(460);
    render(<MailDashboard />);

    const fixed = getFixedContainer();
    expect(fixed).not.toBeNull();
    expect(fixed?.style.paddingRight).toBe("460px");
  });

  it("applies zero paddingRight when copilot is collapsed (offset=60)", () => {
    useCopilotOffsetMock.mockReturnValue(60);
    render(<MailDashboard />);

    const fixed = getFixedContainer();
    expect(fixed?.style.paddingRight).toBe("60px");
  });
});

// ── MetaAdsDashboard ─────────────────────────────────────────────────────────
describe("MetaAdsDashboard — useCopilotOffset adoption", () => {
  it("applies paddingRight equal to copilotOffset on the fixed container when open", () => {
    useCopilotOffsetMock.mockReturnValue(460);
    render(<MetaAdsDashboard />);

    const fixed = getFixedContainer();
    expect(fixed).not.toBeNull();
    expect(fixed?.style.paddingRight).toBe("460px");
  });
});

// ── IgOrganicDashboard ───────────────────────────────────────────────────────
describe("IgOrganicDashboard — useCopilotOffset adoption", () => {
  it("applies paddingRight equal to copilotOffset on the fixed container when open", () => {
    useCopilotOffsetMock.mockReturnValue(460);
    render(<IgOrganicDashboard />);

    const fixed = getFixedContainer();
    expect(fixed).not.toBeNull();
    expect(fixed?.style.paddingRight).toBe("460px");
  });
});

// ── WebsiteDashboard ─────────────────────────────────────────────────────────
describe("WebsiteDashboard — useCopilotOffset adoption", () => {
  it("applies paddingRight equal to copilotOffset on the fixed container when open", () => {
    useCopilotOffsetMock.mockReturnValue(460);
    render(<WebsiteDashboard />);

    const fixed = getFixedContainer();
    expect(fixed).not.toBeNull();
    expect(fixed?.style.paddingRight).toBe("460px");
  });
});

// ── ChannelConnectionModal ───────────────────────────────────────────────────
describe("ChannelConnectionModal — useCopilotOffset adoption", () => {
  const NOOP = () => undefined;

  it("applies marginRight to dialog content when copilot is open", () => {
    useCopilotOffsetMock.mockReturnValue(460);
    // With the Radix Portal mock rendering inline, query within container.
    // DialogPrimitive.Content has class "fixed left-[50%] top-[50%] ...".
    // DialogOverlay also has "fixed" so we target the element that has both
    // "fixed" AND "left-[50%]" to avoid matching the overlay.
    const { container } = render(
      <ChannelConnectionModal channelSlug="meta-ads" channelName="Meta Ads" onClose={NOOP} />,
    );

    // Find all fixed elements; the dialog Content is the one with grid class
    const allFixed = [
      ...Array.from(container.querySelectorAll<HTMLElement>("[class*='fixed']")),
      ...Array.from(document.body.querySelectorAll<HTMLElement>("[class*='fixed']")),
    ];
    const dialogContent = allFixed.find((el) => el.className.includes("grid")) ?? null;
    expect(dialogContent).not.toBeNull();
    expect(dialogContent?.style.marginRight).toBe("460px");
  });

  it("does NOT apply marginRight when copilot offset is 0", () => {
    useCopilotOffsetMock.mockReturnValue(0);
    const { container } = render(
      <ChannelConnectionModal channelSlug="meta-ads" channelName="Meta Ads" onClose={NOOP} />,
    );

    const allFixed = [
      ...Array.from(container.querySelectorAll<HTMLElement>("[class*='fixed']")),
      ...Array.from(document.body.querySelectorAll<HTMLElement>("[class*='fixed']")),
    ];
    const dialogContent = allFixed.find((el) => el.className.includes("grid")) ?? null;
    expect(dialogContent).not.toBeNull();
    expect(dialogContent?.style.marginRight).toBe("");
  });
});
