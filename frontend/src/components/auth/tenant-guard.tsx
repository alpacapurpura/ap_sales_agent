import { currentUser } from "@clerk/nextjs/server";
import ForbiddenPage from "@/app/(main)/forbidden/page";
import { ReactNode } from "react";
import { headers } from "next/headers";

export async function TenantGuard({ children }: { children: ReactNode }) {
  let user;
  try {
    user = await currentUser();
  } catch (err) {
    console.error("TenantGuard: currentUser() failed", err);
    // Fallback: If auth fails here, we proceed as unauthenticated (user = undefined).
    // Middleware should have protected the route if configured correctly.
  }
  const headersList = await headers();
  // x-url is often not available directly in Server Components unless middleware passes it,
  // but we can infer context or just check if the user is in a state that requires redirection.
  // Actually, we can check the path via headers if middleware sets it, or just use a client component wrapper if needed.
  // However, simpler: If user has no tenant, and is NOT on onboarding, redirect/show forbidden.

  // Note: Middleware ensures user is logged in for protected routes,
  // but we double check here to prevent rendering the app without context.
  const isAuth = !!user;
  const hasTenant = user?.publicMetadata?.tenant_id;

  // Get current path from headers (requires middleware to set x-url or similar,
  // but standard Next.js SC doesn't give pathname easily).
  // Strategy: We can't easily know the path here without middleware help.
  // BUT, we can just allow rendering if the user is authenticated.
  // The layout wraps everything.
  // If we return <ForbiddenPage /> it blocks EVERYTHING.

  // Workaround: We will let the page itself handle the redirect if it needs tenant context,
  // OR we assume that if we are here, we are in (main).

  // BETTER APPROACH:
  // If the user has no tenant, we should ONLY allow them to see the Onboarding page.
  // Since we can't check the URL easily in RSC layout without hacks:
  // We will assume that if we are in this Guard, we are enforcing tenant.
  // BUT we need to allow /onboarding.

  // Let's modify the logic:
  // If no tenant -> render children ONLY IF the child is the Onboarding page? No, we don't know what the child is.

  // Valid Fix: Check if the user is accessing a tenant-specific route?
  // Since we are in the root layout, we wrap everything.

  // Let's check if the request header 'x-invoke-path' or similar exists, or rely on the fact
  // that we will move Onboarding OUT of this layout?
  // No, Onboarding is in (main).

  // Alternative: Modify Middleware to pass the pathname in headers.
  const pathname = headersList.get("x-current-path") || "";

  // If we are on onboarding, allow it.
  if (pathname.includes("/onboarding")) {
    return <>{children}</>;
  }

  const showForbidden = isAuth && !hasTenant;

  if (showForbidden) {
    // Instead of Forbidden, we could redirect to onboarding?
    // But we can't redirect in Layout easily without causing loops if not careful.
    // Let's just return the ForbiddenPage which now should guide to onboarding?
    // Or better: Render the Onboarding Page content directly here?
    // No, that's messy.

    // Simplest fix for now:
    // If showForbidden is true, we render a special "No Tenant" state,
    // which IS effectively the Onboarding experience, or a link to it.

    // But wait, if I redirect to /onboarding in middleware/page, this guard still runs.
    // So we MUST know if we are on /onboarding.

    // Let's rely on middleware adding the header.
    // I will add a task to update middleware to pass x-current-path.
    return <ForbiddenPage />;
  }

  return <>{children}</>;
}
