import { useCallback, useEffect, useState } from "react";

const STORAGE_KEY = "nicolify.offer-studio.rail-collapsed";

/**
 * Persisted collapsed state for the Editions Rail.
 *
 * Uses `localStorage` so the preference follows the user across browser
 * sessions. Defaults to expanded. Handles the SSR case — during
 * hydration we return the default so the server and client markup
 * match, then rehydrate with the stored value after mount.
 */
// Lazy initializer reads localStorage on the first client render so we
// avoid triggering a setState-in-effect warning while still keeping SSR
// output deterministic (no window access during initialisation on the
// server; the hook only runs inside client components).
function readPersistedValue(): boolean {
  if (typeof window === "undefined") return false;
  try {
    return window.localStorage.getItem(STORAGE_KEY) === "true";
  } catch {
    return false;
  }
}

/**
 *
 */
export function useRailCollapsed(): [boolean, () => void] {
  const [collapsed, setCollapsed] = useState<boolean>(readPersistedValue);

  // Track changes in other tabs / windows.
  useEffect(() => {
    const onStorage = (event: StorageEvent) => {
      if (event.key === STORAGE_KEY) setCollapsed(event.newValue === "true");
    };
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  const toggle = useCallback(() => {
    setCollapsed((current) => {
      const next = !current;
      try {
        window.localStorage.setItem(STORAGE_KEY, String(next));
      } catch {
        // ignore write errors — state still updates in memory
      }
      return next;
    });
  }, []);

  return [collapsed, toggle];
}
