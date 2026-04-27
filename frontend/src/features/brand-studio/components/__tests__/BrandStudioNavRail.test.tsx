import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

import type { SectionStatusEntry } from "@/features/copilot/hooks/use-section-status";

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

// Fase 03 · Block D — BrandStudioNavRail now consumes the BE section
// catalog via ``useBrandSectionCatalog``. Stub it with the 14-section
// fixture so component tests stay decoupled from React Query.
const MOCK_BRAND_SECTIONS = [
  {
    key: "publico",
    label_es: "Buyer personas",
    icon_name: "Sparkles",
    kind: "collection" as const,
  },
  { key: "identity", label_es: "Identidad", icon_name: "Fingerprint", kind: "singleton" as const },
  {
    key: "estilo",
    label_es: "Estilo Comunicacional",
    icon_name: "MessageCircle",
    kind: "singleton" as const,
  },
  {
    key: "positioning",
    label_es: "Posicionamiento",
    icon_name: "Target",
    kind: "singleton" as const,
  },
  { key: "narrative", label_es: "Narrativa", icon_name: "ScrollText", kind: "singleton" as const },
  { key: "methodology", label_es: "Metodología", icon_name: "Flag", kind: "singleton" as const },
  { key: "story", label_es: "Historia", icon_name: "FileText", kind: "singleton" as const },
  { key: "team", label_es: "Equipo", icon_name: "Users", kind: "collection" as const },
  { key: "authority", label_es: "Autoridad", icon_name: "Landmark", kind: "collection" as const },
  {
    key: "testimonials",
    label_es: "Testimonios",
    icon_name: "Headphones",
    kind: "collection" as const,
  },
  { key: "visuals", label_es: "Visuales", icon_name: "Palette", kind: "singleton" as const },
  {
    key: "communication-assets",
    label_es: "Assets",
    icon_name: "Layers",
    kind: "singleton" as const,
  },
  { key: "contact", label_es: "Contacto", icon_name: "Megaphone", kind: "singleton" as const },
  { key: "legal", label_es: "Legal", icon_name: "Scale", kind: "singleton" as const },
];

vi.mock("../../hooks/use-brand-section-catalog", () => ({
  useBrandSectionCatalog: () => ({
    data: { version: "test", sections: MOCK_BRAND_SECTIONS },
  }),
}));

// Import after mocks are registered.
const { BrandStudioNavRail } = await import("../BrandStudioNavRail");

describe("BrandStudioNavRail", () => {
  beforeEach(() => {
    mockSectionStatus.mockReturnValue({});
  });

  it("renders every section link from the catalog", () => {
    setRoute("/t-demo/brand-studio/identity");
    render(<BrandStudioNavRail />);
    // 14 sections served by the backend catalog mock.
    const links = screen.getAllByRole("link");
    expect(links.length).toBe(MOCK_BRAND_SECTIONS.length);
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
