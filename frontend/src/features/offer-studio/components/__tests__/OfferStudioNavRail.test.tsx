import { describe, it, expect } from "vitest";

import { extractActiveSectionSlug } from "../OfferStudioNavRail";

describe("OfferStudioNavRail · extractActiveSectionSlug", () => {
  const offerId = "o-1";

  it("returns null when the path does not contain the offer id", () => {
    expect(extractActiveSectionSlug("/t-1/offer-studio", offerId)).toBeNull();
    expect(
      extractActiveSectionSlug("/t-1/offer-studio/offer/different-id/editor", offerId),
    ).toBeNull();
  });

  it("returns null when the path ends at /offer/{id}", () => {
    expect(extractActiveSectionSlug("/t-1/offer-studio/offer/o-1", offerId)).toBeNull();
  });

  it("extracts the section slug from the target URL /offer/{id}/editor/{section}", () => {
    expect(extractActiveSectionSlug("/t-1/offer-studio/offer/o-1/editor/promise", offerId)).toBe(
      "promise",
    );
  });

  it("extracts the section slug from the target URL /offer/{id}/editor/{section}/{fieldId}", () => {
    expect(
      extractActiveSectionSlug("/t-1/offer-studio/offer/o-1/editor/pricing/currency", offerId),
    ).toBe("pricing");
  });

  it("extracts the section slug from the legacy URL /offer/{id}/edition/{code}/{section}", () => {
    expect(
      extractActiveSectionSlug("/t-1/offer-studio/offer/o-1/edition/default/promise", offerId),
    ).toBe("promise");
  });

  it("extracts the section slug from the legacy URL with a field id", () => {
    expect(
      extractActiveSectionSlug(
        "/t-1/offer-studio/offer/o-1/edition/default/pricing/currency",
        offerId,
      ),
    ).toBe("pricing");
  });

  it("returns null for editor root (no section selected yet)", () => {
    expect(extractActiveSectionSlug("/t-1/offer-studio/offer/o-1/editor", offerId)).toBeNull();
  });

  it("returns null for sibling tabs that are not editor/edition", () => {
    expect(extractActiveSectionSlug("/t-1/offer-studio/offer/o-1/assets", offerId)).toBeNull();
    expect(extractActiveSectionSlug("/t-1/offer-studio/offer/o-1/editions", offerId)).toBeNull();
  });
});
