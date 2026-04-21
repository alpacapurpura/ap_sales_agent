import { describe, it, expect } from "vitest";

import { buildCrumbs } from "../OfferStudioBreadcrumb";

describe("OfferStudioBreadcrumb · buildCrumbs", () => {
  const tenant = "t-1";

  it("returns the root crumb alone when tenantId is missing", () => {
    expect(buildCrumbs("/t-1/offer-studio/offer/o-1/editor", "")).toEqual([
      { label: "Offer Studio", href: undefined },
    ]);
  });

  it("adds the offer crumb using the shortened id fallback when no name given", () => {
    const crumbs = buildCrumbs("/t-1/offer-studio/offer/o-1/editor", tenant);
    expect(crumbs[0]).toEqual({ label: "Offer Studio", href: "/t-1/offer-studio" });
    expect(crumbs[1]).toEqual({ label: "Oferta o-1", href: "/t-1/offer-studio/offer/o-1" });
    expect(crumbs[2]).toEqual({ label: "Editor", href: "/t-1/offer-studio/offer/o-1/editor" });
  });

  it("prefers the explicit offerName when provided", () => {
    const crumbs = buildCrumbs("/t-1/offer-studio/offer/o-1/editor", tenant, "Mentoría 12 semanas");
    expect(crumbs[1].label).toBe("Mentoría 12 semanas");
  });

  it("appends the section label for editor sub-routes", () => {
    const crumbs = buildCrumbs("/t-1/offer-studio/offer/o-1/editor/promise", tenant);
    expect(crumbs.map((c) => c.label)).toEqual(["Offer Studio", "Oferta o-1", "Editor", "Promesa"]);
  });

  it("appends the field id as the trailing crumb on field detail routes", () => {
    const crumbs = buildCrumbs(
      "/t-1/offer-studio/offer/o-1/editor/promise/central_promise",
      tenant,
    );
    expect(crumbs.at(-1)).toEqual({ label: "central_promise" });
  });

  it("supports the legacy /edition/{code}/{section} URL shape", () => {
    const crumbs = buildCrumbs("/t-1/offer-studio/offer/o-1/edition/default/pricing", tenant);
    expect(crumbs.map((c) => c.label)).toEqual(["Offer Studio", "Oferta o-1", "Editor", "Pricing"]);
  });

  it("labels the editions tab and adds edition id crumb on detail routes", () => {
    const crumbs = buildCrumbs("/t-1/offer-studio/offer/o-1/editions/ed-123", tenant);
    expect(crumbs.map((c) => c.label)).toEqual([
      "Offer Studio",
      "Oferta o-1",
      "Editions",
      "Edición ed-123",
    ]);
  });

  it("labels known sibling tabs (Assets / Knowledge / Campaigns / Ventas)", () => {
    const assets = buildCrumbs("/t-1/offer-studio/offer/o-1/assets", tenant);
    expect(assets.at(-1)?.label).toBe("Assets");

    const ventas = buildCrumbs("/t-1/offer-studio/offer/o-1/ventas", tenant);
    expect(ventas.at(-1)?.label).toBe("Ventas");
  });

  it("falls back to the raw segment for unknown tabs", () => {
    const crumbs = buildCrumbs("/t-1/offer-studio/offer/o-1/unknown-tab", tenant);
    expect(crumbs.at(-1)?.label).toBe("unknown-tab");
  });
});
