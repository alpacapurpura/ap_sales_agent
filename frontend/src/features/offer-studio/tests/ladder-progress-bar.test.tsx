import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

import { LadderProgressBar } from "../components/dashboard/LadderProgressBar";
import { OfferValueLevel } from "../types";

vi.mock("@/features/offer-studio/hooks/use-value-level-catalog", () => ({
  useValueLevelCatalog: vi.fn(),
}));

vi.mock("@/features/offer-studio/lib/icon-name-resolver", () => ({
  resolveIconByName: () => () => <span data-testid="icon" />,
}));

import { useValueLevelCatalog } from "@/features/offer-studio/hooks/use-value-level-catalog";

const mockCatalog = useValueLevelCatalog as unknown as ReturnType<typeof vi.fn>;

const CATALOG_FIXTURE = {
  version: "test",
  value_levels: [
    {
      value_level: OfferValueLevel.LEAD_MAGNET,
      order: 0,
      label_es: "Gancho Gratuito",
      description_es: "",
      role_in_funnel_es: "",
      icon_name: "Lightbulb",
      examples_es: [],
      is_free: true,
      typical_price_min_usd: null,
      typical_price_max_usd: null,
    },
    {
      value_level: OfferValueLevel.ACTIVACION,
      order: 1,
      label_es: "Primera Compra",
      description_es: "",
      role_in_funnel_es: "",
      icon_name: "Rocket",
      examples_es: [],
      is_free: false,
      typical_price_min_usd: 7,
      typical_price_max_usd: 97,
    },
    {
      value_level: OfferValueLevel.TRANSFORMACION,
      order: 2,
      label_es: "Oferta Principal",
      description_es: "",
      role_in_funnel_es: "",
      icon_name: "TrendingUp",
      examples_es: [],
      is_free: false,
      typical_price_min_usd: 97,
      typical_price_max_usd: 1997,
    },
    {
      value_level: OfferValueLevel.MAXIMIZACION,
      order: 3,
      label_es: "Oferta Premium",
      description_es: "",
      role_in_funnel_es: "",
      icon_name: "Gem",
      examples_es: [],
      is_free: false,
      typical_price_min_usd: 2000,
      typical_price_max_usd: 20000,
    },
    {
      value_level: OfferValueLevel.CORPORATIVO,
      order: 4,
      label_es: "Venta Corporativa",
      description_es: "",
      role_in_funnel_es: "",
      icon_name: "Building2",
      examples_es: [],
      is_free: false,
      typical_price_min_usd: 5000,
      typical_price_max_usd: 50000,
    },
  ],
};

describe("LadderProgressBar", () => {
  beforeEach(() => {
    mockCatalog.mockReset();
    mockCatalog.mockReturnValue({ data: CATALOG_FIXTURE, isLoading: false });
  });

  it("renders all 5 level segments", () => {
    render(<LadderProgressBar filledGroups={new Set<OfferValueLevel>()} score="vacia" percentage={0} />);
    expect(screen.getByText("Ladder")).toBeInTheDocument();
    expect(screen.getByText("0/5")).toBeInTheDocument();
  });

  it("shows filled count matching filledGroups size", () => {
    const filled = new Set([OfferValueLevel.LEAD_MAGNET, OfferValueLevel.TRANSFORMACION]);
    render(<LadderProgressBar filledGroups={filled} score="creciendo" percentage={40} />);
    expect(screen.getByText("2/5")).toBeInTheDocument();
    expect(screen.getByText("40")).toBeInTheDocument();
  });

  it("renders with all groups filled", () => {
    const filled = new Set([
      OfferValueLevel.LEAD_MAGNET,
      OfferValueLevel.ACTIVACION,
      OfferValueLevel.TRANSFORMACION,
      OfferValueLevel.MAXIMIZACION,
      OfferValueLevel.CORPORATIVO,
    ]);
    render(<LadderProgressBar filledGroups={filled} score="avanzada" percentage={100} />);
    expect(screen.getByText("5/5")).toBeInTheDocument();
    expect(screen.getByText("100")).toBeInTheDocument();
  });

  it("renders empty shell while catalog is loading", () => {
    mockCatalog.mockReturnValue({ data: undefined, isLoading: true });
    render(<LadderProgressBar filledGroups={new Set<OfferValueLevel>()} score="vacia" percentage={0} />);
    expect(screen.getByText("0/0")).toBeInTheDocument();
  });
});
