"use client";

import { usePathname } from "next/navigation";
import { useEffect } from "react";

import { useCopilotStore } from "../store/copilot-store";

/**
 * Syncs the current pathname to the copilot store
 * so the backend knows where the user is.
 */
export function useRouteTracker() {
  const pathname = usePathname();
  const setCurrentRoute = useCopilotStore((s) => s.setCurrentRoute);

  useEffect(() => {
    if (pathname) {
      setCurrentRoute(pathname);
    }
  }, [pathname, setCurrentRoute]);
}
