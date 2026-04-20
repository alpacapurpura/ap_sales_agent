import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

import { SectionPage } from "../SectionPage";

import type { SectionSchema } from "@/lib/form-runtime/schema";

// Mocked under happy-dom — no real Next.js router
vi.mock("next/navigation", () => ({
  useParams: vi.fn(),
}));

const { useParams } = await import("next/navigation");

const IDENTITY_SCHEMA: SectionSchema = {
  key: "brand.identity",
  title: "Identidad",
  fields: [
    { id: "brand_name", label: "Nombre", type: "text", path: "brand_name" },
    { id: "tagline", label: "Tagline", type: "text", path: "tagline" },
  ],
};

function mockParams(params: { tenantId?: string; fieldId?: string | string[] }) {
  vi.mocked(useParams).mockReturnValue(params as never);
}

describe("SectionPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("delegates activeFieldId to URL params", () => {
    mockParams({ tenantId: "t-1", fieldId: "tagline" });
    render(
      <SectionPage
        sectionSlug="identity"
        schema={IDENTITY_SCHEMA}
        values={{ brand_name: "Visionarias", tagline: "Creadoras que viven de lo que aman" }}
        onSave={vi.fn().mockResolvedValue(undefined)}
      />,
    );
    expect(screen.getByDisplayValue("Creadoras que viven de lo que aman")).toBeTruthy();
  });

  it("builds section-level hrefs when no fieldId is active", () => {
    mockParams({ tenantId: "t-1" });
    render(
      <SectionPage
        sectionSlug="identity"
        schema={IDENTITY_SCHEMA}
        values={{ brand_name: "Visionarias", tagline: "" }}
        onSave={vi.fn().mockResolvedValue(undefined)}
      />,
    );
    const taglineRow = screen.getByRole("option", { name: /Tagline/ });
    expect(taglineRow.getAttribute("href")).toBe("/t-1/brand-studio/identity/tagline");
  });

  it("renders loading when values are missing", () => {
    mockParams({ tenantId: "t-1" });
    render(
      <SectionPage
        sectionSlug="identity"
        schema={IDENTITY_SCHEMA}
        values={undefined}
        onSave={vi.fn()}
        isLoading
      />,
    );
    expect(screen.getByText(/Cargando/i)).toBeTruthy();
  });
});
