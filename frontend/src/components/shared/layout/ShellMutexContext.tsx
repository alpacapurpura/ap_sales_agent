"use client";

import { createContext, useContext } from "react";

import type { UseShellMutexReturn } from "@/hooks/use-shell-mutex";

/**
 * Context that distributes the shell mutex state + actions throughout the
 * component tree without prop-drilling through AppSidebar, CopilotSidebar, etc.
 *
 * Provided by `DashboardShellClient` (inside `SidebarProvider`).
 * Consumed by `AppSidebar` (for Sheet open/close wiring).
 *
 * T-4 AD8: AppSidebar Sheet trigger rewired from local `useState(false)` to
 * `shellMutex.activePanel === 'app-sidebar'` via this context.
 */

const ShellMutexContext = createContext<UseShellMutexReturn | undefined>(undefined);

export const ShellMutexProvider = ShellMutexContext.Provider;

/**
 * Consume shell mutex state/actions from any component inside DashboardShellClient.
 *
 * Returns `undefined` gracefully when called outside the shell (e.g., Storybook,
 * isolated test renders). Components that strictly require mutex should check for
 * undefined and fall back gracefully.
 */
export function useShellMutexContext(): UseShellMutexReturn | undefined {
  return useContext(ShellMutexContext);
}
