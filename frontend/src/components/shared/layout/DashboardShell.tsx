import { DashboardShellClient } from "./DashboardShellClient";

interface DashboardShellProps {
  tenantId: string;
  children: React.ReactNode;
}

/**
 * Server Component wrapper for the authenticated dashboard shell.
 *
 * Passes `tenantId` and `children` down to the Client Component
 * (`DashboardShellClient`) which owns all interactive shell state
 * (sidebar, copilot, mutex).
 *
 * AD1: Hybrid Server+Client split per `tessl__nextjs-app-router-modularization`.
 *
 * Active behavior: T-3 min-width floor + T-4 mutex policy + T-5 CopilotFAB
 * + T-6 z-index tokens. Owns full shell chrome computation.
 */
export function DashboardShell({ tenantId, children }: DashboardShellProps) {
  return <DashboardShellClient tenantId={tenantId}>{children}</DashboardShellClient>;
}
