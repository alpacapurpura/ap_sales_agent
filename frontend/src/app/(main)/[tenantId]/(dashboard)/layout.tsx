import { redirect } from "next/navigation";

import { fetchTenantProfileServer } from "@/features/tenant-profile/api/tenant-profile-server";

import { DashboardLayoutClient } from "./DashboardLayoutClient";

interface DashboardLayoutProps {
  children: React.ReactNode;
  params: Promise<{ tenantId: string }>;
}

/**
 * Server wrapper for all authenticated dashboard routes.
 *
 * Gating: if the tenant profile is not complete, redirect to onboarding.
 * The onboarding route sits outside the ``(dashboard)`` group and is therefore
 * not affected by this layout — no redirect loop possible by construction.
 *
 * CONTRACT §6.4
 */
export default async function DashboardLayout({ children, params }: DashboardLayoutProps) {
  const { tenantId } = await params;
  const profile = await fetchTenantProfileServer(tenantId);

  // Fail open: when we can't verify (network blip, auth mid-flight), let the
  // downstream auth middleware decide. A false positive redirect loop is worse
  // than briefly showing the shell.
  if (profile !== null && !profile.is_complete) {
    redirect(`/${tenantId}/onboarding/perfil-negocio?returnTo=/${tenantId}`);
  }

  return <DashboardLayoutClient>{children}</DashboardLayoutClient>;
}
