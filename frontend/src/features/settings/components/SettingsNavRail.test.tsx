import { render, screen } from "@testing-library/react";
import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";

// Mock next/navigation
vi.mock("next/navigation", () => ({
  useParams: () => ({ tenantId: "tenant-123" }),
  usePathname: () => "/tenant-123/settings/general",
}));

// Mock FinderColumn
vi.mock("@/components/form-runtime/FinderColumn", () => ({
  FinderColumn: ({ children, ariaLabel }: { children: React.ReactNode; ariaLabel?: string }) => (
    <nav aria-label={ariaLabel}>{children}</nav>
  ),
}));

import { SettingsNavRail } from "./SettingsNavRail";

describe("SettingsNavRail", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders all 3 group headers in order", () => {
    render(<SettingsNavRail />);
    const headers = screen.getAllByRole("banner").map((el) => el.textContent?.trim());
    // Groups are rendered as <header> elements inside <section>
    // Check group labels appear in the document
    expect(screen.getByText("Principal")).toBeInTheDocument();
    expect(screen.getByText("Ventas")).toBeInTheDocument();
    expect(screen.getByText("Desarrolladores")).toBeInTheDocument();
  });

  it("all 8 sections are rendered as links", () => {
    render(<SettingsNavRail />);
    const links = screen.getAllByRole("link");
    expect(links.length).toBe(8);
  });

  it("active section (general) has aria-current='page'", () => {
    render(<SettingsNavRail />);
    // pathname ends with /settings/general, so general should be active
    const activeLink = screen.getByRole("link", { name: /general/i });
    expect(activeLink).toHaveAttribute("aria-current", "page");
  });

  it("non-active sections do not have aria-current", () => {
    render(<SettingsNavRail />);
    const perfilLink = screen.getByRole("link", { name: /^perfil$/i });
    expect(perfilLink).not.toHaveAttribute("aria-current");
  });

  it("links point to correct tenant-scoped URLs", () => {
    render(<SettingsNavRail />);
    const generalLink = screen.getByRole("link", { name: /general/i });
    expect(generalLink).toHaveAttribute("href", "/tenant-123/settings/general");
  });
});
