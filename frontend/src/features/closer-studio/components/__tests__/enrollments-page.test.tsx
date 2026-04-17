import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";

// ── Mocks ────────────────────────────────────────────────────────────────────

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({ getToken: () => Promise.resolve("test-token") }),
}));

const mockListFn = vi.fn();
vi.mock("../../api/enrollments-api", () => ({
  enrollmentsApi: {
    list: (...args: unknown[]) => mockListFn(...args),
  },
}));

// ── Imports ──────────────────────────────────────────────────────────────────

import { EnrollmentStatus } from "../../types/enrollment";
import { EnrollmentsPage } from "../EnrollmentsPage";

import type { Enrollment } from "../../types/enrollment";

function baseEnrollment(overrides: Partial<Enrollment> = {}): Enrollment {
  return {
    id: "e-1",
    tenant_id: "t-1",
    offer_id: "11111111-1111-1111-1111-111111111111",
    edition_id: "22222222-2222-2222-2222-222222222222",
    contact_id: "33333333-3333-3333-3333-333333333333",
    conversation_id: null,
    status: EnrollmentStatus.PAID,
    pricing_tier_label: "Early bird",
    pricing_amount: 690,
    currency: "PEN",
    payment_provider: null,
    payment_transaction_id: null,
    payment_link_url: null,
    paid_at: "2026-05-01T10:00:00Z",
    source_channel: "ig_dm",
    notes: null,
    extra: {},
    created_at: "2026-04-20T09:00:00Z",
    updated_at: null,
    ...overrides,
  };
}

function renderWithClient(ui: React.ReactElement) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe("EnrollmentsPage", () => {
  beforeEach(() => {
    mockListFn.mockReset();
  });

  it("renders empty state when no enrollments", async () => {
    mockListFn.mockResolvedValue({ items: [], total: 0 });
    renderWithClient(<EnrollmentsPage />);
    expect(await screen.findByText(/No hay inscripciones todavía/i)).toBeInTheDocument();
  });

  it("renders KPI strip with counts", async () => {
    mockListFn.mockResolvedValue({
      items: [
        baseEnrollment({ id: "e-1", status: EnrollmentStatus.PAID }),
        baseEnrollment({ id: "e-2", status: EnrollmentStatus.PAYMENT_PENDING }),
        baseEnrollment({
          id: "e-3",
          status: EnrollmentStatus.WAITLIST,
          edition_id: null,
        }),
      ],
      total: 3,
    });
    renderWithClient(<EnrollmentsPage />);
    // "Pagadas" / "Pendientes" / "Waitlist" also appear as filter pills, so
    // instead match the KPI row ("Total" is unique) + its value.
    expect(await screen.findByText("Total")).toBeInTheDocument();
    // Filter pills + KPI labels → at least 2 matches each for paid/pending/waitlist.
    expect(screen.getAllByText(/Pagadas/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Pendientes/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Waitlist/i).length).toBeGreaterThan(0);
  });

  it("groups waitlist entries into a separate section", async () => {
    mockListFn.mockResolvedValue({
      items: [
        baseEnrollment({
          id: "e-w1",
          status: EnrollmentStatus.WAITLIST,
          edition_id: null,
        }),
      ],
      total: 1,
    });
    renderWithClient(<EnrollmentsPage />);
    expect(await screen.findByText(/En lista de espera/i)).toBeInTheDocument();
  });
});
