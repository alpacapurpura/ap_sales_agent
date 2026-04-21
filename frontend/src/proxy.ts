import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";

import { matchLegacyFormRuntimeRedirect } from "@/lib/edge/legacy-redirects";

import type { NextRequest } from "next/server";

const isPublicSiteRequest = (request: NextRequest) =>
  request.headers.get("X-Public-Site") === "true";

// Routes that never require auth (sign-in would loop otherwise)
const isPublicRoute = createRouteMatcher(["/sign-in(.*)", "/sign-up(.*)", "/api/webhooks(.*)"]);

// Dashboard routes — require Clerk auth
const isDashboardRoute = createRouteMatcher(["/(main)(.*)", "/[tenantId](.*)", "/onboarding(.*)"]);

export default clerkMiddleware(async (auth, request) => {
  // 1. Form-runtime Phase 2 legacy URL redirects — cheap 308 before any
  //    auth work so external bookmarks resolve to the canonical shape.
  const legacy = matchLegacyFormRuntimeRedirect(request.nextUrl.pathname);
  if (legacy) {
    const url = request.nextUrl.clone();
    url.pathname = legacy.pathname;
    if (legacy.extraParams) {
      for (const [k, v] of Object.entries(legacy.extraParams)) {
        url.searchParams.set(k, v);
      }
    }
    url.searchParams.set("field", legacy.field);
    return NextResponse.redirect(url, 308);
  }

  // 2. Public site traffic (forwarded by Cloudflare Worker).
  if (isPublicSiteRequest(request)) {
    const url = request.nextUrl.clone();
    if (!url.pathname.startsWith("/_public")) {
      url.pathname = `/_public${url.pathname}`;
    }
    const response = NextResponse.rewrite(url);
    const tenantId = request.headers.get("X-Tenant-ID") ?? "";
    const originalHost = request.headers.get("X-Original-Host") ?? "";
    response.headers.set("X-Tenant-ID", tenantId);
    response.headers.set("X-Original-Host", originalHost);
    return response;
  }

  // 3. Never protect sign-in/sign-up (would cause redirect loop).
  if (isPublicRoute(request)) {
    return NextResponse.next();
  }

  // 4. Dashboard routes — protect with Clerk.
  if (isDashboardRoute(request)) {
    await auth.protect();
  }

  return NextResponse.next();
});

export const config = {
  matcher: [
    // Skip Next.js internals and static files
    "/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)",
    // Always run for API routes
    "/(api|trpc)(.*)",
  ],
};
