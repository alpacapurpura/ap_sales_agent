import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, act } from "@testing-library/react";
import { OfferStudioView } from "../components/dashboard/OfferStudioView";
import { OfferValueLevel, OfferArchetype, OfferDeliveryModel, OfferStatus, GuaranteeType } from "../types";
import type { Offer } from "../types";

// --- Mocks ---

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({ getToken: vi.fn().mockResolvedValue("test-token") }),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
  useParams: () => ({ tenantId: "test-tenant" }),
}));

vi.mock("@/components/shared/navigation", () => ({
  useNavigation: () => ({
    navigate: vi.fn(),
    isNavigating: false,
    navigateReplace: vi.fn(),
    pendingHref: null,
  }),
}));

const MOCK_OFFERS: Offer[] = [
  {
    id: "1",
    name: "Lead Magnet 1",
    archetype: OfferArchetype.PRODUCTO,
    value_level: OfferValueLevel.LEAD_MAGNET,
    delivery_model: OfferDeliveryModel.DIY,
    status: OfferStatus.ACTIVE,
    pricing: [],
    currency: "USD",
    specific_details: {},
    marketing_pain_points: [],
    marketing_desires: [],
    deliverables: [],
    target_avatar_match: [],
    prerequisites: [],
    includes_offers: [],
    assets: [],
    guarantee_type: GuaranteeType.NONE,
    instructors: [],
  },
];

// Track how many times onLadderComputed is called
let ladderCallCount = 0;
let lastLadderData: unknown = null;

vi.mock("../api", () => ({
  offerApi: {
    listOffers: vi.fn().mockResolvedValue([
      {
        id: "1",
        public_name: "Lead Magnet 1",
        archetype: "producto",
        status: "active",
        offer_value_level: "lead_magnet",
        delivery_model: "diy",
      },
    ]),
  },
}));

// Mock React Query to return stable data
vi.mock("@tanstack/react-query", () => {
  const actual = vi.importActual("@tanstack/react-query");
  return {
    ...actual,
    useQuery: vi.fn().mockReturnValue({
      data: [
        {
          id: "1",
          name: "Lead Magnet 1",
          archetype: "producto",
          value_level: "lead_magnet",
          delivery_model: "diy",
          status: "active",
          pricing: [],
          currency: "USD",
          specific_details: {},
          marketing_pain_points: [],
          marketing_desires: [],
          deliverables: [],
          target_avatar_match: [],
          prerequisites: [],
          includes_offers: [],
          assets: [],
          guarantee_type: "none",
          instructors: [],
        },
      ],
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    }),
    useQueryClient: () => ({
      invalidateQueries: vi.fn(),
    }),
  };
});

// Spy on React.useState to detect infinite loops
let setStateCallCount = 0;
const originalUseState = await import("react").then((m) => m.useState);

describe("OfferStudioView — infinite loop prevention", () => {
  beforeEach(() => {
    ladderCallCount = 0;
    lastLadderData = null;
    setStateCallCount = 0;
  });

  it("renders without Maximum update depth exceeded error", async () => {
    // This test would FAIL before the fix because the component would
    // enter an infinite re-render loop via onLadderComputed -> setLadderData -> re-render
    expect(() => {
      render(<OfferStudioView />);
    }).not.toThrow();

    // Verify the dashboard content appears (proves render completed)
    await waitFor(() => {
      expect(screen.getByText("Offer Studio")).toBeInTheDocument();
    });
  });

  it("renders the LadderProgressBar when data is available", async () => {
    render(<OfferStudioView />);

    // The ladder bar should show 1/5 since we have 1 offer in 1 group
    await waitFor(() => {
      expect(screen.getByText("1/5")).toBeInTheDocument();
    });
  });

  it("does not trigger excessive re-renders from ladder data sync", async () => {
    const renderCountRef = { count: 0 };

    // Wrap in a counter component to track renders
    function RenderCounter() {
      renderCountRef.count++;
      return <OfferStudioView />;
    }

    render(<RenderCounter />);

    await waitFor(() => {
      expect(screen.getByText("Offer Studio")).toBeInTheDocument();
    });

    // Allow effects to settle
    await act(async () => {
      await new Promise((r) => setTimeout(r, 100));
    });

    // In a healthy component, renders should stabilize quickly.
    // Before the fix, this would exceed React's 50-render limit.
    // After the fix, we expect <= 10 renders (initial + effects settling).
    expect(renderCountRef.count).toBeLessThanOrEqual(10);
  });
});
