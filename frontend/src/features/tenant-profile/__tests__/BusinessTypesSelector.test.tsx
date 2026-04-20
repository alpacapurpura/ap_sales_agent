import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

import { BusinessTypesSelector } from "../components/BusinessTypesSelector";

// Mock hooks
vi.mock("../hooks/use-business-types-catalog", () => ({
  useBusinessTypesCatalog: vi.fn(),
}));

vi.mock("@/features/offer-studio/lib/icon-name-resolver", () => ({
  resolveIconByName: () => () => <span data-testid="icon" />,
}));

import { useBusinessTypesCatalog } from "../hooks/use-business-types-catalog";

const mockCatalog = useBusinessTypesCatalog as unknown as ReturnType<typeof vi.fn>;

const MOCK_CATALOG_DATA = {
  version: "v1",
  business_types: [
    {
      slug: "coach_mentor",
      label_es: "Coach / Mentor",
      description_es: "Sesiones de coaching 1:1",
      icon_name: "user",
      examples_es: ["Life coach", "Business coach"],
    },
    {
      slug: "academia_infoproductor",
      label_es: "Academia / Infoproductor",
      description_es: "Vendes cursos online",
      icon_name: "book",
      examples_es: ["Curso de finanzas"],
    },
    {
      slug: "consultor_profesional",
      label_es: "Consultor",
      description_es: "Consultoría especializada",
      icon_name: "briefcase",
      examples_es: ["Marketing consultant"],
    },
  ],
};

function renderWithClient(ui: React.ReactElement) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe("BusinessTypesSelector", () => {
  beforeEach(() => {
    mockCatalog.mockReset();
  });

  it("renders skeleton while loading", () => {
    mockCatalog.mockReturnValue({ data: undefined, isLoading: true });
    renderWithClient(<BusinessTypesSelector value={[]} onChange={vi.fn()} />);
    expect(document.querySelectorAll(".animate-pulse").length).toBeGreaterThan(0);
  });

  it("renders cards from catalog data", () => {
    mockCatalog.mockReturnValue({ data: MOCK_CATALOG_DATA, isLoading: false });
    renderWithClient(<BusinessTypesSelector value={[]} onChange={vi.fn()} />);
    expect(screen.getByText("Coach / Mentor")).toBeInTheDocument();
    expect(screen.getByText("Academia / Infoproductor")).toBeInTheDocument();
  });

  it("shows helper text with constraint range", () => {
    mockCatalog.mockReturnValue({ data: MOCK_CATALOG_DATA, isLoading: false });
    renderWithClient(<BusinessTypesSelector value={[]} onChange={vi.fn()} min={1} max={2} />);
    expect(screen.getByText(/Elige entre 1 y 2/i)).toBeInTheDocument();
  });

  it("calls onChange when a card is clicked", () => {
    mockCatalog.mockReturnValue({ data: MOCK_CATALOG_DATA, isLoading: false });
    const onChange = vi.fn();
    renderWithClient(<BusinessTypesSelector value={[]} onChange={onChange} />);
    fireEvent.click(screen.getByText("Coach / Mentor"));
    expect(onChange).toHaveBeenCalledWith(["coach_mentor"]);
  });

  it("deselects a selected card", () => {
    mockCatalog.mockReturnValue({ data: MOCK_CATALOG_DATA, isLoading: false });
    const onChange = vi.fn();
    renderWithClient(<BusinessTypesSelector value={["coach_mentor"]} onChange={onChange} />);
    fireEvent.click(screen.getByText("Coach / Mentor"));
    expect(onChange).toHaveBeenCalledWith([]);
  });

  it("disables unselected cards when max is reached", () => {
    mockCatalog.mockReturnValue({ data: MOCK_CATALOG_DATA, isLoading: false });
    const onChange = vi.fn();
    // Select 2 out of 3 — max=2 reached
    renderWithClient(
      <BusinessTypesSelector
        value={["coach_mentor", "academia_infoproductor"]}
        onChange={onChange}
        max={2}
      />,
    );
    // The Consultor card should not be clickable
    const consultorCard = screen.getByText("Consultor").closest("[role='button']");
    expect(consultorCard).toHaveAttribute("aria-disabled", "true");
  });

  it("does not add beyond max when clicking disabled cards", () => {
    mockCatalog.mockReturnValue({ data: MOCK_CATALOG_DATA, isLoading: false });
    const onChange = vi.fn();
    renderWithClient(
      <BusinessTypesSelector
        value={["coach_mentor", "academia_infoproductor"]}
        onChange={onChange}
        max={2}
      />,
    );
    // Clicking disabled card should not trigger onChange
    fireEvent.click(screen.getByText("Consultor"));
    expect(onChange).not.toHaveBeenCalled();
  });

  it("shows max-reached helper text", () => {
    mockCatalog.mockReturnValue({ data: MOCK_CATALOG_DATA, isLoading: false });
    renderWithClient(
      <BusinessTypesSelector
        value={["coach_mentor", "academia_infoproductor"]}
        onChange={vi.fn()}
        max={2}
      />,
    );
    expect(screen.getByText(/máximo/i)).toBeInTheDocument();
  });
});
