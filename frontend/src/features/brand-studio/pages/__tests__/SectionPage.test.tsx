import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

import { SectionPage } from "../SectionPage";

import type { SectionSchema } from "@/lib/form-runtime/schema";

vi.mock("next/navigation", () => ({
  useParams: vi.fn(),
  usePathname: vi.fn(() => "/t-1/brand-studio/identity"),
  useSearchParams: vi.fn(() => new URLSearchParams()),
  useRouter: () => ({ push: vi.fn(), replace: vi.fn(), refresh: vi.fn() }),
}));

const { useParams, usePathname, useSearchParams } = await import("next/navigation");

const IDENTITY_SCHEMA: SectionSchema = {
  key: "brand.identity",
  title: "Identidad",
  fields: [
    { id: "brand_name", label: "Nombre", type: "text", path: "brand_name" },
    { id: "tagline", label: "Tagline", type: "text", path: "tagline" },
  ],
};

function mockRoute({
  tenantId,
  field,
  pathname = "/t-1/brand-studio/identity",
}: {
  tenantId?: string;
  field?: string;
  pathname?: string;
}) {
  vi.mocked(useParams).mockReturnValue({ tenantId } as never);
  vi.mocked(usePathname).mockReturnValue(pathname);
  vi.mocked(useSearchParams).mockReturnValue(
    (field ? new URLSearchParams({ field }) : new URLSearchParams()) as never,
  );
}

describe("SectionPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("delegates activeFieldId to the ?field= query parameter", () => {
    mockRoute({ tenantId: "t-1", field: "tagline" });
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

  it("builds section-level hrefs with the field id as a query param", () => {
    mockRoute({ tenantId: "t-1" });
    render(
      <SectionPage
        sectionSlug="identity"
        schema={IDENTITY_SCHEMA}
        values={{ brand_name: "Visionarias", tagline: "" }}
        onSave={vi.fn().mockResolvedValue(undefined)}
      />,
    );
    const taglineRow = screen.getByRole("option", { name: /Tagline/ });
    expect(taglineRow.getAttribute("href")).toBe("/t-1/brand-studio/identity?field=tagline");
  });

  it("renders loading when values are missing", () => {
    mockRoute({ tenantId: "t-1" });
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
