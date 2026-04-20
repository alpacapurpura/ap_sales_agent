import { headers } from "next/headers";
import { redirect } from "next/navigation";

import { fetchTenantProfileServer } from "@/features/tenant-profile/api/tenant-profile-server";

interface TenantLayoutProps {
  children: React.ReactNode;
  params: Promise<{ tenantId: string }>;
}

/**
 * Server Component layout wrapping all tenant-scoped routes.
 *
 * Gating: if the tenant has no complete profile (business_types not declared),
 * redirect to the onboarding perfil-negocio page.
 *
 * Skips gating for onboarding routes themselves to avoid redirect loops.
 *
 * CONTRACT §6.4
 */
export default async function TenantLayout({ children, params }: TenantLayoutProps) {
  const { tenantId } = await params;
  const headersList = await headers();
  const pathname = headersList.get("x-pathname") ?? headersList.get("x-invoke-path") ?? "";

  // Never gate the onboarding route itself — would create an infinite redirect loop.
  const isOnboardingRoute = pathname.includes("/onboarding/");

  if (!isOnboardingRoute) {
    const profile = await fetchTenantProfileServer(tenantId);

    // If profile is null (unauthenticated or error), let the auth middleware handle it.
    // Only redirect when we have a definitive incomplete profile.
    if (profile !== null && !profile.is_complete) {
      const returnTo = encodeURIComponent(pathname || `/${tenantId}`);
      redirect(`/${tenantId}/onboarding/perfil-negocio?returnTo=${returnTo}`);
    }
  }

  return <>{children}</>;
}
