import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";

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

describe("BrandStudioNavRail", () => {
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
});
