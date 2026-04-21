import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";

import { MOCK_OFFER_NORMALIZED } from "../../../__tests__/fixtures";
import { LeadMagnetStreamCard } from "../LeadMagnetStreamCard";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
  useParams: () => ({ tenantId: "visionarias" }),
}));

vi.mock("@/components/shared/navigation", () => ({
  useNavigation: () => ({
    navigate: vi.fn(),
    isNavigating: false,
    navigateReplace: vi.fn(),
    pendingHref: null,
  }),
}));

vi.mock("@/features/tenant/context/tenant-locale-context", () => ({
  useTenantLocale: () => ({ currency: "USD", timezone: "UTC" }),
}));

vi.mock("@/features/offer-studio/hooks/use-archetype-display", async () => {
  const { Package } = await import("lucide-react");
  return {
    useArchetypeDisplay: (archetype?: string) => {
      if (!archetype) return undefined;
      return {
        archetype,
        label: "Producto",
        subtitle: "",
        icon: Package,
        examples: [],
      };
    },
  };
});

describe("LeadMagnetStreamCard", () => {
  it("renders the offer name", () => {
    render(<LeadMagnetStreamCard offer={MOCK_OFFER_NORMALIZED} />);
    expect(screen.getByText("Guía: Liberar la Mente")).toBeInTheDocument();
  });

  it("hides Archivar menu item when onArchive prop is not provided", async () => {
    const user = userEvent.setup();
    render(<LeadMagnetStreamCard offer={MOCK_OFFER_NORMALIZED} />);

    // Open the dropdown trigger (the only button when dialog is closed)
    const triggers = screen.getAllByRole("button");
    await user.click(triggers[0]);

    expect(screen.queryByRole("menuitem", { name: "Archivar" })).toBeNull();
  });

  it("shows Archivar menu item when onArchive prop is provided", async () => {
    const user = userEvent.setup();
    const onArchive = vi.fn();
    render(<LeadMagnetStreamCard offer={MOCK_OFFER_NORMALIZED} onArchive={onArchive} />);

    await user.click(screen.getAllByRole("button")[0]);
    expect(screen.getByRole("menuitem", { name: "Archivar" })).toBeInTheDocument();
  });

  it("opens confirmation dialog and only calls onArchive on confirm", async () => {
    const user = userEvent.setup();
    const onArchive = vi.fn();
    render(<LeadMagnetStreamCard offer={MOCK_OFFER_NORMALIZED} onArchive={onArchive} />);

    // Open dropdown and click Archivar menu item
    await user.click(screen.getAllByRole("button")[0]);
    await user.click(screen.getByRole("menuitem", { name: "Archivar" }));

    // Confirmation dialog appears — onArchive not called yet
    expect(screen.getByText(/¿Archivar este lead magnet\?/i)).toBeInTheDocument();
    expect(onArchive).not.toHaveBeenCalled();

    // Confirm: click the destructive action button inside the alert dialog
    const dialog = screen.getByRole("alertdialog");
    const confirmBtn = await screen.findByRole("button", { name: "Archivar" });
    expect(dialog).toContainElement(confirmBtn);
    await user.click(confirmBtn);

    expect(onArchive).toHaveBeenCalledWith(MOCK_OFFER_NORMALIZED.id);
  });
});
