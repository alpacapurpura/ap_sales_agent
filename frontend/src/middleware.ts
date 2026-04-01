import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const isPublicSiteRequest = (request: NextRequest) =>
  request.headers.get("X-Public-Site") === "true";

// Dashboard routes — require Clerk auth
const isDashboardRoute = createRouteMatcher([
  "/(main)(.*)",
  "/[tenantId](.*)",
  "/onboarding(.*)",
]);

export default clerkMiddleware(async (auth, request) => {
  // Public site traffic (forwarded by Cloudflare Worker)
  // These requests carry X-Public-Site: true and need no auth
  if (isPublicSiteRequest(request)) {
    const response = NextResponse.next();
    const tenantId = request.headers.get("X-Tenant-ID") ?? "";
    const originalHost = request.headers.get("X-Original-Host") ?? "";
    response.headers.set("X-Tenant-ID", tenantId);
    response.headers.set("X-Original-Host", originalHost);
    return response;
  }

  // Dashboard routes — protect with Clerk
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
