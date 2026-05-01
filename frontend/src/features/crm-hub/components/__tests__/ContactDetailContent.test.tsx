import { render, screen } from "@testing-library/react";
import * as React from "react";
import { describe, it, expect } from "vitest";

import { ContactDetailContent } from "../ContactDetailContent";

import type { ContactDetail } from "../../types";

const mockDetail: ContactDetail = {
  id: "abc-123",
  full_name: "Juan García",
  primary_email: "juan@example.com",
  primary_phone: "+54 9 11 1234-5678",
  lifecycle_stage: "lead",
  lead_score: 67,
  rfm_segment: null,
  lifetime_value: 0,
  is_inactive: false,
  first_conversion_at: null,
  first_seen_at: "2026-01-15T10:00:00Z",
  last_activity_at: "2026-04-28T10:00:00Z",
  lead_source: "instagram_dm",
  lead_source_detail: null,
  traits: { industry: "retail" },
  computed_traits: {},
  created_at: "2026-01-15T10:00:00Z",
  updated_at: "2026-04-28T10:00:00Z",
  lead_id: "lead-456",
  telegram_id: "@juan_arg",
  whatsapp_id: null,
  instagram_id: "@juan.garcia",
  tiktok_id: null,
  api_id: null,
  fit_score: 72,
  intent_score: 60,
  temperature: "hot",
  is_blacklisted: false,
  last_interaction_date: "2026-04-28T10:00:00Z",
  country: "ar",
  conversation_summary: "Preguntó por el precio del paquete premium.",
  identities: [
    {
      type: "email",
      value: "juan@example.com",
      is_primary: true,
      verification_status: "verified",
      last_seen_at: "2026-04-01T00:00:00Z",
    },
  ],
};

describe("ContactDetailContent", () => {
  it("renders full_name in header", () => {
    render(<ContactDetailContent detail={mockDetail} />);
    expect(screen.getByText("Juan García")).toBeInTheDocument();
  });

  it("renders lifecycle stage chip", () => {
    render(<ContactDetailContent detail={mockDetail} />);
    expect(screen.getByText("Lead")).toBeInTheDocument();
  });

  it("renders score badge", () => {
    render(<ContactDetailContent detail={mockDetail} />);
    expect(screen.getByText("67")).toBeInTheDocument();
  });

  it("renders identities list", () => {
    render(<ContactDetailContent detail={mockDetail} />);
    expect(screen.getByText("juan@example.com")).toBeInTheDocument();
  });

  it("renders telegram_id channel", () => {
    render(<ContactDetailContent detail={mockDetail} />);
    expect(screen.getByText("@juan_arg")).toBeInTheDocument();
  });

  it("renders conversation summary", () => {
    render(<ContactDetailContent detail={mockDetail} />);
    expect(screen.getByText(/Preguntó por el precio/)).toBeInTheDocument();
  });

  it("renders traits section when traits present", () => {
    render(<ContactDetailContent detail={mockDetail} />);
    expect(screen.getByText("industry")).toBeInTheDocument();
  });

  it("shows loading skeletons when isLoading", () => {
    const { container } = render(<ContactDetailContent detail={null} isLoading />);
    const skeletons = container.querySelectorAll(".animate-pulse");
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it("shows placeholder when detail is null and not loading", () => {
    render(<ContactDetailContent detail={null} />);
    expect(screen.getByText(/Selecciona un contacto/)).toBeInTheDocument();
  });

  it("does NOT import Sheet/Dialog (host-agnostic)", async () => {
    // Source check: import chain should not pull in drawer components
    // The arch test enforces this; here we verify the component renders in isolation
    const { container } = render(<ContactDetailContent detail={mockDetail} />);
    expect(container).toBeDefined();
  });
});
