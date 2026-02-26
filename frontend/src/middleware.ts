import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";

const isPublicRoute = createRouteMatcher([
  '/sign-in(.*)',
  '/sign-up(.*)',
  '/api/webhooks(.*)',
  '/visit(.*)',
  '/p(.*)',
  '/onboarding(.*)'
]);

export default clerkMiddleware(async (auth, req) => {
  if (!isPublicRoute(req)) await auth.protect();
  
  // Inject current path into headers for Layout to read
  const requestHeaders = new Headers(req.headers);
  requestHeaders.set('x-current-path', req.nextUrl.pathname);
  
  return NextResponse.next({
      request: {
          headers: requestHeaders,
      },
  });
});

export const config = {
  matcher: [
    // Skip Next.js internals and all static files, unless found in search params
    '/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)|_global-error|_not-found).*)',
    // Always run for API routes
    '/(api|trpc)(.*)',
  ],
};
