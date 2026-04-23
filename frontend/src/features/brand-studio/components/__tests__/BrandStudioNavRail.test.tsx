import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

import type { SectionStatusEntry } from "@/features/copilot/hooks/use-section-status";

import { BrandStudioNavRail } from "../BrandStudioNavRail";

vi.mock("next/navigation", () => ({
  useParams: vi.fn(),
  usePathname: vi.fn(),
}));

const { useParams, usePathname } = await import("next/navigation");

function setRoute(path: string, tenantId = "t-demo") {
  vi.mocked(useParams).mockReturnValue({ tenantId } as never);
  vi.mocked(usePathname).mockReturnValue(path);
}

// ── Mock use-section-status ────────────────────────────────────────────────
// We mock useSectionStatus directly so the component tests are isolated from
// the copilot store. Each test seeds the return value via mockSectionStatus.

const mockSectionStatus = vi.fn(() => ({}) as Record<string, SectionStatusEntry>);

vi.mock("@/features/copilot/hooks/use-section-status", () => ({
  useSectionStatus: (_module: string) => mockSectionStatus(),
}));

describe("BrandStudioNavRail", () => {
  beforeEach(() => {
    mockSectionStatus.mockReturnValue({});
  });

  it("renders every section + personas link", () => {
    setRoute("/t-demo/brand-studio/identity");
    render(<BrandStudioNavRail />);
    // 11 factory-generated sections + personas = 12 links
    const links = screen.getAllByRole("link");
    expect(links.length).toBeGreaterThanOrEqual(12);
  });

  it("marks the active section with aria-current=page", () => {
    setRoute("/t-demo/brand-studio/positioning");
    render(<BrandStudioNavRail />);
    const activeLink = screen.getByRole("link", { current: "page" });
    expect(activeLink.textContent).toContain("Posicionamiento");
  });

  it("builds hrefs under the active tenant", () => {
    setRoute("/abc-tenant/brand-studio/identity", "abc-tenant");
    render(<BrandStudioNavRail />);
    const identityLink = screen.getByRole("link", { name: /Identidad/ });
    expect(identityLink.getAttribute("href")).toBe("/abc-tenant/brand-studio/identity");
  });

  it("derives the active section from the URL even when a fieldId segment exists", () => {
    setRoute("/t-demo/brand-studio/visuals/primary_color");
    render(<BrandStudioNavRail />);
    const activeLink = screen.getByRole("link", { current: "page" });
    expect(activeLink.textContent).toContain("Visuales");
  });

  // ── Badge tests ──────────────────────────────────────────────────────────

  it("idle state — no badges rendered", () => {
    setRoute("/t-demo/brand-studio/identity");
    mockSectionStatus.mockReturnValue({});
    render(<BrandStudioNavRail />);
    expect(screen.queryByText(/entrando/)).toBeNull();
    expect(screen.queryByText(/sugeridos/)).toBeNull();
    const queuedBadges = screen.queryAllByLabelText("En cola");
    expect(queuedBadges).toHaveLength(0);
  });

  it("running state — Identidad row shows spinner and '2 entrando'", () => {
    setRoute("/t-demo/brand-studio/identity");
    mockSectionStatus.mockReturnValue({
      identity: { status: "running", fieldCount: 2, fieldIds: ["brand_name", "tagline"] },
    });
    render(<BrandStudioNavRail />);
    expect(screen.getByText("2 entrando")).toBeTruthy();
    const spinners = document.querySelectorAll(".animate-spin");
    expect(spinners.length).toBeGreaterThanOrEqual(1);
  });

  it("completed state — Identidad row shows check and '5 sugeridos'", () => {
    setRoute("/t-demo/brand-studio/identity");
    mockSectionStatus.mockReturnValue({
      identity: {
        status: "completed",
        fieldCount: 5,
        fieldIds: ["brand_name", "tagline", "slogan", "logo_url", "primary_color"],
      },
    });
    render(<BrandStudioNavRail />);
    expect(screen.getByText("5 sugeridos")).toBeTruthy();
  });

  it("queued state — Posicionamiento row shows muted dot badge", () => {
    setRoute("/t-demo/brand-studio/identity");
    mockSectionStatus.mockReturnValue({
      positioning: { status: "queued", fieldCount: 0 },
    });
    render(<BrandStudioNavRail />);
    const queuedBadges = screen.getAllByLabelText("En cola");
    expect(queuedBadges.length).toBeGreaterThanOrEqual(1);
  });

  it("no layout shift — row has min-h-[36px] class across states", () => {
    setRoute("/t-demo/brand-studio/identity");
    mockSectionStatus.mockReturnValue({
      identity: { status: "running", fieldCount: 3, fieldIds: ["a", "b", "c"] },
    });
    render(<BrandStudioNavRail />);
    const activeLink = screen.getByRole("link", { current: "page" });
    expect(activeLink.className).toContain("min-h-[36px]");
  });
});
