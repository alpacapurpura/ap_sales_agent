import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";

import { OfferShell } from "../OfferShell";

import type { Offer } from "../../../types";

// ── Mocks ────────────────────────────────────────────────────────────────────

const mockUseEditions = vi.fn();
const mockUseOfferWithEdition = vi.fn();
const mockUseRailCollapsed = vi.fn();

vi.mock("../../../hooks/use-editions", () => ({
  useEditions: (...args: unknown[]) => mockUseEditions(...args),
}));

vi.mock("../../../hooks/use-offer-with-edition", () => ({
  useOfferWithEdition: (...args: unknown[]) => mockUseOfferWithEdition(...args),
}));

vi.mock("../../../hooks/use-rail-collapsed", () => ({
  useRailCollapsed: () => mockUseRailCollapsed(),
}));

// Stub the three heaviest children so the OfferShell test stays focused on
// layout + wiring rather than their internal behaviour.
vi.mock("../OfferShellHeaderRow1", () => ({
  OfferShellHeaderRow1: () => <div data-testid="row1" />,
}));

vi.mock("../OfferTabBar", () => ({
  OfferTabBar: () => <nav data-testid="tab-bar" />,
}));

vi.mock("../EditionsRail", () => ({
  EditionsRail: ({ onCreateNew }: { onCreateNew: () => void }) => (
    <aside data-testid="editions-rail">
      <button type="button" data-testid="rail-new-edition" onClick={onCreateNew}>
        Nueva edición
      </button>
    </aside>
  ),
}));

vi.mock("../EditionsRailCollapsed", () => ({
  EditionsRailCollapsed: () => <aside data-testid="editions-rail-collapsed" />,
}));

const mockEditionFormDialog = vi.fn();
vi.mock("../../editions/EditionFormDialog", () => ({
  EditionFormDialog: (props: { open: boolean; onOpenChange: (o: boolean) => void }) => {
    mockEditionFormDialog(props);
    return props.open ? <div data-testid="edition-form-dialog">edit-dialog</div> : null;
  },
}));

// ── Imports after mocks ──────────────────────────────────────────────────────

// ── Fixtures ─────────────────────────────────────────────────────────────────

function buildOffer(overrides: Partial<Offer> = {}): Offer {
  return {
    id: "offer-1",
    tenant_id: "tenant-1",
    name: "MasterClass Copy",
    status: "active",
    has_editions: true,
    archetype: "programa",
    format_hint: null,
    pricing: [],
    currency: "PEN",
    // Remaining fields are marked optional in the Offer type or carry safe
    // defaults; we spread overrides so tests can override shape freely.
    ...overrides,
  } as Offer;
}

const TENANT = "acme";
const counts = { assets: 2, campaigns: 1, knowledge: 0, active_campaigns: 1 };

describe("OfferShell — v3 layout", () => {
  beforeEach(() => {
    mockEditionFormDialog.mockReset();
    mockUseEditions.mockReturnValue({ editions: [], createEdition: vi.fn() });
    mockUseOfferWithEdition.mockReturnValue({ currentEditionId: null });
    mockUseRailCollapsed.mockReturnValue([false, vi.fn()]);
  });

  it("renders Row1 but not the deprecated Row2", () => {
    render(
      <OfferShell offer={buildOffer({ has_editions: false })} counts={counts} tenantId={TENANT}>
        <div data-testid="tab-content" />
      </OfferShell>,
    );
    expect(screen.getByTestId("row1")).toBeInTheDocument();
    // Row2 held the progress bar. It must not render in v3.
    expect(screen.queryByTestId("offer-progress-bar")).toBeNull();
  });

  it("renders the tab bar and the children", () => {
    render(
      <OfferShell offer={buildOffer({ has_editions: false })} counts={counts} tenantId={TENANT}>
        <div data-testid="tab-content" />
      </OfferShell>,
    );
    expect(screen.getByTestId("tab-bar")).toBeInTheDocument();
    expect(screen.getByTestId("tab-content")).toBeInTheDocument();
  });

  it("renders the EditionsRail when offer.has_editions === true", () => {
    render(
      <OfferShell offer={buildOffer({ has_editions: true })} counts={counts} tenantId={TENANT}>
        <div />
      </OfferShell>,
    );
    expect(screen.getByTestId("editions-rail")).toBeInTheDocument();
  });

  it("hides the rail entirely when offer.has_editions === false", () => {
    render(
      <OfferShell offer={buildOffer({ has_editions: false })} counts={counts} tenantId={TENANT}>
        <div />
      </OfferShell>,
    );
    expect(screen.queryByTestId("editions-rail")).toBeNull();
    expect(screen.queryByTestId("editions-rail-collapsed")).toBeNull();
  });

  it("shows the collapsed variant when the rail is collapsed", () => {
    mockUseRailCollapsed.mockReturnValue([true, vi.fn()]);
    render(
      <OfferShell offer={buildOffer({ has_editions: true })} counts={counts} tenantId={TENANT}>
        <div />
      </OfferShell>,
    );
    expect(screen.getByTestId("editions-rail-collapsed")).toBeInTheDocument();
    expect(screen.queryByTestId("editions-rail")).toBeNull();
  });

  it("clicking 'Nueva edición' in the rail opens the EditionFormDialog (no console stub)", async () => {
    const user = userEvent.setup();
    render(
      <OfferShell offer={buildOffer({ has_editions: true })} counts={counts} tenantId={TENANT}>
        <div />
      </OfferShell>,
    );
    // Initially dialog is closed.
    expect(screen.queryByTestId("edition-form-dialog")).toBeNull();
    expect(mockEditionFormDialog).toHaveBeenCalledWith(expect.objectContaining({ open: false }));

    await user.click(screen.getByTestId("rail-new-edition"));

    expect(screen.getByTestId("edition-form-dialog")).toBeInTheDocument();
    expect(mockEditionFormDialog).toHaveBeenLastCalledWith(expect.objectContaining({ open: true }));
  });

  it("places Row1 above the rail/content split (Row1 is the first main descendant)", () => {
    const { container } = render(
      <OfferShell offer={buildOffer({ has_editions: true })} counts={counts} tenantId={TENANT}>
        <div data-testid="tab-content" />
      </OfferShell>,
    );
    // The top-level flex container owns: main wrapper. Row1 must precede the
    // rail+content split in the document order. We assert that by locating
    // Row1's index relative to the rail.
    const row1 = screen.getByTestId("row1");
    const rail = screen.getByTestId("editions-rail");
    // Row1 should appear before the rail in document order.

    const positionBits = row1.compareDocumentPosition(rail);
    expect(positionBits & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(container).toBeTruthy();
  });
});
