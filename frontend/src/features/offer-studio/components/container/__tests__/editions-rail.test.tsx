import { render, screen, fireEvent } from "@testing-library/react";
import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";

// ── Mocks ────────────────────────────────────────────────────────────────────

const mockPush = vi.fn();
const mockReplace = vi.fn();
const mockUsePathname = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush, replace: mockReplace }),
  usePathname: () => mockUsePathname(),
}));

// ── Imports after mocks ──────────────────────────────────────────────────────

import { EditionStatus, EditionVisibility } from "../../../types";
import { EditionsRail } from "../EditionsRail";
import { EditionsRailCollapsed } from "../EditionsRailCollapsed";

import type { LaunchEdition } from "../../../types";

const upcoming: LaunchEdition = {
  id: "ed-3",
  offer_id: "offer-1",
  edition_name: "Edición #3",
  edition_number: 3,
  start_date: "2026-07-15T19:00:00Z",
  end_date: null,
  registration_start: null,
  registration_end: null,
  timezone: "UTC",
  pricing_override: null,
  pricing_tiers: [],
  active_tier: null,
  effective_pricing: [],
  currency: "USD",
  capacity: 50,
  enrollment_count: 12,
  status: EditionStatus.UPCOMING,
  visibility: EditionVisibility.PUBLIC,
  is_placeholder: false,
  location_override: null,
  notes: null,
  cloned_from_edition_id: null,
  created_at: null,
  updated_at: null,
};

const draft: LaunchEdition = {
  ...upcoming,
  id: "ed-4",
  edition_number: 4,
  start_date: null,
  status: EditionStatus.DRAFT,
  visibility: EditionVisibility.PRIVATE,
};

const completed: LaunchEdition = {
  ...upcoming,
  id: "ed-2",
  edition_number: 2,
  start_date: "2026-04-14T19:00:00Z",
  status: EditionStatus.COMPLETED,
  visibility: EditionVisibility.PUBLIC,
  enrollment_count: 25,
  capacity: 25,
};

const BASE = "/acme/offer-studio/offer/offer-1";
const baseProps = {
  offerId: "offer-1",
  tenantId: "acme",
  editions: [upcoming, draft, completed],
  currentEditionId: "ed-3",
  onCollapse: vi.fn(),
  onCreateNew: vi.fn(),
};

describe("EditionsRail (expanded, slim header v3)", () => {
  beforeEach(() => {
    mockPush.mockReset();
    mockReplace.mockReset();
    mockUsePathname.mockReset();
    mockUsePathname.mockReturnValue(BASE); // default: on Info
    baseProps.onCollapse = vi.fn();
    baseProps.onCreateNew = vi.fn();
  });

  it("renders a generic 'Ediciones' label in the header (no offer name)", () => {
    render(<EditionsRail {...baseProps} />);
    expect(screen.getByText(/^Ediciones$/)).toBeInTheDocument();
  });

  it("does not render the offer name anywhere in the rail", () => {
    render(<EditionsRail {...baseProps} />);
    expect(screen.queryByText(/MasterClass/i)).toBeNull();
  });

  it("renders the three lifecycle groups", () => {
    render(<EditionsRail {...baseProps} />);
    expect(screen.getByText(/⭐ Próxima/)).toBeInTheDocument();
    expect(screen.getByText(/✏ Borradores/)).toBeInTheDocument();
    expect(screen.getByText(/✓ Pasadas/)).toBeInTheDocument();
  });

  it("lists each edition with its number", () => {
    render(<EditionsRail {...baseProps} />);
    expect(screen.getByText("Edición #3")).toBeInTheDocument();
    expect(screen.getByText("Edición #4")).toBeInTheDocument();
    expect(screen.getByText("Edición #2")).toBeInTheDocument();
  });

  // ── Navigation: path-based, preserves current tab ──────────────────────────

  it("from Info: clicking an entry pushes /editions/{eid} (no tab suffix)", () => {
    mockUsePathname.mockReturnValue(BASE);
    render(<EditionsRail {...baseProps} />);
    fireEvent.click(screen.getByText("Edición #2"));
    expect(mockPush).toHaveBeenCalledWith(`${BASE}/editions/ed-2`);
  });

  it("from a per-edition tab: clicking another edition preserves the tab suffix", () => {
    mockUsePathname.mockReturnValue(`${BASE}/editions/ed-3/ventas`);
    render(<EditionsRail {...baseProps} />);
    fireEvent.click(screen.getByText("Edición #2"));
    expect(mockPush).toHaveBeenCalledWith(`${BASE}/editions/ed-2/ventas`);
  });

  it("from an offer-level tab (evergreen): preserves that tab under the new edition", () => {
    mockUsePathname.mockReturnValue(`${BASE}/ventas`);
    render(<EditionsRail {...baseProps} />);
    fireEvent.click(screen.getByText("Edición #2"));
    expect(mockPush).toHaveBeenCalledWith(`${BASE}/editions/ed-2/ventas`);
  });

  it("from an unknown deep path: falls back to the edition default", () => {
    mockUsePathname.mockReturnValue(`${BASE}/some/unknown/segment`);
    render(<EditionsRail {...baseProps} />);
    fireEvent.click(screen.getByText("Edición #2"));
    expect(mockPush).toHaveBeenCalledWith(`${BASE}/editions/ed-2`);
  });

  // ── Other behaviour ────────────────────────────────────────────────────────

  it("collapse button fires onCollapse", () => {
    render(<EditionsRail {...baseProps} />);
    fireEvent.click(screen.getByLabelText("Contraer rail"));
    expect(baseProps.onCollapse).toHaveBeenCalledTimes(1);
  });

  it("nueva edición button fires onCreateNew", () => {
    render(<EditionsRail {...baseProps} />);
    fireEvent.click(screen.getByRole("button", { name: /Nueva edición/i }));
    expect(baseProps.onCreateNew).toHaveBeenCalledTimes(1);
  });

  it("renders empty state when no editions", () => {
    render(<EditionsRail {...baseProps} editions={[]} />);
    expect(screen.getByText(/Sin ediciones todavía/i)).toBeInTheDocument();
  });
});

describe("EditionsRailCollapsed", () => {
  beforeEach(() => {
    mockPush.mockReset();
    mockReplace.mockReset();
    mockUsePathname.mockReset();
    mockUsePathname.mockReturnValue(BASE);
  });

  it("renders one badge per edition plus the + button", () => {
    const onExpand = vi.fn();
    const onCreateNew = vi.fn();
    render(
      <EditionsRailCollapsed
        offerId="offer-1"
        tenantId="acme"
        editions={[upcoming, draft, completed]}
        currentEditionId="ed-3"
        onExpand={onExpand}
        onCreateNew={onCreateNew}
      />,
    );
    expect(screen.getByText("3")).toBeInTheDocument();
    expect(screen.getByText("4")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
    expect(screen.getByLabelText(/Expandir rail/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Crear nueva edición/i)).toBeInTheDocument();
  });

  it("clicking a badge pushes /editions/{eid} preserving the current tab", () => {
    mockUsePathname.mockReturnValue(`${BASE}/editions/ed-4/assets`);
    render(
      <EditionsRailCollapsed
        offerId="offer-1"
        tenantId="acme"
        editions={[upcoming]}
        currentEditionId={null}
        onExpand={vi.fn()}
        onCreateNew={vi.fn()}
      />,
    );
    fireEvent.click(screen.getByText("3"));
    expect(mockPush).toHaveBeenCalledWith(`${BASE}/editions/ed-3/assets`);
  });
});
