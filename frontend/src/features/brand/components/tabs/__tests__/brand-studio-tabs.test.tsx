import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";

import { BrandStudioTabs } from "../brand-studio-tabs";

import type { BrandSettings } from "../../../types";

const mockSettings: BrandSettings = {
  identity: { brand_name: "Test Brand", industry: "Tech" },
  story: { origin_story: "Founded in 2020" },
  strategy: { methodology_pillars: [] },
  positioning: { reasons_to_believe: [] },
  narrative: { plan: [] },
  visuals: {},
  team: [],
  contact: {},
  authority_vault: [],
  communication_assets: undefined,
};

describe("BrandStudioTabs", () => {
  it("renders all 4 section tabs", () => {
    render(<BrandStudioTabs activeTab="esencia" onTabChange={vi.fn()} settings={mockSettings} />);
    expect(screen.getByRole("tab", { name: /esencia/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /estrategia/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /público/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /identidad creativa/i })).toBeInTheDocument();
  });

  it("shows health percentage on each tab", () => {
    render(<BrandStudioTabs activeTab="esencia" onTabChange={vi.fn()} settings={mockSettings} />);
    const esenciaTab = screen.getByRole("tab", { name: /esencia/i });
    expect(esenciaTab).toHaveTextContent("%");
  });

  it("calls onTabChange when clicking a tab", async () => {
    const onTabChange = vi.fn();
    render(
      <BrandStudioTabs activeTab="esencia" onTabChange={onTabChange} settings={mockSettings} />,
    );
    await userEvent.click(screen.getByRole("tab", { name: /estrategia/i }));
    expect(onTabChange).toHaveBeenCalledWith("estrategia");
  });

  it("marks active tab visually", () => {
    render(
      <BrandStudioTabs activeTab="estrategia" onTabChange={vi.fn()} settings={mockSettings} />,
    );
    const activeTab = screen.getByRole("tab", { name: /estrategia/i });
    expect(activeTab).toHaveAttribute("data-state", "active");
  });
});
