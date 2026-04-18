import { render, screen, fireEvent } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeEach } from "vitest";

import { BusinessTypeSelector } from "../BusinessTypeSelector";

vi.mock("@/features/brand-studio/hooks/use-expert-business-types-catalog", () => ({
  useExpertBusinessTypesCatalog: vi.fn(),
}));

vi.mock("@/features/offer-studio/lib/icon-name-resolver", () => ({
  resolveIconByName: () => () => <span data-testid="icon" />,
}));

import { useExpertBusinessTypesCatalog } from "@/features/brand-studio/hooks/use-expert-business-types-catalog";

const mockCatalog = useExpertBusinessTypesCatalog as unknown as ReturnType<typeof vi.fn>;

function renderWithClient(ui: React.ReactElement) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe("BusinessTypeSelector", () => {
  beforeEach(() => {
    mockCatalog.mockReset();
  });

  it("renders skeleton while loading", () => {
    mockCatalog.mockReturnValue({ data: undefined, isLoading: true });
    renderWithClient(<BusinessTypeSelector value={[]} onChange={vi.fn()} />);
    expect(document.querySelectorAll(".animate-pulse").length).toBeGreaterThan(0);
  });

  it("renders business type cards from catalog", () => {
    mockCatalog.mockReturnValue({
      data: {
        business_types: [
          {
            business_type: "course_creator",
            label_es: "Creador de cursos",
            description_es: "Vendés cursos en línea",
            icon_name: "book",
            examples_es: ["Ejemplo A"],
          },
        ],
      },
      isLoading: false,
    });
    renderWithClient(<BusinessTypeSelector value={[]} onChange={vi.fn()} />);
    expect(screen.getByText("Creador de cursos")).toBeInTheDocument();
  });

  it("calls onChange when a card is toggled", () => {
    const onChange = vi.fn();
    mockCatalog.mockReturnValue({
      data: {
        business_types: [
          {
            business_type: "coach",
            label_es: "Coach",
            description_es: "Coaching 1:1",
            icon_name: "user",
            examples_es: [],
          },
        ],
      },
      isLoading: false,
    });
    renderWithClient(<BusinessTypeSelector value={[]} onChange={onChange} />);
    fireEvent.click(screen.getByText("Coach"));
    expect(onChange).toHaveBeenCalledWith(["coach"]);
  });
});
