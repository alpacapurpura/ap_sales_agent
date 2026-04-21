import { NextRequest } from "next/server";
import { describe, expect, it } from "vitest";

import { middleware } from "../middleware";

function requestFor(pathname: string, search = ""): NextRequest {
  return new NextRequest(`http://localhost${pathname}${search}`);
}

function redirectTarget(pathname: string, search = ""): string {
  const res = middleware(requestFor(pathname, search));
  expect(res.status).toBe(308);
  const loc = res.headers.get("location");
  expect(loc).toBeTruthy();
  return loc ?? "";
}

describe("middleware · legacy field redirects", () => {
  it("offer editor field segment → ?field=", () => {
    expect(redirectTarget("/t-1/offer-studio/offer/o-1/editor/identity/frase_titular")).toContain(
      "/t-1/offer-studio/offer/o-1/editor/identity?field=frase_titular",
    );
  });

  it("offer editor collection (testimonials) field segment → ?field=", () => {
    expect(
      redirectTarget("/t-1/offer-studio/offer/o-1/editor/testimonials/inst-9/author_name"),
    ).toContain("/t-1/offer-studio/offer/o-1/editor/testimonials/inst-9?field=author_name");
  });

  it("offer legacy edition field → new editor URL with edition + field query params", () => {
    const target = redirectTarget("/t-1/offer-studio/offer/o-1/edition/2/pricing/currency");
    expect(target).toContain("/t-1/offer-studio/offer/o-1/editor/pricing");
    expect(target).toContain("edition=2");
    expect(target).toContain("field=currency");
  });

  it("brand section field → ?field=", () => {
    expect(redirectTarget("/t-1/brand-studio/identity/brand_name")).toContain(
      "/t-1/brand-studio/identity?field=brand_name",
    );
  });

  it("brand collection instance field → ?field=", () => {
    expect(redirectTarget("/t-1/brand-studio/team/instance/m-1/role")).toContain(
      "/t-1/brand-studio/team/instance/m-1?field=role",
    );
  });

  it("brand persona field → ?field=", () => {
    expect(redirectTarget("/t-1/brand-studio/publico/persona/p-1/age_range")).toContain(
      "/t-1/brand-studio/publico/persona/p-1?field=age_range",
    );
  });

  it("already-modern URL falls through (no redirect)", () => {
    const res = middleware(requestFor("/t-1/brand-studio/identity", "?field=brand_name"));
    // NextResponse.next() has no location header + status 200 (default).
    expect(res.headers.get("location")).toBeNull();
  });

  it("collection root without field segment falls through", () => {
    const res = middleware(requestFor("/t-1/brand-studio/team"));
    expect(res.headers.get("location")).toBeNull();
  });
});
