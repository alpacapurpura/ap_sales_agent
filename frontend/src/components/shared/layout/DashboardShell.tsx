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
 * Phase 1: Passthrough skeleton — no behavior change vs DashboardLayoutClient.
 * Behavioral activation in T-3 (min-width floor) and T-4 (mutex policy).
 */
export function DashboardShell({ tenantId, children }: DashboardShellProps) {
  return <DashboardShellClient tenantId={tenantId}>{children}</DashboardShellClient>;
}
