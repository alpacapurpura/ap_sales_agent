import { describe, expect, it } from "vitest";

import { matchLegacyFormRuntimeRedirect } from "./legacy-redirects";

describe("matchLegacyFormRuntimeRedirect", () => {
  describe("offer-studio editor field", () => {
    it("collapses section/fieldId into query param", () => {
      expect(
        matchLegacyFormRuntimeRedirect(
          "/tenant-1/offer-studio/offer/offer-9/editor/promise/headline",
        ),
      ).toEqual({
        pathname: "/tenant-1/offer-studio/offer/offer-9/editor/promise",
        field: "headline",
      });
    });

    it("tolerates trailing slash", () => {
      expect(
        matchLegacyFormRuntimeRedirect(
          "/tenant-1/offer-studio/offer/offer-9/editor/promise/headline/",
        )?.pathname,
      ).toBe("/tenant-1/offer-studio/offer/offer-9/editor/promise");
    });

    it("does not match 4-segment editor root", () => {
      expect(
        matchLegacyFormRuntimeRedirect("/tenant-1/offer-studio/offer/offer-9/editor/promise"),
      ).toBeNull();
    });
  });

  describe("offer-studio collection instance field", () => {
    it.each(["testimonials", "faq", "instructors"])(
      "collapses %s/{instance}/fieldId",
      (section) => {
        expect(
          matchLegacyFormRuntimeRedirect(
            `/tenant-1/offer-studio/offer/offer-9/editor/${section}/inst-42/quote`,
          ),
        ).toEqual({
          pathname: `/tenant-1/offer-studio/offer/offer-9/editor/${section}/inst-42`,
          field: "quote",
        });
      },
    );

    it("does not collapse non-collection section with 5 segments", () => {
      // promise is not a collection → fifth segment is not an instance
      expect(
        matchLegacyFormRuntimeRedirect(
          "/tenant-1/offer-studio/offer/offer-9/editor/promise/extra/slug",
        ),
      ).toBeNull();
    });
  });

  describe("offer-studio legacy edition field", () => {
    it("preserves edition code in extraParams", () => {
      expect(
        matchLegacyFormRuntimeRedirect(
          "/tenant-1/offer-studio/offer/offer-9/edition/v2/promise/headline",
        ),
      ).toEqual({
        pathname: "/tenant-1/offer-studio/offer/offer-9/editor/promise",
        field: "headline",
        extraParams: { edition: "v2" },
      });
    });
  });

  describe("brand-studio section field", () => {
    it("collapses section/fieldId", () => {
      expect(matchLegacyFormRuntimeRedirect("/tenant-1/brand-studio/esencia/mision")).toEqual({
        pathname: "/tenant-1/brand-studio/esencia",
        field: "mision",
      });
    });

    it.each(["team", "authority", "testimonials", "publico"])(
      "skips collection root %s",
      (section) => {
        expect(
          matchLegacyFormRuntimeRedirect(`/tenant-1/brand-studio/${section}/whatever`),
        ).toBeNull();
      },
    );
  });

  describe("brand-studio collection instance field", () => {
    it.each(["team", "authority", "testimonials"])("collapses %s/instance/id/field", (section) => {
      expect(
        matchLegacyFormRuntimeRedirect(`/tenant-1/brand-studio/${section}/instance/inst-7/role`),
      ).toEqual({
        pathname: `/tenant-1/brand-studio/${section}/instance/inst-7`,
        field: "role",
      });
    });

    it("does not match when section is not a collection root", () => {
      expect(
        matchLegacyFormRuntimeRedirect("/tenant-1/brand-studio/esencia/instance/x/field"),
      ).toBeNull();
    });
  });

  describe("brand-studio publico persona field", () => {
    it("collapses persona/id/field", () => {
      expect(
        matchLegacyFormRuntimeRedirect("/tenant-1/brand-studio/publico/persona/persona-3/avatar"),
      ).toEqual({
        pathname: "/tenant-1/brand-studio/publico/persona/persona-3",
        field: "avatar",
      });
    });
  });

  describe("non-legacy paths", () => {
    it.each([
      "/",
      "/tenant-1",
      "/tenant-1/offer-studio",
      "/tenant-1/offer-studio/offer/offer-9/editor/promise",
      "/tenant-1/brand-studio/esencia",
      "/sign-in",
      "/api/webhooks/clerk",
    ])("returns null for %s", (pathname) => {
      expect(matchLegacyFormRuntimeRedirect(pathname)).toBeNull();
    });
  });
});
